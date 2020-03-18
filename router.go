package main

import (
	"fmt"
	"github.com/gin-gonic/gin"
	"html/template"
	"net/http"
	"strconv"
)

func unescaped (x string) interface{} { return template.HTML(x) }
func getOrder (orderId string, language string) string {
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

func index(c *gin.Context) {
	page := c.Query("p")
	p, err := strconv.Atoi(page)
	lang := c.Query("language")
	if err != nil {
		p = 1
	}
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
	// html render
	if lang == "" {
		lang = "default"
	}
	c.HTML(http.StatusOK, lang + "/datapacks.html", gin.H {
		//domain
		"Domain": "datapacks",
		//result-related
		"Datapacks": datapacks,
		"NoResult": len(*datapacks) == 0,
		//page-related
		"PageNotEnd": p * datapackPageCount < total,
		"OffsetCount": (p - 1) * datapackPageCount + 1,
		"EndCount": (p - 1) * datapackPageCount + len(*datapacks),
		"TotalCount": total,
		"Page": p,
	})
}
func search(c *gin.Context) {
	var datapacks *[]Datapack
	total := 0
	page := c.Query("p")
	p, err := strconv.Atoi(page)
	if err != nil {
		p = 1
	}
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
	lang := c.Query("language")
	if search != "" {
		datapacks, total = SearchDatapacks(lang, p, search, filterSource, filterVersion, postTimeRange, updateTimeRange)
	} else {
		nameContent := c.Query("name")
		introContent := c.Query("intro")
		authorContent := c.Query("author")
		datapacks, total = AccurateSearchDatapacks(lang, p, nameContent, introContent, authorContent, filterSource, filterVersion, postTimeRange, updateTimeRange)
	}
	// html render
	if lang == "" {
		lang = "default"
	}
	c.HTML(http.StatusOK, lang + "/datapacks.html", gin.H {
		//domain
		"Domain": "datapacks",
		//result-related
		"Datapacks": datapacks,
		"NoResult": len(*datapacks) == 0,
		//page-related
		"PageNotEnd": p * datapackPageCount < total,
		"OffsetCount": (p - 1) * datapackPageCount + 1,
		"EndCount": (p - 1) * datapackPageCount + len(*datapacks),
		"TotalCount": total,
		"Page": p,
	})
}
func datapack(c *gin.Context) {
	id := c.Param("id")
	lang := c.Query("language")
	datapack := GetDatapack(lang, id)
	// html render
	if lang == "" {
		lang = "default"
	}
	c.HTML(http.StatusOK, lang + "/datapack.html", gin.H {
		//domain
		"Domain": datapack.Name,
		//result-related
		"Datapack": datapack,
		"NoResult": datapack == nil,
	})
}
func authorList(c *gin.Context) {
	page := c.Query("p")
	name := c.Query("author")
	lang := c.Query("language")
	p, err := strconv.Atoi(page)
	if err != nil {
		p = 1
	}
	authors, total := ListAuthors(p, name)
	// html render
	if lang == "" {
		lang = "default"
	}
	c.HTML(http.StatusOK, lang + "/authors.html", gin.H {
		//domain
		"Domain": "authors",
		//result-related
		"Authors": authors,
		"NoResult": len(*authors) == 0,
		//page-related
		"PageNotEnd": p * authorPageCount < total,
		"OffsetCount": (p - 1) * authorPageCount + 1,
		"EndCount": (p - 1) * authorPageCount + len(*authors),
		"TotalCount": total,
		"Page": p,
	})
}
func author(c *gin.Context) {
	id := c.Param("id")
	page := c.Query("p")
	p, err := strconv.Atoi(page)
	if err != nil {
		p = 1
	}
	lang := c.Query("language")
	if lang == "" {
		lang = "default"
	}
	author := GetAuthor(lang, id)
	// html render
	if author == nil { // No Result
		authors, total := ListAuthors(p, id)
		c.HTML(http.StatusOK, lang + "/authors.html", gin.H {
			//domain
			"Domain": "authors",
			//result-related
			"Authors": authors,
			"NoResult": len(*authors) == 0,
			//page-related
			"PageNotEnd": p * authorPageCount < total,
			"OffsetCount": (p - 1) * authorPageCount + 1,
			"EndCount": (p - 1) * authorPageCount + len(*authors),
			"TotalCount": total,
			"Page": p,
		})
	} else {
		sourcesMap := map[string]Tag{} //Source / Last Update Time Analysis
		var sources []Tag
		lastUpdateTime := ""
		for i := 0; i < len(author.Datapacks); i++ {
			sourcesMap[author.Datapacks[i].Source] = author.Datapacks[i].Tags[0]
			if author.Datapacks[i].UpdateTimeString > lastUpdateTime {
				lastUpdateTime = author.Datapacks[i].UpdateTimeString
			}
		}
		for _, tag := range sourcesMap {
			sources = append(sources, tag)
		}
		c.HTML(http.StatusOK, lang + "/author.html", gin.H {
			//domain
			"Domain": author.AuthorName,
			//result-related
			"Author": author,
			"TotalCount": len(author.Datapacks),
			"Sources": sources,
			"LastUpdateTime": lastUpdateTime,
		})
	}
}
func tagList(c *gin.Context) {
	page := c.Query("p")
	name := c.Query("tag")
	lang := c.Query("language")
	p, err := strconv.Atoi(page)
	if err != nil {
		p = 1
	}
	if lang == "" {
		lang = "default"
	}
	tags, total := ListTags(lang, p, name)
	// html render
	c.HTML(http.StatusOK, lang + "/tags.html", gin.H {
		//domain
		"Domain": "tags",
		//result-related
		"Tags": tags,
		"NoResult": len(*tags) == 0,
		//page-related
		"PageNotEnd": p * tagPageCount < total,
		"OffsetCount": (p - 1) * tagPageCount + 1,
		"EndCount": (p - 1) * tagPageCount + len(*tags),
		"TotalCount": total,
		"Page": p,
	})
}
func tag(c *gin.Context) {
	id := c.Param("id")
	page := c.Query("p")
	p, err := strconv.Atoi(page)
	if err != nil {
		p = 1
	}
	lang := c.Query("language")
	if lang == "" {
		lang = "default"
	}
	tag := GetTag(lang, id)
	// html render
	if tag == nil { // No Result
		tags, total := ListTags(lang, p, id)
		fmt.Println(tags, total)
	} else {
		fmt.Println(tag)
	}
}