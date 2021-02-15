package main

import (
	"database/sql"
	"encoding/json"
	"fmt"
	"io/ioutil"
	"os"
	"sort"
	"strconv"
	"strings"

	"github.com/go-ego/gse"
	"github.com/jinzhu/gorm"
	_ "github.com/jinzhu/gorm/dialects/mysql"
)

var db *gorm.DB
var seg gse.Segmenter

type Auth struct {
	Host     string `json:"host"`
	Port     int    `json:"port"`
	User     string `json:"user"`
	Password string `json:"password"`
}

func Connect() {
	var auth Auth
	jstring, err := ioutil.ReadFile("auth.json")
	if err != nil {
		panic(err)
	}
	err = json.Unmarshal(jstring, &auth)
	if err != nil {
		panic(err)
	}
	dsn := auth.User + ":" + auth.Password + "@tcp(" + auth.Host + ":" + strconv.Itoa(auth.Port) + ")/datapack_collection?charset=UTF8MB4&parseTime=True&loc=Local"
	fmt.Println(dsn + " connecting..")
	db, err = gorm.Open("mysql", dsn)
	if err != nil {
		fmt.Println(err)
	}
}

type Language struct {
	Name string `json:"name"`
}

func GetLanguages() map[string]Language {
	var languages map[string]Language
	jString, err := ioutil.ReadFile("languages.json")
	if err != nil {
		fmt.Println("languages.json: ", err)
		os.Exit(1)
	}
	err = json.Unmarshal(jString, &languages)
	if err != nil {
		fmt.Println("languages.json -> map[Language] err: ", err)
		os.Exit(1)
	}
	fmt.Println("loaded languages.json")
	return languages
}

var invertedIndexName string

type InvertedIndex struct {
	Word  string
	ID    string
	Count int
}

func (InvertedIndex) TableName() string {
	return invertedIndexName
}
func buildIndex(table string, column string, length int) {
	fmt.Println("building b+ index for '" + column + "' in '" + table + "'")
	if length <= 0 {
		db.Exec("create index " + table + "_" + column + "_i on " + table + "(" + column + ");")
	} else {
		db.Exec("create index " + table + "_" + column + "_i on " + table + "(" + column + "(" + strconv.Itoa(length) + "));")
	}
}
func updateInvertedIndex(table string, column string, indexQueue string) {
	fmt.Println("building inverted index for '" + column + "' in '" + table + "'")
	invertedIndexName = table + "_" + column + "_ii"
	// Get rows
	var rows *sql.Rows
	var err error
	id, val, sum, rowIndex, total := "", "", "", 1, 0
	if indexQueue == "" { // Get All
		rows, err = db.Raw("select id, " + column + " from " + table + ";").Rows()
		_ = db.Raw("select count(id) from " + table + ";").Row().Scan(&sum)
	} else { // Get From Queue
		// Get ids and columns to insert
		rows, err = db.Raw("select id, " + column + " from (select id as i, operate as o from " + indexQueue + ") as q left join " + table + " as d on q.i = d.id where q.o = '+';").Rows()
		_ = db.Raw("select count(id) from (select id as i, operate as o from " + indexQueue + ") as q left join " + table + " as d on q.i = d.id where q.o = '+';").Row().Scan(&sum)
		// Remove those which needs to be removed from inverted index
		_ = db.Exec("delete from " + invertedIndexName + " where id in (select id from " + indexQueue + " where operate = '-');")
	}
	if err != nil {
		fmt.Println("building inverted index error (when getting 'id' and '"+column+"' from '"+table+"') : ", err)
	}
	// Create index
	// db.Exec("drop table if exists " + table + "_" + column + "_ii")
	db.Exec("create table if not exists " + table + "_" + column + "_ii (word VARCHAR(1024) NOT NULL, id VARCHAR(36) NOT NULL, count INT DEFAULT 0) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;")
	// Scan each row
	for rows.Next() {
		err = rows.Scan(&id, &val)
		if err != nil {
			fmt.Println("building inverted index error (when scanning 'id' and '"+column+"' from '"+table+"') : ", err)
		}
		db.Exec("delete from "+invertedIndexName+" where id = ?", id)
		words := analyzeDocument(&val) // Analyze words after nlp
		total += len(words)
		fmt.Println("Analyzing", strconv.Itoa(rowIndex)+"/"+sum, ", got", len(words), ", totally got", total)
		rowIndex++
		for k, v := range words { // Insert words into index
			db.Create(&InvertedIndex{Word: k, ID: id, Count: v})
			//db.Exec("insert into " + table + "_" + column + "_ii (word, id, count) values ('" + k + "', '" + id + "', " + strconv.Itoa(v) + ");")
		}
	}
	// Close rows
	err = rows.Close()
	if err != nil {
		fmt.Println("building inverted index error (when closing '"+table+"') : ", err)
	}
}
func analyzeDocument(doc *string) (words map[string]int) {
	hmm := seg.CutSearch(*doc, true)
	words = wordCounter(hmm)
	return
}
func wordCounter(w []string) map[string]int {
	sort.Strings(w)
	counter := make(map[string]int)
	for i := 0; i < len(w); i++ {
		if len(w[i]) == 0 || w[i] == " " || w[i] == "," || w[i] == "，" { // If empty, continue
			continue
		}
		_, ok := counter[w[i]]
		if !ok {
			counter[w[i]] = 0
		}
		counter[w[i]]++
	}
	return counter
}

func main() {
	//connect to database
	Connect()
	defer db.Close()            //close database
	_ = seg.LoadDict()          //load dict
	db.LogMode(false)           //disable log
	languages := GetLanguages() // list all languages

	//build b+ index (for all translated tags)
	for k, _ := range languages {
		k = strings.ReplaceAll(k, "-", "_")
		buildIndex("tags", "tag_"+k, 36)
	}

	//build inverted index
	datapacksInvertedColumns := make([]string, 0)
	datapacksInvertedColumns = append(datapacksInvertedColumns, "default_name")
	datapacksInvertedColumns = append(datapacksInvertedColumns, "default_intro")
	for k, _ := range languages {
		k = strings.ReplaceAll(k, "-", "_")
		datapacksInvertedColumns = append(datapacksInvertedColumns, "name_"+k)
		datapacksInvertedColumns = append(datapacksInvertedColumns, "intro_"+k)
	}
	for _, col := range datapacksInvertedColumns {
		queue := "ii_queue_" + col
		if len(os.Args) > 1 && os.Args[1] == "-a" {
			queue = ""
		}
		updateInvertedIndex("datapacks", col, queue)
		buildIndex(invertedIndexName, "word", 36)
		buildIndex(invertedIndexName, "id", 36)
		_ = db.Exec("delete from " + queue + ";") // Clear queue
	}
}
