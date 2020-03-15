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
	/*dps, total := ListDatapacks("en",1,orderByPostTimeDesc,"mcbbs","1.15")
	fmt.Println(total)
	for _, v := range *dps {
		fmt.Println(v.Name + " " + v.DefaultName + " " + v.Tags[2].Tag)
	}
	fmt.Println("==== Search")
	for _, v := range *SearchDatapacks(1, "挖掘任意木头") {
		fmt.Print(v.Name + " " + v.NameZh + " ")
		fmt.Println(v.KeyWordCount)
	}
	fmt.Println("==== AccurateSearch")
	for _, v := range *AccurateSearchDatapacks(1, "砍树", "", "", 0, 0) {
		fmt.Print(v.Name + " " + v.NameZh + " ")
		fmt.Println(v.KeyWordCount)
	}
	fmt.Println("==== Today")
	for _, v := range *AccurateSearchDatapacks(1, "", "", "", 1, 0) {
		fmt.Print(v.Name + " " + v.NameZh + " ")
		fmt.Println(v.KeyWordCount)
	}
	fmt.Println("==== Tags")
	for _, v := range *ListTags(1,"Rec") {
		fmt.Print(v.Tag, " ", v.Type, " ")
		fmt.Println(v.KeyWordCount)
		for _, d := range v.Datapacks {
			fmt.Println("| ", d.NameZh)
		}
	}
	fmt.Println("==== Authors")
	for _, v := range *ListAuthors(1,"tre") {
		fmt.Print(v.AuthorName, " ", v.ID, " ")
		fmt.Println(v.KeyWordCount)
		for _, d := range v.Datapacks {
			fmt.Println("| ", d.NameZh)
		}
	}*/
	r := gin.Default()
	r.SetFuncMap(template.FuncMap{
		"unescaped": unescaped,
	})
	r.Static("/bin", "./bin")
	r.LoadHTMLGlob("templates/**/*")
	r.GET("/", index)
	r.GET("/datapack/:id", datapack)
	r.GET("/search", search)
	r.GET("/author", authorList)
	r.GET("/author/:id", author)
	r.GET("/tag", tagList)
	r.GET("/tag/:id", tag)
	_ = r.Run(":8080")
}