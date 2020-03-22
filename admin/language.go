package main

import (
	"encoding/json"
	"flag"
	"fmt"
	"io"
	"io/ioutil"
	"os"
	"path"
	"path/filepath"
)

type Language struct {
	Name string `json:"name"`
}

var h = flag.Bool("h", false, "help")
var c = flag.Bool("c", false, "create a new language")
var d = flag.Bool("d", false, "delete a language")
var id = flag.String("id", "", "the id of the language")
var name = flag.String("name", "", "the name of the language")

func GetLanguages(parent string) *map[string]Language {
	var languages map[string]Language
	jstring, err := ioutil.ReadFile(parent + "\\util\\languages.json")
	if err != nil {
		fmt.Println("languages.json: ", err)
	}
	err = json.Unmarshal(jstring, &languages)
	if err != nil {
		fmt.Println("languages.json -> map[Language] err: ", err)
	}
	fmt.Println("loaded", parent + "\\util\\languages.json")
	return &languages
}
func FileCopy(src, dst string) error {
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
		fmt.Println(dst + ": ", err)
	}
	ioutil.WriteFile(dst, tmpl, os.ModeAppend)
	return os.Chmod(dst, srcinfo.Mode())
}
func DirCopy(src string, dst string) error {
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
			if err = DirCopy(srcfp, dstfp); err != nil {
				fmt.Println(err)
			}
		} else {
			if err = FileCopy(srcfp, dstfp); err != nil {
				fmt.Println(err)
			}
		}
	}
	return nil
}

func main() {
	parent, err := filepath.Abs(filepath.Dir(filepath.Dir(os.Args[0])))
	if err != nil {
		fmt.Println(err)
	}
	languages := GetLanguages(parent)
	flag.Usage = func() {
		_, err := fmt.Fprintf(os.Stderr, `language:
Usage: language -c [-id id] [-name name] | -d [-id id]
Options:
`)
		if err != nil {
			panic(err)
		}
		flag.PrintDefaults()
	}
	flag.Parse()
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
		(*languages)[*id] = Language{Name:*name}
		err := DirCopy(parent + "\\templates\\default", parent + "\\templates\\" + *id)
		if err != nil {
			fmt.Println(err)
			os.Exit(1)
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
		err := os.RemoveAll(parent + "\\templates\\" + *id)
		if err != nil {
			fmt.Println(err)
			os.Exit(1)
		}
	}
}