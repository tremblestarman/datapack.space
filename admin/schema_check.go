package main

import (
	"encoding/json"
	"fmt"
	"io/ioutil"
	"os"
	"path/filepath"
)

func main() {
	// Open
	parent, err := filepath.Abs("..")
	if err != nil {
		fmt.Println(err)
	}
	var schema map[string]interface{}
	jString, err := ioutil.ReadFile(parent + "\\util\\" + os.Args[1] + ".json")
	if err != nil {
		fmt.Println("open schema '"+os.Args[1]+"' error :", err)
		os.Exit(1)
	}
	err = json.Unmarshal(jString, &schema)
	if err != nil {
		fmt.Println("schema '"+os.Args[1]+"' format error :", err)
		os.Exit(1)
	}
	// Analyze
	// ...
}
