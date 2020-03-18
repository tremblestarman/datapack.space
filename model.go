package main

import (
	"encoding/json"
	"fmt"
	"github.com/go-ego/gse"
	"github.com/jinzhu/gorm"
	_ "github.com/jinzhu/gorm/dialects/mysql"
	"io/ioutil"
	"os"
	"regexp"
	"sort"
	"strconv"
	"strings"
	"time"
)

var db *gorm.DB
var seg gse.Segmenter

const (
	orderByPostTime = "post_time"
	orderByPostTimeDesc = "post_time desc"
	orderByUpdateTime = "update_time"
	orderByUpdateTimeDesc = "update_time desc"
	datapackPageCount = 15
	tagPageCount = 50
	authorPageCount = 24
	keyWordHighlightHead = "<span class=\"highlight\">"
	keyWordHighlightTail = "</span>"
)

func PathExists(path string) (bool, error) {
	_, err := os.Stat(path)
	if err == nil {
		return true, nil
	}
	if os.IsNotExist(err) {
		return false, nil
	}
	return false, err
}

type Auth struct {
	Host string `json:"host"`
	Port int `json:"port"`
	User string `json:"user"`
	Password string `json:"password"`
}
type SearchResult struct {
	KeyWordCount int
}

type Tag struct {
	SearchResult
	ID string `gorm:"primary_key:true"`
	Tag string
	DefaultLang string
	DefaultTag string
	Type int
	Thumb int
	Datapacks []Datapack `gorm:"many2many:datapack_tags"`
}
type Author struct {
	SearchResult
	ID string `gorm:"primary_key:true"`
	AuthorUid string
	AuthorName string
	Avatar string
	Thumb int
	Datapacks []Datapack `gorm:"ForeignKey:AuthorID;AssociationForeignKey:ID"`
}
type Datapack struct {
	SearchResult
	ID string `gorm:"primary_key:true"`
	Link string
	Name string
	Author Author
	AuthorID string
	DefaultLang string
	DefaultName string
	Source string
	Intro string
	FullContent string
	PostTime time.Time
	PostTimeString string
	UpdateTime time.Time
	UpdateTimeString string
	CoverExists bool
	Thumb int
	Tags []Tag `gorm:"many2many:datapack_tags"`
}

func (t *Tag) Relate(language string) {
	db.Model(&t).Related(&t.Datapacks, "Datapacks")
	tag := "default_tag"
	if language != "" && language != "default" {
		tag = "tag_" + language
	}
	db.Raw("SELECT tags." + tag + " as tag FROM tags WHERE id = ?", t.ID).Scan(&t)
}
func (a *Author) Relate() {
	db.Model(&a).Related(&a.Datapacks)
}
func (d *Datapack) Relate(language string) {
	db.Model(&d).Related(&d.Author)
	db.Model(&d).Related(&d.Tags, "Tags")
	sort.Slice(d.Tags, func(i, j int) bool { // Sort
		return d.Tags[i].Type < d.Tags[j].Type
	})
	for i := 0; i < len(d.Tags); i++ {
		d.Tags[i].Relate(language)
	}
	d.PostTimeString = d.PostTime.Format("2006-01-02 15:04:05")
	d.UpdateTimeString = d.UpdateTime.Format("2006-01-02 15:04:05")
	d.Intro = "    " + strings.ReplaceAll(d.Intro, "\n", ".\n    ") + "."
	//Set Name
	name := "default_name"
	if language != "" && language != "default" {
		name = "name_" + language
	}
	db.Raw("SELECT datapacks." + name + " as name FROM datapacks WHERE id = ?", d.ID).Scan(&d)
	d.CoverExists, _ = PathExists("bin/img/cover/" + d.ID + ".png")
}

