package main

import (
	"github.com/gin-gonic/gin"
	"html/template"
	"net/http"
	"strconv"
)

func unescaped(x string) interface{} { return template.HTML(x) }
func getLanguage(c *gin.Context) string {
	lang := c.Query("language")
	if lang == "" {
		lang = "default"
	}
	return lang
}
func getPage(c *gin.Context) int {
	page := c.Query("p")
	p, err := strconv.Atoi(page)
	if err != nil {
		p = 1
	}
	return p
}
func getStyle(c *gin.Context) string {
	cookie, e := c.Request.Cookie("style")
	if e == nil {
		return cookie.Value
	} else {
		return "normal"
	}
}
func getOrder(orderId string, language string) string {
	orderName := orderByPostTimeDesc
	switch orderId {
	case "1":
		orderName = orderByPostTime
	case "2":
		orderName = orderByUpdateTimeDesc
	case "3":
		orderName = orderByUpdateTime
	case "4":
		orderName = "default_name"
		if language != "" && language != "default" {
			orderName = "name_" + language
		}
	}
	return orderName
}

func renderDatapacks(c *gin.Context, page int, total int, language string, datapacks *[]Datapack) {
	c.HTML(http.StatusOK, language+"/datapacks.html", gin.H{
		//domain
		"Domain": "datapacks",
		//style
		"Style": getStyle(c),
		//result-related
		"Datapacks": datapacks,
		"NoResult":  len(*datapacks) == 0,
		//page-related
		"PageNotEnd":  page*datapackPageCount < total,
		"OffsetCount": (page-1)*datapackPageCount + 1,
		"EndCount":    (page-1)*datapackPageCount + len(*datapacks),
		"TotalCount":  total,
		"Page":        page,
	})
}
func renderDatapack(c *gin.Context, language string, datapack *Datapack) {
	c.HTML(http.StatusOK, language+"/datapack.html", gin.H{
		//domain
		"Domain": datapack.Name,
		//style
		"Style": getStyle(c),
		//result-related
		"Datapack":  datapack,
		"IsRelated": len(datapack.RelatedDatapacks) > 0,
		"NoResult":  datapack == nil,
	})
}
func renderAuthors(c *gin.Context, page int, total int, language string, authors *[]Author) {
	c.HTML(http.StatusOK, language+"/authors.html", gin.H{
		//domain
		"Domain": "authors",
		//style
		"Style": getStyle(c),
		//result-related
		"Authors":  authors,
		"NoResult": len(*authors) == 0,
		//page-related
		"PageNotEnd":  page*authorPageCount < total,
		"OffsetCount": (page-1)*authorPageCount + 1,
		"EndCount":    (page-1)*authorPageCount + len(*authors),
		"TotalCount":  total,
		"Page":        page,
	})
}
func renderAuthor(c *gin.Context, language string, author *Author) {
	sourcesMap := make(map[string]string) //Source / Last Update Time Analysis
	lastUpdateTime := ""
	if len(author.Datapacks) > 0 { // This Source
		sourcesMap[author.Datapacks[0].Source] = author.ID
	}
	for i := 0; i < len(author.RelatedAuthors); i++ {
		if len(author.RelatedAuthors[i].Datapacks) > 0 { // Related Sources
			sourcesMap[author.RelatedAuthors[i].Datapacks[0].Source] = author.RelatedAuthors[i].ID
		}
		author.Datapacks = append(author.Datapacks, author.RelatedAuthors[i].Datapacks...)
	}
	for i := 0; i < len(author.Datapacks); i++ {
		author.Datapacks[i].Initialize() // Initialize
		if author.Datapacks[i].UpdateTimeString > lastUpdateTime {
			lastUpdateTime = author.Datapacks[i].UpdateTimeString
		}
	}
	c.HTML(http.StatusOK, language+"/author.html", gin.H{
		//domain
		"Domain": author.AuthorName,
		//style
		"Style": getStyle(c),
		//result-related
		"Author":         author,
		"TotalCount":     len(author.Datapacks),
		"Sources":        sourcesMap,
		"LastUpdateTime": lastUpdateTime,
	})
}
func renderTags(c *gin.Context, page int, total int, language string, tags *[]Tag) {
	c.HTML(http.StatusOK, language+"/tags.html", gin.H{
		//domain
		"Domain": "tags",
		//style
		"Style": getStyle(c),
		//result-related
		"Tags":     tags,
		"NoResult": len(*tags) == 0,
		//page-related
		"PageNotEnd":  page*tagPageCount < total,
		"OffsetCount": (page-1)*tagPageCount + 1,
		"EndCount":    (page-1)*tagPageCount + len(*tags),
		"TotalCount":  total,
		"Page":        page,
	})
}
func renderTag(c *gin.Context, language string, tag *Tag) {
	if tag.Type == 0 {
		c.Redirect(http.StatusMovedPermanently, "/?source="+tag.DefaultTag)
	} else if tag.Type == 1 {
		c.Redirect(http.StatusMovedPermanently, "/?version="+tag.DefaultTag)
	} else {
		synonymous := tag.GetSynonymousTag(language)
		c.HTML(http.StatusOK, language+"/tag.html", gin.H{
			//domain
			"Domain": tag.Tag,
			//style
			"Style": getStyle(c),
			//result-related
			"Tag":             tag,
			"TotalCount":      len(tag.Datapacks),
			"Synonymous":      synonymous,
			"SynonymousCount": len(*synonymous),
		})
	}
}

