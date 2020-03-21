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
	tagPageCount = 100
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
	KeyWordCount int `json:"-"`
}

type Tag struct {
	SearchResult
	ID string `json:"-" gorm:"primary_key:true"`
	Tag string `json:"tag_name"`
	DefaultLang string `json:"tag_language"`
	DefaultLangId string `json:"-"`
	DefaultTag string `json:"tag_default_name"`
	Type int `json:"tag_type"`
	Thumb int `json:"-"`
	Quotation int `json:"quotation"`
	Datapacks []Datapack `json:"datapacks" gorm:"many2many:datapack_tags;association_foreignkey:id;foreignkey:id;association_jointable_foreignkey:datapack_id;jointable_foreignkey:tag_id;"`
}
type Author struct {
	SearchResult
	ID string `json:"-" gorm:"primary_key:true"`
	AuthorUid string `json:"-"`
	AuthorName string `json:"author_name"`
	Avatar string `json:"author_avatar"`
	Thumb int `json:"-"`
	Datapacks []Datapack `json:"datapacks" gorm:"ForeignKey:AuthorID;AssociationForeignKey:ID"`
}
type Datapack struct {
	SearchResult
	ID string `json:"-" gorm:"primary_key:true"`
	Link string `json:"datapack_link"`
	Name string `json:"datapack_name"`
	Author Author `json:"author"`
	AuthorID string `json:"-"`
	DefaultLang string `json:"datapack_language"`
	DefaultLangId string `json:"-"`
	DefaultName string `json:"datapack_default_name"`
	Source string `json:"source"`
	Intro string `json:"introduction"`
	FullContent string `json:"-"`
	PostTime time.Time `json:"-"`
	PostTimeString string `json:"post_time"`
	UpdateTime time.Time `json:"-"`
	UpdateTimeString string `json:"update_time"`
	CoverExists bool `json:"-"`
	Thumb int `json:"-"`
	Tags []Tag `json:"tag" gorm:"many2many:datapack_tags;association_foreignkey:id;foreignkey:id;association_jointable_foreignkey:tag_id;jointable_foreignkey:datapack_id;"`
}

