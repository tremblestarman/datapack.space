package main

import (
	"github.com/gin-gonic/gin"
	"html/template"
)

func main() {
	//connect to database
	Connect()
	defer db.Close()   //close database
	_ = seg.LoadDict() //load dict
	r := gin.Default()
	r.SetFuncMap(template.FuncMap{
		"unescaped": unescaped,
	})
	// Load Resources
	r.Static("/bin", "./bin")
	r.LoadHTMLGlob("templates/**/*")
	// Router
	r.GET("/", index)
	r.GET("/datapack/:id", datapack)
	r.GET("/random/datapack", datapackRand)
	r.GET("/search", search)
	r.GET("/author", authorList)
	r.GET("/author/:id", author)
	r.GET("/random/author", datapackRand)
	r.GET("/tag", tagList)
	r.GET("/tag/:id", tag)
	r.GET("/random/tag", datapackRand)
	_ = r.Run(":8080")
}