func KeyWordHighlight(raw *string, keywordsReg string) int {
	l, q := len(*raw), len(keyWordHighlightHead + keyWordHighlightTail)
	re := regexp.MustCompile("(?i)" + keywordsReg)
	*raw = re.ReplaceAllStringFunc(*raw, func (s string) string {
		return keyWordHighlightHead + strings.ToUpper(s) + keyWordHighlightTail
	})
	return (len(*raw) - l) / q
}
func (d *Datapack) CountKeyWords(language string, keywordsReg string) {
	d.Relate(language)
	d.KeyWordCount += KeyWordHighlight(&d.Name, keywordsReg)
	d.KeyWordCount += KeyWordHighlight(&d.Intro, keywordsReg)
	for _, t := range d.Tags {
		if t.Type == 3 || t.Type == 4 {
			d.KeyWordCount += KeyWordHighlight(&t.Tag, keywordsReg)
		}
	}
}
func (d *Datapack) AccurateCountKeyWords(language string, keywordsRegMatrix *[3]string) {
	d.Relate(language)
	if (*keywordsRegMatrix)[0] != "" {
		d.KeyWordCount += KeyWordHighlight(&d.Name, (*keywordsRegMatrix)[0])
	}
	if (*keywordsRegMatrix)[1] != "" {
		d.KeyWordCount += KeyWordHighlight(&d.Intro, (*keywordsRegMatrix)[1])
	}
	if (*keywordsRegMatrix)[2] != "" {
		d.KeyWordCount += KeyWordHighlight(&d.Author.AuthorName, (*keywordsRegMatrix)[2])
	}
}
func (t *Tag) CountKeyWords(language string, keywordsReg string) {
	t.Relate(language)
	t.KeyWordCount += KeyWordHighlight(&t.Tag, keywordsReg)
}
func (a *Author) CountKeyWords(keywordsReg string) {
	a.Relate()
	a.KeyWordCount += KeyWordHighlight(&a.AuthorName, keywordsReg)
}

