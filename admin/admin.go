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
type Authorized struct {
	Datapacks []string `json:"datapacks"`
	Authors   []string `json:"authors"`
}
type AuthList struct {
	Authorized   Authorized `json:"auth"`
	UnAuthorized []string   `json:"unauth"` // Only Ids of Datapack
	Queue        Authorized `json:"queue"`  // To be updated
}

func GetAuthList() *AuthList {
	var authList AuthList
	jString, err := ioutil.ReadFile("../util/authlist.json")
	if err != nil {
		fmt.Println("authlist.json: ", err)
		os.Exit(1)
	}
	err = json.Unmarshal(jString, &authList)
	if err != nil {
		fmt.Println("authlist.json -> AuthList err: ", err)
		os.Exit(1)
	}
	fmt.Println("loaded authlist.json")
	return &authList
}
func WriteAuthList(authList *AuthList) {
	jString, err := json.Marshal(authList)
	if err != nil {
		fmt.Println("AuthList -> languages.json err: ", err)
		os.Exit(1)
	}
	err = ioutil.WriteFile("../util/authlist.json", jString, os.ModeAppend)
	if err != nil {
		fmt.Println("authlist.json: ", err)
		os.Exit(1)
	}
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
func listAppend(id string, list *[]string) bool {
	for _, v := range *list {
		if v == id {
			return false
		}
	}
	*list = append(*list, id)
	return true
}
func listDelete(id string, list *[]string) bool {
	for i, v := range *list {
		if v == id {
			*list = append((*list)[:i], (*list)[i+1:]...)
			return true
		}
	}
	return false
}
func Authorize() {
	if len(os.Args) < 4 {
		fmt.Println("Parameters error.")
		os.Exit(1)
	}
	isDatapack := false
	if os.Args[2] == "-d" {
		isDatapack = true
	} else if os.Args[2] != "-a" {
		fmt.Println("You must choose a type. '-a' or '-d'.")
		os.Exit(1)
	}
	id := os.Args[3]

	aList := GetAuthList()
	if isDatapack {
		success := listDelete(id, &aList.UnAuthorized)
		if success {
			fmt.Println("Removed '" + id + "' from 'unauth'.")
		}
		success = listAppend(id, &aList.Authorized.Datapacks)
		if success {
			fmt.Println("Appended '" + id + "' to 'auth.datapacks'.")
		}
		aList.Queue.Datapacks = append(aList.Queue.Datapacks, id)
	} else {
		success := listAppend(id, &aList.Authorized.Authors)
		if success {
			fmt.Println("Appended '" + id + "' to 'auth.authors.")
		}
		aList.Queue.Datapacks = append(aList.Queue.Authors, id)
	}
	WriteAuthList(aList)
}
func UnAuthorize() {
	if len(os.Args) < 4 {
		fmt.Println("Parameters error.")
		os.Exit(1)
	}
	isDatapack := false
	if os.Args[2] == "-d" {
		isDatapack = true
	} else if os.Args[2] != "-a" {
		fmt.Println("You must choose a type. '-a' or '-d'.")
		os.Exit(1)
	}
	id := os.Args[3]

	aList := GetAuthList()
	if isDatapack {
		success := listDelete(id, &aList.Authorized.Datapacks)
		if success {
			fmt.Println("Removed '" + id + "' from 'auth.datapacks'.")
		}
		success = listAppend(id, &aList.UnAuthorized)
		if success {
			fmt.Println("Appended '" + id + "' to 'unauth'.")
		}
		aList.Queue.Datapacks = append(aList.Queue.Datapacks, id)
	} else {
		success := listDelete(id, &aList.Authorized.Authors)
		if success {
			fmt.Println("Removed '" + id + "' from 'auth.authors'.")
		}
		aList.Queue.Datapacks = append(aList.Queue.Authors, id)
	}
	WriteAuthList(aList)
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
func getRow(id string, table string) map[string]interface{} {
	var s = db
	result := make(map[string]interface{})
	rows, err := s.Raw("select * from " + table + "s where id = '" + id + "'").Rows()
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
	return result
}
func Query() {
	if len(os.Args) < 4 {
		fmt.Println("Parameters error.")
		os.Exit(1)
	}
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

	for k, v := range getRow(id, table) {
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
func Update() {
	if len(os.Args) < 6 {
		fmt.Println("Parameters error.")
		os.Exit(1)
	}
	table := "author"
	if os.Args[2] == "-d" {
		table = "datapack"
	} else if os.Args[2] == "-t" {
		table = "tag"
	} else if os.Args[2] != "-a" {
		fmt.Println("You must choose a table. '-a' or '-d'.")
		os.Exit(1)
	}
	id, column, content := os.Args[3], os.Args[4], os.Args[5]
	if id == "" || column == "" || content == "" {
		fmt.Println("You must input id, column and content.")
		os.Exit(1)
	}

	if v, ok := getRow(id, table)[column]; ok {
		vType := reflect.TypeOf(v)
		switch vType.String() {
		case "int64":
			fmt.Println("from '" + strconv.FormatInt(v.(int64), 10) + "' to '" + content + "';")
		case "string":
			vl := v.(string)
			fmt.Println("from '" + vl + "' to '" + content + "'")
		case "time.Time":
			fmt.Println("from '" + v.(time.Time).Format("2006-01-02 15:04:05") + "' to '" + content + "';")
		case "[]uint8":
			vl := string(v.([]uint8))
			fmt.Println("from '" + vl + "' to '" + content + "';")
		default:
			fmt.Println("Do not support '" + vType.String() + "';")
			return
		}
		db.Exec("update " + table + "s set " + column + " = '" + content + "' where id = '" + id + "';")
		fmt.Println("Updated '" + column + "' of '" + id + "' successfully.")
	} else {
		fmt.Println("No record.")
		os.Exit(0)
	}
}

func main() {
	//connect to database
	Connect()
	defer db.Close() //close database
	flag.Usage = func() {
		_, err := fmt.Fprintf(os.Stderr, `admin:
Usage:
admin auth [-a | -d] [id]
admin unauth [-a | -d] [id]
admin combine [-a | -d] [id1] [id2]
admin query [-a | -d | -t] [id] 
admin update [-a | -d | -t] [id] [column] "[content]"
Options:
`)
		if err != nil {
			panic(err)
		}
		flag.PrintDefaults()
	}
	if os.Args[1] == "auth" {
		Authorize()
	} else if os.Args[1] == "unauth" {
		UnAuthorize()
	} else if os.Args[1] == "combine" {
		Combine()
	} else if os.Args[1] == "query" {
		Query()
	} else if os.Args[1] == "update" {
		Update()
	} else {
		fmt.Println("unknown command. -h see usage.")
	}
}
