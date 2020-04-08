package main

import (
	"encoding/json"
	"flag"
	"fmt"
	"github.com/jinzhu/gorm"
	_ "github.com/jinzhu/gorm/dialects/mysql"
	"io/ioutil"
	"os"
	"reflect"
	"strconv"
	"strings"
	"time"
)

type Auth struct {
	Host     string `json:"host"`
	Port     int    `json:"port"`
	User     string `json:"user"`
	Password string `json:"password"`
}

var db *gorm.DB

type IDRelated struct {
	Related     string
	RelatedList []string
}

func (i *IDRelated) Spilt() {
	l := strings.Split(i.Related, ";")
	for j := 0; j < len(l); j++ {
		if (j == 0 || l[j-1] != l[j]) && l[j] != "" {
			i.RelatedList = append(i.RelatedList, l[j])
		}
	}
}
func GetRelatedID(id string, table string) IDRelated {
	// Get Related ID
	var sql = db
	var related IDRelated
	sql.Table(table+"s_related").
		Where(table+"_id = ?", id).
		First(&related)
	related.Spilt()
	return related
}

func Connect() {
	var auth Auth
	jstring, err := ioutil.ReadFile("../util/auth.json")
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
func Combine() {
	if len(os.Args) < 5 {
		fmt.Println("Parameters error.")
		os.Exit(1)
	}
	table := "author"
	if os.Args[2] == "-d" {
		table = "datapack"
	} else if os.Args[2] != "-a" {
		fmt.Println("You must choose a table. '-a' or '-d'.")
		os.Exit(1)
	}
	id1, id2 := os.Args[3], os.Args[4]
	relate := GetRelatedID(id1, table) // Get from ID1
	if relate.Related == "" {
		id1, id2 = id2, id1               // ID1 always the exists, ID2 always the new
		relate = GetRelatedID(id1, table) // Switch
	}
	relate.RelatedList = append(relate.RelatedList, id1)

	_relate := GetRelatedID(id2, table) // Get from ID2
	if _relate.Related != "" {          // Had been Combined
		fmt.Println(id1 + " and " + id2 + " had been combined.")
		fmt.Println("In '" + table + "s_related' " + strconv.Itoa(len(relate.RelatedList)+1) + " are related:")
		for i, id := range relate.RelatedList {
			fmt.Print(id)
			if i == len(relate.RelatedList)-1 {
				fmt.Println(".")
			} else {
				fmt.Println(",")
			}
		}
		os.Exit(0) // ID2 also exists, exit.
	}

	for _, id := range relate.RelatedList { // Update previous all
		_r := GetRelatedID(id, table)
		_r.Spilt()
		db.Exec("update " + table + "s_related set related = '" + _r.Related + id2 + ";' where " + table + "_id = '" + id + "';")
	}
	if relate.Related == "" { // ID2 does not exists, create it.
		db.Exec("insert into " + table + "s_related (" + table + "_id, related) values ('" + id1 + "', '" + id2 + ";');")
	}
	db.Exec("insert into " + table + "s_related (" + table + "_id, related) values ('" + id2 + "', '" + id1 + ";" + relate.Related + "');")
	fmt.Println("Successfully combined. Now in '" + table + "s_related' " + strconv.Itoa(len(relate.RelatedList)+1) + " are related:")
	for _, id := range relate.RelatedList {
		fmt.Println(id + ",")
	}
	fmt.Println(id2 + ".")
}
func makeResultReceiver(length int) []interface{} {
	result := make([]interface{}, 0, length)
	for i := 0; i < length; i++ {
		var current interface{}
		current = struct{}{}
		result = append(result, &current)
	}
	return result
}
func Query() {
	if len(os.Args) < 4 {
		fmt.Println("Parameters error.")
		os.Exit(1)
	}
	var sql = db
	table := "author"
	if os.Args[2] == "-d" {
		table = "datapack"
	} else if os.Args[2] == "-t" {
		table = "tag"
	} else if os.Args[2] != "-a" {
		fmt.Println("You must choose a table. '-a' or '-d'.")
		os.Exit(1)
	}
	id := os.Args[3]
	if id == "" {
		fmt.Println("You must input id.")
		os.Exit(1)
	}
	showAll := false
	if len(os.Args) == 5 && os.Args[4] == "-v" {
		showAll = true
		fmt.Println("-- Show All : enabled ;")
	}

	result := make(map[string]interface{})
	rows, err := sql.Raw("select * from " + table + "s where id = '" + id + "'").Rows()
	if err != nil {
		panic(err)
	}
	columns, err := rows.Columns()
	if err != nil {
		panic(err)
	}
	length := len(columns)
	for rows.Next() {
		current := makeResultReceiver(length)
		if err := rows.Scan(current...); err != nil {
			panic(err)
		}
		for i := 0; i < length; i++ {
			key := columns[i]
			result[key] = *(current[i]).(*interface{})
		}
	}
	for k, v := range result {
		vType := reflect.TypeOf(v)
		switch vType.String() {
		case "int64":
			fmt.Println(k + " : \"" + strconv.FormatInt(v.(int64), 10) + "\" ;")
		case "string":
			vl := v.(string)
			if showAll || len(vl) <= 50 {
				fmt.Println(k + " : \"" + vl + "\" ;")
			} else if len(vl) > 50 {
				fmt.Println(k + " : \"" + vl[:50] + "...\" ;")
			}
		case "time.Time":
			fmt.Println(k + " : \"" + v.(time.Time).Format("2006-01-02 15:04:05") + "\" ;")
		case "[]uint8":
			vl := string(v.([]uint8))
			if showAll || len(vl) <= 50 {
				fmt.Println(k + " : \"" + vl + "\" ;")
			} else if len(vl) > 50 {
				fmt.Println(k + " : \"" + vl[:50] + "...\" ;")
			}
		default:
			fmt.Println("Do not support '" + vType.String() + "'")
		}
	}
}
func main() {
	//connect to database
	Connect()
	defer db.Close() //close database
	flag.Usage = func() {
		_, err := fmt.Fprintf(os.Stderr, `admin:
Usage:
admin combine [-a | -d] [id1] [id2]
admin query [-a | -d | -t] [id] 
admin update [-a | -d | -t] [-l=language] [...]
Options:
`)
		if err != nil {
			panic(err)
		}
		flag.PrintDefaults()
	}
	if os.Args[1] == "combine" {
		Combine()
	} else if os.Args[1] == "query" {
		Query()
	}
}
