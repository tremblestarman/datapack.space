package main

import (
	"html/template"
	"net/http"

	"github.com/gin-gonic/gin"
)

func SetCookie() gin.HandlerFunc {
	return func(c *gin.Context) {
		cookie, e := c.Request.Cookie("style")
		if e == nil { // Refresh Cookie
			c.SetCookie(cookie.Name, cookie.Value, 604800, cookie.Path, cookie.Domain, cookie.Secure, cookie.HttpOnly)
		} else { // Set New Cookie
			c.SetCookie("style", "normal", 604800, "/", "localhost", false, true)
		}
		c.Next()
	}
}
func Cors() gin.HandlerFunc {
	return func(c *gin.Context) {
		method := c.Request.Method
		path := c.FullPath()
		if len(path) >= 11 && path[:11] == "/bin/stats/" { // allow cors
			c.Header("Access-Control-Allow-Origin", "*")
			c.Header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
			c.Header("Access-Control-Allow-Headers", "Origin, X-Requested-With, Content-Type, Accept, Authorization")
			c.Header("Access-Control-Expose-Headers", "Content-Length, Access-Control-Allow-Origin, Access-Control-Allow-Headers, Cache-Control, Content-Language, Content-Type")
			c.Header("Access-Control-Allow-Credentials", "true")
		}
		if method == "OPTIONS" {
			c.AbortWithStatus(http.StatusNoContent)
		}
		c.Next()
	}
}
func main() {
	//connect to database
	Connect()
	defer db.Close()   //close database
	_ = seg.LoadDict() //load dict
	r := gin.Default()
	r.Use(SetCookie())
	r.Use(Cors())
	r.SetFuncMap(template.FuncMap{
		"unescaped": unescaped,
	})
	// Load Resources
	r.Static("/bin", "./bin")
	r.StaticFile("/favicon.ico", "./bin/icon/datapackspace.ico")
	r.StaticFile("/sitemap.xml", "./bin/sitemap.xml")
	r.StaticFile("/robots.txt", "./bin/robots.txt")
	r.LoadHTMLGlob("templates/**/*")
	// Router
	r.GET("/", index)
	r.GET("/datapack/:id", datapack)
	r.GET("/random/datapack", datapackRand)
	r.GET("/search", search)
	r.GET("/author", authorList)
	r.GET("/author/:id", author)
	r.GET("/random/author", authorRand)
	r.GET("/tag", tagList)
	r.GET("/tag/:id", tag)
	r.GET("/random/tag", tagRand)
	r.GET("/language", language)
	r.GET("/guide", guide)
	r.GET("/about", about)
	r.POST("/thumb", thumbByID)
	_ = r.Run(":4080")
}
