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
	/*
	var sum int64
	for i:= 0; i < 100; i++ {
		t1 := time.Now()
		v, _ := ListAuthors(1, "")
		vs := GetAuthor("", (*v)[0].ID)
		fmt.Println(vs.Datapacks[0].Tags[4].Tag)
		t2 := time.Now()
		fmt.Println(t2.Sub(t1))
		sum += t2.Sub(t1).Nanoseconds()
	}
	fmt.Println(sum/1e8, "ms")
	*//*
	dps, total := ListDatapacks("",1,orderByPostTimeDesc,"","1.14",0,0)
	fmt.Println(total)
	for _, v := range *dps {
		fmt.Println(v.Name + " " + v.DefaultName + " " + v.Tags[2].Tag + " " + v.Author.AuthorName)
	}
	fmt.Println("==== Search")
	dp, total := SearchDatapacks("", 1, "羊", "", "", 0, 0)
	fmt.Println(total)
	for _, v := range *dp {
		fmt.Print(v.Name + " " + v.Tags[2].Tag + " ")
		fmt.Println(v.KeyWordCount)
	}
	fmt.Println("==== AccurateSearch")
	dp, total := AccurateSearchDatapacks("",1, "矿", "", "", "", "", 0, 0)
	fmt.Println(total)
	for _, v := range *dp {
		fmt.Print(v.Name + " " + v.Tags[2].Tag + " ")
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
	_ = r.Run(":8080")/**/
}