func (d *Datapack) Initialize() {
	d.PostTimeString = d.PostTime.Format("2006-01-02 15:04:05")
	d.UpdateTimeString = d.UpdateTime.Format("2006-01-02 15:04:05")
	d.Intro = "    " + strings.ReplaceAll(d.Intro, "\n", ".\n    ") + "."
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
func (d *Datapack) CountKeyWords(keywordsReg string) {
	d.Initialize()
	d.KeyWordCount += KeyWordHighlight(&d.Name, keywordsReg)
	d.KeyWordCount += KeyWordHighlight(&d.Intro, keywordsReg)
	for _, t := range d.Tags {
		if t.Type == 3 || t.Type == 4 {
			d.KeyWordCount += KeyWordHighlight(&t.Tag, keywordsReg)
		}
	}
}
func (d *Datapack) AccurateCountKeyWords(keywordsRegMatrix *[3]string) {
	d.Initialize()
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
func (t *Tag) CountKeyWords(keywordsReg string) {
	t.KeyWordCount += KeyWordHighlight(&t.Tag, keywordsReg)
}
func (a *Author) CountKeyWords(keywordsReg string) {
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
func datapackFilter(sql *gorm.DB, source string, version string, postTimeRange int, updateTimeRange int) *gorm.DB {
	if source != "" {
		sql = sql.Where("source = '" + source + "'")
	}
	if version != "" {
		sql = sql.Where("default_tags_str REGEXP '1:" + version + ",'")
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
	// Set language
	name, tag := "default_name", "default_tag"
	if language != "" && language != "default" {
		name, tag = "name_" + language, "tag_" + language
	}
	// Query
	total := 0
	sql = db.Model(&Datapack{}).
		Select("distinct datapacks.*, datapacks." + name + " as name"). // Set Datapack Name
		Preload("Tags", func(db *gorm.DB) *gorm.DB { // Preload Tags
			return db.Select("*, tags." + tag + " as tag").Order("tags.type") // Set Tag Name & Set Order
		}).
		Preload("Author") // Preload Author
	sql = datapackFilter(sql, source, version, postTimeRange, updateTimeRange) // Filter, Using Joined Table
	sql.Count(&total).Order(order).Offset(offset).Limit(limit).Find(&datapacks) // Count All & Only Find Datapack to be Shown
	// Initialize Datapacks
	for i := 0; i < len(datapacks); i++ {
		datapacks[i].Initialize()
	}
	return &datapacks, total
}
func GetDatapack(language string, id string) *Datapack {
	var datapacks []Datapack
	var sql = db
	// Set language
	name, tag := "default_name", "default_tag"
	if language != "" && language != "default" {
		name, tag = "name_" + language, "tag_" + language
	}
	sql.Model(&Datapack{}).
		Select("distinct datapacks.*, datapacks." + name + " as name"). // Set Datapack Name
		Preload("Tags", func(db *gorm.DB) *gorm.DB { // Preload Tags
			return db.Select("*, tags." + tag + " as tag").Order("tags.type") // Set Tag Name & Set Order
		}).
		Preload("Author"). // Preload Author
		Where("datapacks.id = '" + id + "'").First(&datapacks)
	if len(datapacks) > 0 {
		datapacks[0].Initialize()
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
	// Set language
	_tag := "default_tag"
	if language != "" && language != "default" {
		_tag = "tag_" + language
	}
	var sql = db.Select("distinct tags.*, tags." + _tag + " as tag").Order("tags.quotation DESC")
	// Return All
	if tag == "" {
		sql.Find(&tags)
	} else { // Find via Reg
		sql.Where("tags.tag REG '" + tag + "'").Find(&tags)
		keywordsReg, sqlReg := &tag, &tag
		if len(tags) == 0 {
			keywordsReg, sqlReg = SplitAllCharacters(tag)
			sql.Where(strings.ReplaceAll(*sqlReg, "$?", "tags." + _tag)).Find(&tags) // Find via Letters
		}
		for i := 0; i < len(tags); i++ { // Count and mark keywords
			tags[i].CountKeyWords(*keywordsReg)
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
	return &tags, total
}
func (t Tag) GetSynonymousTag(language string) *[]Tag {
	var tags []Tag
	// Set language
	_tag := "default_tag"
	if language != "" && language != "default" {
		_tag = "tag_" + language
	}
	db.Select("distinct tags.*, tags.default_tag as tag").
		Where("tags." + _tag + " = " + t.Tag).Not("tags.id = " + t.ID).Find(&tags)
	return &tags
}
func GetTag(language string, id string) *Tag {
	var tags []Tag
	var sql = db
	// Set language
	name, tag := "default_name", "default_tag"
	if language != "" && language != "default" {
		name, tag = "name_" + language, "tag_" + language
	}
	// Query
	sql.Model(&Tag{}).
		Select("distinct tags.*, tags.default_tag as tag"). // Set Tag Name As Default
		Preload("Datapacks", func(db *gorm.DB) *gorm.DB { // Preload Datapacks
			return db.Select("*, datapacks." + name + " as name").Order("datapacks.post_time DESC") // Set Datapack Name & Set Order
		}).
		Preload("Datapacks.Tags", func(db *gorm.DB) *gorm.DB { // Preload Datapacks.Tags
			return db.Select("*, tags." + tag + " as tag").Order("tags.type") // Set Tag Name & Set Order
		}).
		Where("tags.id = '" + id + "'"). // Find Tag Id
		First(&tags) // Find One
	if len(tags) > 0 {
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
	// Return All
	if author == "" {
		sql.Select("distinct authors.*").Find(&authors)
	} else { // Find via Reg
		sql.Where("authors.author_name REG '" + author + "'").Limit(1).Find(&authors)
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
	// Set language
	name, tag := "default_name", "default_tag"
	if language != "" && language != "default" {
		name, tag = "name_" + language, "tag_" + language
	}
	// Query
	sql.Preload("Datapacks", func(db *gorm.DB) *gorm.DB { // Preload Datapacks
			return db.Select("*, datapacks." + name + " as name").Order("datapacks.post_time DESC") // Set Datapack Name & Set Order
		}).
		Preload("Datapacks.Tags", func(db *gorm.DB) *gorm.DB { // Preload Datapacks.Tags
			return db.Select("*, tags." + tag + " as tag").Order("tags.type") // Set Tag Name & Set Order
		}).
		Where("authors.id = '" + id + "'"). // Find Tag Id
		First(&authors) // Find One
	if len(authors) > 0 {
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
	// Set language
	name, tag, tagStr := "default_name", "default_tag", "default_tags_str"
	if language != "" && language != "default" {
		name, tag, tagStr = "name_" + language, "tag_" + language, "tags_str_" + language
	}
	cols := []string{"datapacks." + name, "datapacks.intro", "datapacks." + tagStr}
	// Set SqlRegs Expression
	for _, v := range cols {
		regexps = append(regexps, strings.ReplaceAll(*sqlReg, "$?", v))
	}
	// Query
	sql = db.Model(&Datapack{}).
		Select("distinct datapacks.*, datapacks." + name + " as name"). // Set Datapack Name
		Preload("Tags", func(db *gorm.DB) *gorm.DB { // Preload Tags
			return db.Select("*, tags." + tag + " as tag").Order("tags.type") // Set Tag Name & Set Order
		}).
		Preload("Author"). // Preload Author
		Where(strings.Join(regexps, " OR ")) // Search
	sql = datapackFilter(sql, source, version, postTimeRange, updateTimeRange) // Filter, Using Joined Table
	sql.Find(&datapacks) // Find All
	total := len(datapacks)
	// Count and Mark Keywords
	for i := 0; i < len(datapacks); i++ {
		datapacks[i].CountKeyWords(*keywordsReg)
	}
	// Sort by Keywords Occur-Time And Slice
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
	// Set language
	_name, tag := "default_name", "default_tag"
	if language != "" && language != "default" {
		_name, tag = "name_" + language, "tag_" + language
	}
	// Query
	sql = db.Model(&Datapack{}).
		Select("distinct datapacks.*, datapacks." + _name + " as name"). // Set Datapack Name
		Preload("Tags", func(db *gorm.DB) *gorm.DB { // Preload Tags
			return db.Select("*, tags." + tag + " as tag").Order("tags.type") // Set Tag Name & Set Order
		}).
		Preload("Author"). // Preload Authors
		Joins("JOIN authors ON datapacks.author_id = authors.id")
	// Query Name
	if name != "" {
		keywordsReg, sqlReg := LettersIn(name)
		keywordsMatrix[0] = *keywordsReg
		sql = sql.Where(strings.ReplaceAll(*sqlReg, "$?", "datapacks." + _name))
	}
	// Query Intro
	if intro != "" {
		keywordsReg, sqlReg := LettersIn(intro)
		keywordsMatrix[1] = *keywordsReg
		sql = sql.Where(strings.ReplaceAll(*sqlReg, "$?", "datapacks.intro"))
	}
	// Query Author
	if author != "" {
		keywordsReg, sqlReg := LettersIn(author)
		keywordsMatrix[2] = *keywordsReg
		sql = sql.Where(strings.ReplaceAll(*sqlReg, "$?", "authors.author_name"))
	}
	sql = datapackFilter(sql, source, version, postTimeRange, updateTimeRange) // Filter, Using Joined Table
	sql.Find(&datapacks) // Find All
	total := len(datapacks)
	// Count and Mark Keywords
	for i := 0; i < len(datapacks); i++ {
		datapacks[i].AccurateCountKeyWords(&keywordsMatrix)
	}
	// Sort by Keywords Occur-Time And Slice
	datapacksSortTrim(&datapacks, offset, limit)
	return &datapacks, total
}
// Rand
func GetRandID(table string) string {
	var id []string
	err := db.Raw("select id from " + table + " order by rand() limit 1;").Pluck("id", &id).Error
	if err != nil {
		panic(err)
	}
	if len(id) == 0 {
		panic("result empty.")
	}
	return id[0]
}
func GetRandDatapack(language string) *Datapack {
	return GetDatapack(language, GetRandID("datapacks"))
}
func GetRandAuthor(language string) *Author {
	return GetAuthor(language, GetRandID("authors"))
}
func GetRandTag(language string) *Tag {
	return GetTag(language, GetRandID("tags"))
}