package main

import (
	"encoding/json"
	"fmt"
	"io/ioutil"
	"os"
	"path/filepath"
	"reflect"
	"strconv"
	"strings"
)

type Schema struct {
	Domain      string                 `json:"domain" required:"true"`
	ID          string                 `json:"id" required:"true"`
	Name        string                 `json:"name" required:"true"`
	Language    string                 `json:"lang" required:"true"`
	Scan        Scan                   `json:"scan" required:"true"`
	Sleep       float32                `json:"sleep" required:"false" default:"0.5"`
	Timeout     float32                `json:"timeout" required:"false" default:"5"`
	AsyncCount  int                    `json:"async_count" required:"false" default:"32"`
	Retry       int                    `json:"retry" required:"false" default:"2"`
	PostPath    interface{}            `json:"post_path" required:"true" support:"string,map"`
	PostType    string                 `json:"post_type" required:"false" default:"html"`
	InfoCollect map[string]interface{} `json:"info_collect" required:"true" support:"map"`
	InfoRefine  map[string]interface{} `json:"info_refine" required:"false" default:"empty" support:"map"`
	InfoAdapt   map[string]interface{} `json:"info_adapt" required:"false" default:"empty" support:"map"`
}
type Scan struct {
	Type          string `json:"type"`
	Entrance      string `json:"entrance"`
	PageStart     int    `json:"page_start"`
	PageIncrement int    `json:"page_increment"`
	PageMax       int    `json:"page_max"`
	Display       string `json:"display"`
	NextXPath     string `json:"next_xpath"`
}

func MapOrString(i interface{}) string {
	switch i.(type) {
	case map[string]interface{}:
		return "map"
	case string:
		return "string"
	default:
		return "unknown"
	}
}
func (schema *Schema) CheckSchema() {
	_type := reflect.TypeOf(*schema)
	_val := reflect.ValueOf(*schema)
	for i := 0; i < _type.NumField(); i++ {
		t := _type.Field(i)
		v := _val.Field(i)
		_json := t.Tag.Get("json")
		_required := t.Tag.Get("required")
		_default := t.Tag.Get("default")
		_support := t.Tag.Get("support")
		if !v.IsValid() {
			if _required == "true" { // Required parameter
				errorList = append(errorList, "- *\""+_json+"\":\nInvalid value.")
			} else { // Not required parameter, set default
				infoList = append(infoList, "- \""+_json+"\":\n"+_default)
			}
			continue // If value is invalid, skip this field
		}
		if _support != "" && !strings.Contains(_support, MapOrString(_val.FieldByName(t.Name).Interface())) { // Type error
			errorList = append(errorList, "- *\""+_json+"\":\nType error. ('"+
				strings.ReplaceAll(_support, ",", " or ")+
				"', but got '"+MapOrString(v)+"'.)")
			continue // If type error, skip this field.
		}
		value := ""
		if v.Kind().String() == "string" { // If value is a string,
			value = v.String()
		} else if v.Kind().String() == "int" { // If value is a int.
			value = strconv.FormatInt(v.Int(), 10)
		} else if v.Kind().String() == "float32" { // If value is a float.
			value = strconv.FormatFloat(v.Float(), 'f', 3, 32)
		}
		// Append to info list
		if value != "" {
			if _required == "true" {
				infoList = append(infoList, "- *\""+_json+"\":\n"+value)
			} else {
				infoList = append(infoList, "- \""+_json+"\":\n"+value)
			}
		}
	}
	schema.Scan.CheckScanner()
	if MapOrString(schema.InfoCollect) == "map" {
		schema.CheckSelectors()
	}
	if MapOrString(schema.InfoRefine) == "map" {
		schema.CheckRefiners()
	}
	if MapOrString(schema.InfoAdapt) == "map" {
		schema.CheckAdaptors()
	}
}
func (scan *Scan) CheckScanner() {
	infoList = append(infoList, "- *\"scan\":")
	if scan.Entrance == "" {
		errorList = append(errorList, "  -- *\"scan.entrance\":\nInvalid value.")
	} else {
		infoList = append(infoList, "  -- *\"scan.entrance\":\n"+scan.Entrance)
	}
	if scan.Type == "normal" {
		infoList = append(infoList, "  -- *\"scan.type\":\n"+scan.Type)
		infoList = append(infoList, "  -- \"scan.page_start\":\n"+strconv.Itoa(scan.PageStart))
		if scan.PageIncrement == 0 {
			errorList = append(errorList, "  -- \"scan.page_increment\":\nAdd 0 is meaningless.")
		} else {
			infoList = append(infoList, "  -- \"scan.page_increment\":\n"+strconv.Itoa(scan.PageIncrement))
		}
		infoList = append(infoList, "  -- \"scan.page_max\":\n"+strconv.Itoa(scan.PageMax))
	} else if scan.Type == "selenium" {
		infoList = append(infoList, "  -- *\"scan.type\":\n"+scan.Type)
		if scan.Display != "" {
			scan.Display = "windows"
		}
		if scan.Display != "window" && scan.Display != "virtual" && scan.Display != "headless" {
			errorList = append(errorList, "  -- *\"scan.display\":\nInvalid value. (Must be 'window', 'virtual', 'headless')")
		} else {
			infoList = append(infoList, "  -- *\"scan.display\":\n"+scan.Display)
		}
		if scan.NextXPath == "" {
			errorList = append(errorList, "  -- *\"scan.next_xpath\":\nInvalid value. (Must be Xpath of 'next' button)")
		} else {
			infoList = append(infoList, "  -- *\"scan.next_xpath\":\n"+scan.NextXPath)
		}
	} else {
		errorList = append(errorList, "  -- *\"scan.type\":\nInvalid value. (Must be 'normal' or 'selenium')")
	}
}

