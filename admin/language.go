package main

import (
	"bytes"
	"encoding/json"
	"flag"
	"fmt"
	"io"
	"io/ioutil"
	"os"
	"path"
	"path/filepath"
	"strings"
)

type Language struct {
	Name string `json:"name"`
}

var h = flag.Bool("h", false, "help")
var c = flag.Bool("c", false, "create a new language")
var d = flag.Bool("d", false, "delete a language")
var u = flag.Bool("u", false, "update a language")
var a = flag.Bool("a", false, "select all")
var id = flag.String("id", "", "the id of the language")
var name = flag.String("name", "", "the name of the language")

func GetLanguages(parent string) *map[string]Language {
	var languages map[string]Language
	jstring, err := ioutil.ReadFile(parent + "\\util\\languages.json")
	if err != nil {
		fmt.Println("languages.json: ", err)
		os.Exit(1)
	}
	err = json.Unmarshal(jstring, &languages)
	if err != nil {
		fmt.Println("languages.json -> map[Language] err: ", err)
		os.Exit(1)
	}
	fmt.Println("loaded", parent+"\\util\\languages.json")
	return &languages
}
func WriteLanguage(parent string, languages *map[string]Language) {
	jstring, err := json.Marshal(languages)
	if err != nil {
		fmt.Println("map[Language] -> languages.json err: ", err)
		os.Exit(1)
	}
	err = ioutil.WriteFile(parent+"\\util\\languages.json", jstring, os.ModeAppend)
	if err != nil {
		fmt.Println("languages.json: ", err)
		os.Exit(1)
	}
}
func FileCopy(src, dst string, id string) error {
	var err error
	var srcfd *os.File
	var dstfd *os.File
	var srcinfo os.FileInfo

	if srcfd, err = os.Open(src); err != nil {
		return err
	}
	defer srcfd.Close()

	if dstfd, err = os.Create(dst); err != nil {
		return err
	}
	defer dstfd.Close()

	if _, err = io.Copy(dstfd, srcfd); err != nil {
		return err
	}
	if srcinfo, err = os.Stat(src); err != nil {
		return err
	}

	tmpl, err := ioutil.ReadFile(dst)
	if err != nil {
		fmt.Println(dst+": ", err)
	}
	err = ioutil.WriteFile(dst, bytes.ReplaceAll(tmpl, []byte("default/"), []byte(strings.ReplaceAll(id, "-", "_")+"/")), os.ModeAppend)
	if err != nil {
		fmt.Println(dst+": ", err)
	}
	return os.Chmod(dst, srcinfo.Mode())
}
func DirCopy(src string, dst string, id string) error {
	var err error
	var fds []os.FileInfo
	var srcinfo os.FileInfo

	if srcinfo, err = os.Stat(src); err != nil {
		return err
	}

	if err = os.MkdirAll(dst, srcinfo.Mode()); err != nil {
		return err
	}

	if fds, err = ioutil.ReadDir(src); err != nil {
		return err
	}
	for _, fd := range fds {
		srcfp := path.Join(src, fd.Name())
		dstfp := path.Join(dst, fd.Name())

		if fd.IsDir() {
			if err = DirCopy(srcfp, dstfp, id); err != nil {
				fmt.Println(err)
			}
		} else {
			if err = FileCopy(srcfp, dstfp, id); err != nil {
				fmt.Println(err)
			}
		}
	}
	return nil
}

func main() {
	parent, err := filepath.Abs("..")
	if err != nil {
		fmt.Println(err)
	}
	languages := GetLanguages(parent)
	flag.Usage = func() {
		_, err := fmt.Fprintf(os.Stderr, `language:
Usage: language -c [-id id] [-name name] | -d [-id id] | -u [-a | -id id]
Options:
`)
		if err != nil {
			panic(err)
		}
		flag.PrintDefaults()
	}
	flag.Parse()
	if *id == "default" || *id == "generic" {
		fmt.Println("id can't be '" + *id + "'")
		os.Exit(2)
	}
	if *h { // Help
		flag.Usage()
	}
	if *c { // Create
		if *id == "" || *name == "" {
			fmt.Println("the new language should have id and name")
			os.Exit(2)
		}
		_, ok := (*languages)[*id]
		if ok {
			fmt.Println(*id, "language already exists")
			os.Exit(2)
		}
		(*languages)[*id] = Language{Name: *name}
		err := DirCopy(parent+"\\templates\\default", parent+"\\templates\\"+strings.ReplaceAll(*id, "-", "_"), *id)
		if err != nil {
			fmt.Println(err)
			os.Exit(1)
		}
		WriteLanguage(parent, languages)
		fmt.Println(*id, "created")
	}
	if *u { // Update
		if *id == "" && !*a {
			fmt.Println("the language to update should have id")
			os.Exit(2)
		}
		if *id != "" {
			_, ok := (*languages)[*id]
			if !ok {
				fmt.Println(*id, "language does not exist")
				os.Exit(2)
			}
		}
		var updates []string
		if *a {
			for i, _ := range *languages {
				updates = append(updates, i)
			}
		} else {
			updates = append(updates, *id)
		}
		for _, i := range updates { // Save translation & Remove & Copy & Write translation
			dir := parent + "\\templates\\" + strings.ReplaceAll(i, "-", "_")
			tmpl, err := ioutil.ReadFile(dir + "\\translation.tmpl") //save
			if err != nil {
				fmt.Println(dir+"\\translation.tmpl"+": ", err)
			}
			err = os.RemoveAll(dir) //remove
			if err != nil {
				fmt.Println(err)
				os.Exit(1)
			}
			err = DirCopy(parent+"\\templates\\default", dir, i) //copy
			if err != nil {
				fmt.Println(err)
				os.Exit(1)
			}
			err = ioutil.WriteFile(dir+"\\translation.tmpl", tmpl, os.ModeAppend) //write
			if err != nil {
				fmt.Println(dir+"\\translation.tmpl"+": ", err)
			}
			fmt.Println(i, "updated")
		}
	}
	if *d { // Delete
		if *id == "" {
			fmt.Println("the language to be deleted should have id")
			os.Exit(2)
		}
		_, ok := (*languages)[*id]
		if !ok {
			fmt.Println(*id, "language does not exist")
			os.Exit(2)
		}
		delete(*languages, *id)
		err := os.RemoveAll(parent + "\\templates\\" + strings.ReplaceAll(*id, "-", "_"))
		if err != nil {
			fmt.Println(err)
			os.Exit(1)
		}
		WriteLanguage(parent, languages)
		fmt.Println(*id, "deleted")
	}
}
