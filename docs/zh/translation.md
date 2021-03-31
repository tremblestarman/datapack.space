如果想要翻译开发文档，只需遵照目录格式翻译`/docs`下的内容，本文不会详述。

# 翻译

> 翻译对象为`/templates`下的静态资源，即网站提示模板。

如果想要创建新的语言、翻译未被翻译的网站提示，或者进一步优化已翻译的内容，建议您阅读以下内容。

## 模板结构

|子文件夹名|描述|
|:-:|:-:|
|default|默认语言下的模板(默认中文)|
|generic|不涉及文本的通用模板|
|\[ language \]|某语言下的模板|

## 创建/更新新的语言

- ### 手动

    1. 更新`languages.json`

        打开`/util/languages.json`，向json对象中添加一个新的语言对象。语言对象的格式如下：

        ```json
        "[lang-id]":{"name":"[lang-name]"}

        eg:
        "en":{"name":"English"}
        ```

        - lang-id

            必须与谷歌翻译中的语言id匹配，否则无法自动对该语言下的数据包内容进行机器翻译。

        - lang-name

            在网站语言切换界面显示的语言全称。

    2. 复制模板

        在`/templates`下复制`/templates/default`，更名为`/templates/[lang-id]`，这里`lang-id`必须与`languages.json`中的匹配。

- ### 自动

    1. 编译

        ```shell
        cd admin
        go build language.go 
        ```

        得到的language二进制文件即自动化维护语言的脚本程序。

    2. 参数

        |参数|描述|
        |:-|:-|
        |-h|帮助|
        |-c|创建新语言|
        |-r|重置某语言|
        |-u|更新某语言|
        |-d|删除某语言|
        |-a|目标为所有语言|
        |-id=|目标为某id的语言；或定义id|
        |-name=|目标为某名称的语言；或定义语言名|

    3. 例子

        - 创建简体中文
            ```shell
            ./language -c -id="zh-CN" -name="简体中文"
            ```
        - 更新全部语言
            ```
            ./language -u -a
            ```
        - 删除id为xxx的语言
            ```shell
            ./language -d -id=xxx
            ```

## 翻译

打开`/templates/[lang-id]/translation.tmpl`，然后翻译其中的文本。

如：

```js
{{define "default/about_msg"}}关于{{end}}
--->
{{define "default/about_msg"}}About{{end}}
```