var localParams map[string]bool

func (schema *Schema) CheckSelectors() {
	localParams = make(map[string]bool)
	if len(schema.InfoCollect) > 0 {
		hasError := false
		for k, _ := range schema.InfoCollect {
			hasError = false /////////
			if len(k) > 0 && k[0] == '$' {
				localParams[k] = true
			} else {
				localParams[k] = false
			}
		}
		if hasError {
			infoList = append(infoList, "- *\"info_collect\":\nError occurs. See errors.")
		} else {
			infoList = append(infoList, "- *\"info_collect\":\nNo error.")
		}
	} else {
		errorList = append(errorList, "- *\"info_collect\":\nShould not be empty.")
	}
}
func (schema *Schema) CheckRefiners() {
	if len(schema.InfoCollect) > 0 {
		hasError := false
		for k, v := range schema.InfoRefine {
			if _, ok := localParams[k]; ok {
				_type := MapOrString(v)
				if _type == "map" {
					for _k := range v.(map[string]interface{}) {
						if !(strings.Contains(_k, "remove") || strings.Contains(_k, "replace") || strings.Contains(_k, "regex") || _k == "hide") {
							errorList = append(errorList, "  -- *\"info_refine."+k+
								"\":\nUnknown operation '"+_k+
								"'. (Must be 'hide' or contain substring 'remove', 'replace', or 'regex'.)")
							hasError = true
						}
					}
				} else {
					errorList = append(errorList, "  -- *\"info_refine."+k+"\":\nType error. (Must be a map.)")
					hasError = true
				}
			} else {
				errorList = append(errorList, "  -- *\"info_refine."+k+
					"\":\nDo not exists. (Should have been declared in 'info_collect' first.)")
				hasError = true
			}
		}
		if hasError {
			infoList = append(infoList, "- *\"info_refine\":\nError occurs. See errors.")
		} else {
			infoList = append(infoList, "- *\"info_refine\":\nNo error.")
		}
	}
}
func (schema *Schema) CheckAdaptors() {
	if len(schema.InfoCollect) > 0 {
		hasError := false
		for k, v := range schema.InfoRefine {
			if _, ok := localParams[k]; ok {
				_type := MapOrString(v)
				if _type != "string" {
					errorList = append(errorList, "  -- *\"info_adapt."+k+"\":\nType error. (Must be a string.)")
					hasError = true
				}
			} else {
				errorList = append(errorList, "  -- *\"info_adapt."+k+
					"\":\nDo not exists. (Should have been declared in 'info_collect' first.)")
				hasError = true
			}
		}
		if hasError {
			infoList = append(infoList, "- *\"info_adapt\":\nError occurs. See errors.")
		} else {
			infoList = append(infoList, "- *\"info_adapt\":\nNo error.")
		}
	}
}

var infoList []string
var errorList []string

func main() {
	// Open
	parent, err := filepath.Abs("..")
	if err != nil {
		fmt.Println(err)
	}
	var schema Schema
	// set default
	schema.Sleep = 0.5
	schema.Timeout = 5
	schema.AsyncCount = 32
	schema.Retry = 2
	schema.Scan.PageStart = 0
	schema.Scan.PageIncrement = 1
	schema.Scan.PageMax = -1 //os.Args[1]
	// read json
	jString, err := ioutil.ReadFile(parent + "\\util\\schema\\" + "datapackcenter" + ".json")
	if err != nil {
		fmt.Println("open schema '"+"mcbbs"+"' error :", err)
		os.Exit(1)
	}
	err = json.Unmarshal(jString, &schema)
	if err != nil {
		fmt.Println("schema '"+"mcbbs"+"' format error :", err)
		os.Exit(1)
	}
	// Analyze
	schema.CheckSchema()
	for _, e := range errorList {
		fmt.Println(e)
	}
	fmt.Println("========")
	for _, i := range infoList {
		fmt.Println(i)
	}
}