// Connect
func Connect() {
	var auth Auth
	jstring, err := ioutil.ReadFile("util/auth.json")
	if err != nil {
		panic(err)
	}
	err = json.Unmarshal(jstring, &auth)
	if err != nil {
		panic(err)
	}
	dsn := auth.User + ":" + auth.Password + "@tcp(" + auth.Host + ":" + strconv.Itoa(auth.Port) + ")/datapack_collection?charset=UTF8MB4&parseTime=True&loc=Local"
	fmt.Println(dsn + " connecting..")
	db, err = gorm.Open("mysql", dsn)
	if err != nil {
		fmt.Println(err)
	}
}
// List
func datapackFilter(sql *gorm.DB, source string, version string, postTimeRange int, updateTimeRange int) *gorm.DB {
	if source != "" {
		sql = sql.Where("source = '" + source + "'")
	}
	if version != "" {
		sql = sql.Where("t.type = 1 AND t.tag = '" + version + "'")
	}
	if postTimeRange != 0 {
		sql = dateRange(sql, postTimeRange, "datapacks.post_time")
	}
	if updateTimeRange != 0 {
		sql = dateRange(sql, updateTimeRange, "datapacks.update_time")
	}
	return sql
}
func ListDatapacks(language string, page int, order string, source string, version string, postTimeRange int, updateTimeRange int) (*[]Datapack, int) {
	var datapacks []Datapack
	if page < 1 {
		page = 1
	}
	var offset, limit = (page - 1) * datapackPageCount, datapackPageCount
	var sql = db
	sql = sql.Select("distinct datapacks.*").Order(order).Joins("JOIN datapack_tags AS dt ON datapacks.id = dt.datapack_id JOIN tags AS t ON dt.tag_id = t.id")
	sql = datapackFilter(sql, source, version, postTimeRange, updateTimeRange)
	sql.Find(&datapacks)
	total := len(datapacks)
	if offset >= len(datapacks) {
		datapacks = make([]Datapack, 0)
	} else if offset + limit > len(datapacks) { // Slice
		datapacks = append((datapacks)[offset :])
	} else {
		datapacks = append((datapacks)[offset : offset + limit])
	}
	for i := 0; i < len(datapacks); i++ {
		datapacks[i].Relate(language)
	}
	return &datapacks, total
}
func GetDatapack(language string, id string) *Datapack {
	var datapacks []Datapack
	var sql = db
	sql.Where("datapacks.id = '" + id + "'").Limit(1).Find(&datapacks)
	if len(datapacks) > 0 {
		datapacks[0].Relate(language)
		return &(datapacks[0])
	}
	return nil
}
func RemoveDuplicates(a []string) (ret []string){
	sort.Strings(a)
	aLen := len(a)
	for i:=0; i < aLen; i++{
		if (i > 0 && a[i-1] == a[i]) || len(a[i]) == 0 || a[i] == " " || a[i] == "," || a[i] == "，"{
			continue
		}
		ret = append(ret, a[i])
	}
	return
}
func SplitAllCharacters(content string) (*string, *string) {
	chars := []rune(content)
	var keywords []string
	for _, c := range chars {
		keywords = append(keywords, string(c))
	}
	keywords = RemoveDuplicates(keywords)
	keywordsReg := strings.Join(keywords, "|")
	sqlReg := "($? REGEXP '" + strings.Join(keywords, "' AND $? REGEXP '") + "')"
	return &keywordsReg, &sqlReg
}
func ListTags(language string, page int, tag string) (*[]Tag, int) {
	var tags []Tag
	if page < 1 {
		page = 1
	}
	var offset, limit = (page - 1) * tagPageCount,tagPageCount
	var sql = db
	if tag == "" { // Return All
		sql.Select("distinct tags.*").Find(&tags)
	} else {
		sql.Where("tags.tag REG '" + tag + "'").Find(&tags) // Find via Reg
		keywordsReg, sqlReg := &tag, &tag
		if len(tags) == 0 {
			keywordsReg, sqlReg = SplitAllCharacters(tag)
			sql.Where(strings.ReplaceAll(*sqlReg, "$?", "tags.tag")).Find(&tags) // Find via Letters
		}
		for i := 0; i < len(tags); i++ { // Count and mark keywords
			tags[i].CountKeyWords(language, *keywordsReg)
		}
		sort.Slice(tags, func(i, j int) bool { // Sort
			if tags[j].KeyWordCount == tags[i].KeyWordCount {
				return len(tags[i].Tag) < len(tags[j].Tag)
			}
			return tags[j].KeyWordCount < tags[i].KeyWordCount
		})
	}
	total := len(tags)
	if offset >= len(tags) {
		tags = make([]Tag, 0)
	} else if offset + limit > len(tags) { // Slice
		tags = append(tags[offset :])
	} else {
		tags = append(tags[offset : offset + limit])
	}
	for i := 0; i < len(tags); i++ {
		tags[i].Relate(language)
	}
	return &tags, total
}
func GetTag(language string, id string) *Tag {
	var tags []Tag
	var sql = db
	sql.Where("tags.id = '" + id + "'").Limit(1).Find(&tags)
	if len(tags) > 0 {
		tags[0].Relate(language)
		for i := 0; i < len(tags[0].Datapacks); i++ {
			tags[0].Datapacks[i].Relate(language)
		}
		return &(tags[0])
	}
	return nil
}
func ListAuthors(page int, author string) (*[]Author, int) {
	var authors []Author
	if page < 1 {
		page = 1
	}
	var offset, limit = (page - 1) * authorPageCount, authorPageCount
	var sql = db
	if author == "" { // Return All
		sql.Select("distinct authors.*").Find(&authors)
	} else {
		sql.Where("authors.author_name REG '" + author + "'").Limit(1).Find(&authors) // Find via Reg
		keywordsReg, sqlReg := &author, &author
		if len(authors) == 0 { // No Result
			keywordsReg, sqlReg = SplitAllCharacters(author)
			sql.Where(strings.ReplaceAll(*sqlReg, "$?", "authors.author_name")).Find(&authors) // Find via Letters
		}
		for i := 0; i < len(authors); i++ { // Count and mark keywords
			authors[i].CountKeyWords(*keywordsReg)
		}
		sort.Slice(authors, func(i, j int) bool { // Sort
			if authors[j].KeyWordCount == authors[i].KeyWordCount {
				return len(authors[i].AuthorName) < len(authors[j].AuthorName)
			}
			return authors[j].KeyWordCount < authors[i].KeyWordCount
		})
	}
	total := len(authors)
	if offset >= len(authors) {
		authors = make([]Author, 0)
    } else if offset + limit > len(authors) { // Slice
		authors = append(authors[offset :])
	} else {
		authors = append(authors[offset : offset + limit])
	}
	return &authors, total
}
func GetAuthor(language string, id string) *Author {
	var authors []Author
	var sql = db
	sql.Where("authors.id = '" + id + "'").Limit(1).Find(&authors)
	if len(authors) > 0 {
		authors[0].Relate()
		for i := 0; i < len(authors[0].Datapacks); i++ {
			authors[0].Datapacks[i].Relate(language)
		}
		return &(authors[0])
	}
	return nil
}
// Search
func WordsIntersect(text string) (*string, *string) {
	hmm := seg.CutSearch(text, true)
	var words []string
	words = RemoveDuplicates(hmm)
	keywordsReg := strings.Join(words, "|")
	sqlReg := "$? REGEXP '" + keywordsReg + "'"
	return &keywordsReg, &sqlReg
}
func LettersIn(text string) (*string, *string) {
	hmm := seg.CutSearch(text, true)
	var words []string
	words = RemoveDuplicates(hmm)
	keywordsReg := strings.Join(words, "|")
	sqlReg := "($? REGEXP '" + strings.Join(words, "' AND $? REGEXP '") + "')"
	return &keywordsReg, &sqlReg
}
func dateRange(sql *gorm.DB, dateRange int, col string) *gorm.DB {
	switch dateRange {
	case 1: // Today
		sql = sql.Where("TO_DAYS(" + col + ") = TO_DAYS(NOW())")
	case 2: // 3 Days
		sql = sql.Where("TO_DAYS(NOW()) - TO_DAYS(" + col + ") <= 3")
	case 3: // 7 Days
		sql = sql.Where("DATE_SUB(CURDATE(), INTERVAL 7 DAY) <= date(" + col + ")")
	case 4: // 1 Month
		sql = sql.Where("DATE_SUB(CURDATE(), INTERVAL 30 DAY) <= date(" + col + ")")
	case 5: // this Month
		sql = sql.Where("DATE_FORMAT(" + col + ", '%Y%m') = DATE_FORMAT(CURDATE(), '%Y%m')")
	case 6: // this Year
		sql = sql.Where("YEAR(" + col + ")=YEAR(NOW())")
	}
	return sql
}
func datapacksSortTrim(datapacks *[]Datapack, offset int, limit int) {
	sort.Slice(*datapacks, func(i, j int) bool { // Sort
		return (*datapacks)[j].KeyWordCount < (*datapacks)[i].KeyWordCount
	})
	if offset >= len(*datapacks) {
		*datapacks = make([]Datapack, 0)
	} else if offset + limit > len(*datapacks) { // Slice
		*datapacks = append((*datapacks)[offset :])
	} else {
		*datapacks = append((*datapacks)[offset : offset + limit])
	}
}
func SearchDatapacks(language string, page int, content string, source string, version string, postTimeRange int, updateTimeRange int) (*[]Datapack, int) {
	if page < 1 {
		page = 1
	}
	var datapacks []Datapack
	// search via datapacks.name or datapacks.name_zh or datapacks.content or t.tag (type = 3 or 4
	var sql = db
	var offset, limit = (page - 1) * datapackPageCount, datapackPageCount
	keywordsReg, sqlReg := WordsIntersect(content)
	var regexps []string
	name := "default_name"
	if language != "" && language != "default" {
		name = "name_" + language
	}
	tag := "default_tag"
	if language != "" && language != "default" {
		tag = "tag_" + language
	}
	cols := []string{"datapacks." + name, "datapacks.intro", "t." + tag}
	for _, v := range cols {
		regexps = append(regexps, strings.ReplaceAll(*sqlReg, "$?", v))
	}
	sql = sql.Select("distinct datapacks.*").Joins("JOIN authors AS a ON datapacks.author_id = a.id JOIN datapack_tags AS dt ON datapacks.id = dt.datapack_id JOIN tags AS t ON dt.tag_id = t.id").Where(strings.Join(regexps, " OR ") + " AND (t.type = 1 OR t.type = 3 OR t.type = 4)")
	sql = datapackFilter(sql, source, version, postTimeRange, updateTimeRange)
	sql.Find(&datapacks)
	for i := 0; i < len(datapacks); i++ { // Count and mark keywords
		datapacks[i].CountKeyWords(language, *keywordsReg)
	}
	total := len(datapacks)
	datapacksSortTrim(&datapacks, offset, limit)
	return &datapacks, total
}
func AccurateSearchDatapacks(language string, page int, name string, intro string, author string, source string, version string, postTimeRange int, updateTimeRange int) (*[]Datapack, int) {
	if page < 1 {
		page = 1
	}
	var datapacks []Datapack
	// search via datapacks.name or name_zh and datapacks.intro and authors.author_name and date
	var sql = db
	var offset, limit = (page - 1) * datapackPageCount, datapackPageCount
	var keywordsMatrix [3]string
	sql = sql.Select("distinct datapacks.*").Joins("JOIN authors AS a ON datapacks.author_id = a.id JOIN datapack_tags AS dt ON datapacks.id = dt.datapack_id JOIN tags AS t ON dt.tag_id = t.id")
	if name != "" {
		keywordsReg, sqlReg := LettersIn(name)
		keywordsMatrix[0] = *keywordsReg
		name := "default_name"
		if language != "" && language != "default"{
			name = "name_" + language
		}
		sql = sql.Where(strings.ReplaceAll(*sqlReg, "$?", "datapacks." + name))
	}
	if intro != "" {
		keywordsReg, sqlReg := LettersIn(intro)
		keywordsMatrix[1] = *keywordsReg
		sql = sql.Where(strings.ReplaceAll(*sqlReg, "$?", "datapacks.intro"))
	}
	if author != "" {
		keywordsReg, sqlReg := LettersIn(author)
		keywordsMatrix[2] = *keywordsReg
		sql = sql.Where(strings.ReplaceAll(*sqlReg, "$?", "a.author_name"))
	}
	sql = datapackFilter(sql, source, version, postTimeRange, updateTimeRange)
	sql.Find(&datapacks)
	for i := 0; i < len(datapacks); i++ { // Count and mark keywords
		datapacks[i].AccurateCountKeyWords(language, &keywordsMatrix)
	}
	total := len(datapacks)
	datapacksSortTrim(&datapacks, offset, limit)
	return &datapacks, total
}