func thumbByID(c *gin.Context) {
	table := c.PostForm("table")
	id := c.PostForm("id")
	if id == "" || table == "" {
		return
	}
	Thumb(table, id)
}
func queryAPI(c *gin.Context, data interface{}) {
	c.JSON(http.StatusOK, gin.H{
		"status": 200,
		"error":  nil,
		"data":   data,
	})
}

func index(c *gin.Context) {
	lang := getLanguage(c)
	p := getPage(c)
	order := c.Query("order")
	orderName := getOrder(order, lang)
	postTime := c.Query("p_time")
	postTimeRange, err := strconv.Atoi(postTime)
	if err != nil {
		postTimeRange = 0
	}
	updateTime := c.Query("u_time")
	updateTimeRange, err := strconv.Atoi(updateTime)
	if err != nil {
		updateTimeRange = 0
	}
	filterSource := c.Query("source")
	filterVersion := c.Query("version")
	datapacks, total := ListDatapacks(lang, p, orderName, filterSource, filterVersion, postTimeRange, updateTimeRange)
	// api service
	api := c.Query("api")
	if api != "" {
		queryAPI(c, datapacks)
	} else {
		// html render
		renderDatapacks(c, p, total, lang, datapacks)
	}
}
func search(c *gin.Context) {
	var datapacks *[]Datapack
	total := 0
	p := getPage(c)
	search := c.Query("search")
	postTime := c.Query("p_time")
	postTimeRange, err := strconv.Atoi(postTime)
	if err != nil {
		postTimeRange = 0
	}
	updateTime := c.Query("u_time")
	updateTimeRange, err := strconv.Atoi(updateTime)
	if err != nil {
		updateTimeRange = 0
	}
	filterSource := c.Query("source")
	filterVersion := c.Query("version")
	lang := getLanguage(c)
	if search != "" {
		datapacks, total = SearchDatapacks(lang, p, search, filterSource, filterVersion, postTimeRange, updateTimeRange)
	} else {
		nameContent := c.Query("name")
		introContent := c.Query("intro")
		authorContent := c.Query("author")
		if nameContent == "" && introContent == "" && authorContent != "" {
			c.Redirect(http.StatusMovedPermanently, "/author?author="+authorContent)
		}
		datapacks, total = AccurateSearchDatapacks(lang, p, nameContent, introContent, authorContent, filterSource, filterVersion, postTimeRange, updateTimeRange)
	}
	// api service
	api := c.Query("api")
	if api != "" {
		queryAPI(c, datapacks)
	} else {
		// html render
		renderDatapacks(c, p, total, lang, datapacks)
	}
}
func datapack(c *gin.Context) {
	id := c.Param("id")
	lang := getLanguage(c)
	datapack := GetDatapack(lang, id)
	// api service
	api := c.Query("api")
	if api != "" {
		queryAPI(c, datapack)
	} else {
		// html render
		renderDatapack(c, lang, datapack)
	}
}
func datapackRand(c *gin.Context) {
	lang := getLanguage(c)
	datapack := GetRandDatapack(lang)
	// api service
	api := c.Query("api")
	if api != "" {
		queryAPI(c, datapack)
	} else {
		// html render
		renderDatapack(c, lang, datapack)
	}
}
func authorList(c *gin.Context) {
	name := c.Query("author")
	lang := getLanguage(c)
	p := getPage(c)
	authors, total := ListAuthors(p, name)
	// api service
	api := c.Query("api")
	if api != "" {
		queryAPI(c, authors)
	} else {
		// html render
		renderAuthors(c, p, total, lang, authors)
	}
}
func author(c *gin.Context) {
	id := c.Param("id")
	p := getPage(c)
	lang := getLanguage(c)
	author := GetAuthor(lang, id)
	// api service
	api := c.Query("api")
	// html render
	if author == nil { // No Result
		authors, total := ListAuthors(p, id)
		if api != "" {
			queryAPI(c, authors)
		} else {
			renderAuthors(c, p, total, lang, authors)
		}
	} else {
		if api != "" {
			queryAPI(c, author)
		} else {
			renderAuthor(c, lang, author)
		}
	}
}
func authorRand(c *gin.Context) {
	lang := getLanguage(c)
	author := GetRandAuthor(lang)
	// api service
	api := c.Query("api")
	if api != "" {
		queryAPI(c, author)
	} else {
		// html render
		renderAuthor(c, lang, author)
	}
}
func tagList(c *gin.Context) {
	name := c.Query("tag")
	lang := getLanguage(c)
	p := getPage(c)
	tags, total := ListTags(lang, p, name)
	// api service
	api := c.Query("api")
	if api != "" {
		queryAPI(c, tags)
	} else {
		// html render
		renderTags(c, p, total, lang, tags)
	}
}
func tag(c *gin.Context) {
	id := c.Param("id")
	p := getPage(c)
	lang := getLanguage(c)
	tag := GetTag(lang, id)
	// api service
	api := c.Query("api")
	// html render
	if tag == nil { // No Result
		tags, total := ListTags(lang, p, id)
		if api != "" {
			queryAPI(c, tags)
		} else {
			renderTags(c, p, total, lang, tags)
		}
	} else {
		if api != "" {
			queryAPI(c, tag)
		} else {
			renderTag(c, lang, tag)
		}
	}
}
func tagRand(c *gin.Context) {
	lang := getLanguage(c)
	tag := GetRandTag(lang)
	// html render
	renderTag(c, lang, tag)
}

func language(c *gin.Context) {
	languages := GetLanguages()
	mapLang := make(map[string]string)
	for k, v := range *languages {
		mapLang[k] = v.(map[string]interface{})["name"].(string)
	}
	lang := getLanguage(c)
	c.HTML(http.StatusOK, lang+"/language.html", gin.H{
		//domain
		"Domain": "languages",
		//style
		"Style": getStyle(c),
		//result-related
		"languages": mapLang,
	})
}
func guide(c *gin.Context) {
	lang := getLanguage(c)
	c.HTML(http.StatusOK, lang+"/guide.html", gin.H{
		//domain
		"Domain": "guide",
		//style
		"Style": getStyle(c),
	})
}
func about(c *gin.Context) {
	lang := getLanguage(c)
	c.HTML(http.StatusOK, lang+"/about.html", gin.H{
		//domain
		"Domain": "about",
		//style
		"Style": getStyle(c),
	})
}
