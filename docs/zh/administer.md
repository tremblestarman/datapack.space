# 管理

----

## 纠错

> 不要使用Issue来提交纠错

机器翻译难免会出现错误，且错误比较多。如果存在严重的错误，请在[反馈贴](https://www.mcbbs.net/thread-1178642-1-1.html)中告知我。

----

## 合并

网站的运作逻辑是将不同来源的作者视为不同作者、不同来源的数据包视为不同数据包。如果想关联您在不同网站发布的数据包，或者直接关联您在不同网站的账户，请在[反馈贴](https://www.mcbbs.net/thread-1178642-1-1.html)中告知我。

----

## 授权

本网站的定位是一个导航站，而不是绕过作者盗取未经授权的数字资源。网站采取了一个十分安全可靠的策略来维护作者的权益：默认只提供图片与文字信息，视频、可交互内容、链接等均被屏蔽。

如果您想在本站开放您的数据包，即授权本站提供包括下载链接在内的一切内容，请在[反馈贴](https://www.mcbbs.net/thread-1178642-1-1.html)中告知我。

----

## 添加网站来源

> 这是一个技术性内容，请确保您对html、爬虫有基本了解。

网站的爬虫逻辑被存放在`/util/schema`下的json文件中，以对象的方式定义了爬虫该如何浏览、抓取、分析、提炼网站内容。

- ### 爬虫对象

    |属性名|描述|
    |:-|:-|
    |domain|网站的域，如: "https://www.mcbbs.net/"。|
    |id|网站id，如: "mcbbs"。|
    |name|网站全称，如: "Minecraft中文论坛"。|
    |lang|网站默认语言名称，与`language.json`匹配。它规定了机器翻译的源语言。|
    |scan|列表扫描。|
    |post_path|定义数据包路径的捕获规则。|
    |post_type|定义`post_path`捕获结果的类型。|
    |info_collect|定义各种信息的捕获规则。|
    |info_refine|信息的修饰与提炼。|
    |info_adapt|信息的改写。|

    - 捕获规则

        1. DOM对象形式

            若值为对象，则使用如下所示的选择器。
            ```json
            "div": {
                "class": "test",
                "a": {
                    "href": "__xxx___"
                }
            }
            ```

            形如上述形式的json，即将DOM对象以json对象形式表示。最后捕获的信息以双'_'开头。例子中捕获的结果即：第一个类为"test"的"div"元素下第一个"a"元素的"href"值。

            - 多选一

                只填写元素名将默认选择第一个元素。你可以通过以下格式选择其他元素。
                ```json
                "div.0", "div.1", ...
                ```
                匹配第一个、第二个、...的"div"元素。"div"等价于"div.0"。

            - 多选多

                你可以通过以下格式选择所有元素。
                ```json
                "div.", "a.", "li."
                ```
                匹配结果为一个列表。如果匹配结果中出现列表嵌套，爬虫将对嵌套列表进行展开处理，使其最终为一维。
        2. XPATH

            若值为字符串，则使用XPATH选择器。详见XPATH文档。

    - 列表扫描过程

        - `scan`的属性

            |属性名|描述|
            |:-|:-|
            |type|"normal"则是requests爬取，"selenium"则是selenium爬取。|
            |entrance|列表入口链接。|
            |page_start|替换入口链接中的"$p"参数，定义入口页数。|
            |display|仅当type="selenium"才设置。"headless"以无头打开浏览器；"virtual"以虚拟显示方式打开浏览器；"window"以图形化界面方式打开浏览器。建议"virtual"。|

        - 爬取过程
            
            爬虫从入口进入，按照`scan`中定义的方式获取完整的html。然后按照`post_path`中的捕获规则捕获信息。接着"\$p=\$p+1"进入下一个页面。不断重复直到没有新的信息被捕获。

            `post_type`表示`post_path`捕获结果的类型。如果值为"url"，则表明捕获到的信息是数据包的地址链接，爬虫接下来会访问该链接进而爬取数据包的详细信息；如果值为"content"，则表明捕获到的信息就是数据包的全部信息，爬虫接下来直接根据该内容爬取数据包的详细信息。

    - 捕获数据包的详细信息

        - `info_collect`的属性

            |属性名|描述|
            |:-|:-|
            |name|默认名称。|
            |name_\[ lang-id \]|在某语言下的名称，可选。若为空则会被机器翻译填充。|
            |author_uid|作者的uid。|
            |author_name|作者的名字。|
            |author_avatar|作者的头像。|
            |version|数据包的版本。|
            |game_version|数据包支持的游戏版本。|
            |tag|数据包的自带标签。|
            |content_raw|数据包介绍，无屏蔽。|
            |content_filtered|数据包介绍，有屏蔽。默认"auto"，根据`content_raw`自动屏蔽。|
            |cover_img|数据包的封面图片。|
            |post_time|发布时间。|
            |update_time|更新时间。|

        - 爬取过程

            根据捕获规则直接捕获信息，最终结果的类型为字符串或列表。如果捕获的DOM对象，则会先强行转化为字符串。

    - 信息修饰与提炼

        其属性同`info_collect`，与之一一对应。（可省略）

        - 操作

            1. remove

                - 如果值为字符串，则从捕获信息中移除该字符串。
                - 如果值为对象，则先将捕获信息转化为DOM对象，再移除值所对应的对象。

            2. replace

                - from：源字符串，可以是正则表达式。
                - to：结果字符串，可以使用'$'匹配捕获组。

            3. regex

                - from：匹配字符串，可以是正则表达式。
                - to：模式字符串，可以使用'$'匹配捕获组，也可以用'%s'匹配。

                与replace区别在于，regex将所有模式化的结果记录在一个数组中。

    - 信息的改写

        其属性同`info_collect`，与之一一对应。（可省略）
        
        值为一段Python代码，爬虫最后将执行该段代码。代码中将捕获与属性同名的局部变量。

    - 最终数据类型

        在前面的过程中，信息的中间类型可以是字符串或列表，但其最终类型必须如下表，否则将以None替代。

        |信息|最终类型|
        |:-|:-|
        |name|str|
        |name_\[ lang-id \]|str|
        |author_uid|str|
        |author_name|str|
        |author_avatar|str|
        |version|str|
        |game_version|list|
        |tag|list|
        |content_raw|str|
        |content_filtered|str|
        |cover_img|str|
        |post_time|str|
        |update_time|str|