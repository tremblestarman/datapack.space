function jump(href, target) {
    if (!target) {
        location.href = href;
    } else {
        window.open(href, target);
    }
}
function jump_datapack(id) {
    location.href = window.location.protocol + "//" + window.location.host + "/datapack/" + id;
}
function jump_tag(id) {
    location.href = window.location.protocol + "//" + window.location.host + "/tag/" + id;
}
function jump_author(id) {
    location.href = window.location.protocol + "//" + window.location.host + "/author/" + id;
}

function load() {
    loaded();
    if (typeof load_extra == "function")
        load_extra();
    setTimeout(function(){
        page_rotate_back();
    },500);
}
function loading() {
    var load = document.getElementById("loading");
    load.classList.add("show");
}
function loaded() {
    var load = document.getElementById("loading");
    load.classList.add("hide");
}

var timer = null;
function back_to_top() {
    cancelAnimationFrame(timer);
    timer = requestAnimationFrame(function fn(){
        var oTop = document.body.scrollTop || document.documentElement.scrollTop;
        if(oTop > 0){
            document.body.scrollTop = document.documentElement.scrollTop = oTop - 50;
            timer = requestAnimationFrame(fn);
        } else {
            cancelAnimationFrame(timer);
        }
    });
}

function navigation(goal) {
    target = event.currentTarget;
    if (goal == "more") {
        if (target.parentNode.classList.contains("sub")) { // fold it
            target.classList.remove("sub");
            target.parentNode.classList.remove("sub");
            target.classList.remove("sub");
        } else { // unfold it
            target.classList.add("sub");
            target.parentNode.classList.add("sub");
            target.classList.add("sub");
        }
    } else {
        if (goal == 'datapack') goal = '';
        location.href = window.location.protocol + "//" + window.location.host + "/" + goal;
    }
}

function option_datapacks_default() {
    let normal_search = document.getElementById("normal-search"),
        datapack_name = document.getElementById("datapack-name"),
        datapack_author = document.getElementById("datapack-author"),
        datapack_intro = document.getElementById("datapack-intro");
    if (normal_search != null && GetQueryStringDecode("search") != null) {
        normal_search.value = GetQueryStringDecode("search");
    }
    let acc= false;
    if (datapack_name != null && GetQueryStringDecode("name") != null) {
        acc = true;
        datapack_name.value = GetQueryStringDecode("name");
    }
    if (datapack_author != null && GetQueryStringDecode("author") != null) {
        acc = true;
        datapack_author.value = GetQueryStringDecode("author");
    }
    if (datapack_intro != null && GetQueryStringDecode("intro") != null) {
        acc = true;
        datapack_intro.value = GetQueryStringDecode("intro");
    }
    if (acc) accurate();
}
function search_datapacks_keyboard() {
    if(event.keyCode != "13") {
        return;
    }
    search_datapacks();
}
function search_datapacks() {
    let normal_search = document.getElementById("normal-search"),
        datapack_name = document.getElementById("datapack-name").value,
        datapack_author = document.getElementById("datapack-author").value,
        datapack_intro = document.getElementById("datapack-intro").value,
        order = document.getElementById("order").selectedIndex,
        source_el = document.getElementById("filter-source"),
        version_el = document.getElementById("filter-version"),
        source = source_el.options[source_el.selectedIndex].text,
        version = version_el.options[version_el.selectedIndex].text,
        post_time = document.getElementById("filter-post-time").selectedIndex,
        update_time = document.getElementById("filter-update-time").selectedIndex;
    page_rotate(90);
    setTimeout(function(){
        loading();
    },500);
    let params = getQueryObject(), search = false;
    delete params['p'];
    if (order > 0) params["order"] = order; else delete params['order'];
    if (source_el.selectedIndex > 0) params["source"] = source; else delete params['source'];
    if (version_el.selectedIndex > 0) params["version"] = version; else delete params['version'];
    if (post_time > 0) params["p_time"] = post_time; else delete params['p_time'];
    if (update_time > 0) params["u_time"] = update_time; else delete params['u_time'];
    if (normal_search.value !== '' && !normal_search.classList.contains('hide')) { //Search
        delete params['name'];
        delete params['author'];
        delete params['intro'];
        search = true;
        params["search"] = normal_search.value;
    } else if ((datapack_name !== '' || datapack_author !== '' || datapack_intro !== '') && normal_search.classList.contains('hide')) {// Accurate Search
        delete params['search'];
        search = true;
        if (datapack_name !== '') params["name"] = datapack_name;
        if (datapack_author !== '') params["author"] = datapack_author;
        if (datapack_intro !== '') params["intro"] = datapack_intro;
    }
    setTimeout(function(){
        let p = [];
        for (var key in params) {
            p.push(key + "=" + params[key]);
        }
        nUrl = ((p.length > 0) ? "?" : "") + p.join("&");
        if (search) {
            nUrl = "search/" + nUrl;
        }
        nUrl = window.location.protocol + "//" + window.location.host + "/" + nUrl;
        this.location = nUrl;
        window.location.href = nUrl;
    },500);
}
function option_authors_default() {
    let normal_search = document.getElementById("normal-search");
    if (normal_search != null && GetQueryStringDecode("author") != null) {
        normal_search.value = GetQueryStringDecode("author");
    }
}
function search_authors_keyboard() {
    if(event.keyCode != "13") {
        return;
    }
    search_authors();
}
function search_authors() {
    let normal_search = document.getElementById("normal-search");
    page_rotate(90);
    let params = getQueryObject();
    delete params['p'];
    params['author'] = normal_search.value;
    setTimeout(function(){
        loading();
    },500);
    setTimeout(function(){
        let p = [];
        for (var key in params) {
            p.push(key + "=" + params[key]);
        }
        nUrl = 'author' + ((p.length > 0) ? "?" : "") + p.join("&");
        nUrl = window.location.protocol + "//" + window.location.host + "/" + nUrl;
        this.location = nUrl;
        window.location.href = nUrl;
    },500);
}

function next_page() {
    page = 1;
    if (GetQueryString("p") != null)
        page = Number(GetQueryString("p"));
    page_rotate(90);
    setTimeout(function(){
        loading();
    },500);
    setTimeout(function(){
        replaceParamVal("p", page + 1)
    },500);
}
function last_page() {
    page = 1;
    if (GetQueryString("p") != null)
        page = Number(GetQueryString("p"));
    page_rotate(-90);
    setTimeout(function(){
        loading();
    },500);
    setTimeout(function(){
        replaceParamVal("p", page - 1)
    },500);
}
function to_page() {
    if(event.keyCode != "13") {
        return;
    }
    num = event.currentTarget.value;
    if (num <= 0)
        num = 1;
    page_rotate(90);
    setTimeout(function(){
        loading();
    },500);
    setTimeout(function(){
        replaceParamVal("p", num)
    },500);
}

function GetQueryString(name) {
    var reg = new RegExp("(^|&)" + name + "=([^&]*)(&|$)");
    var r = window.location.search.substr(1).match(reg);
    if (r != null) {
        return unescape(r[2]);
    }
    return null;
}
function GetQueryStringDecode(name) {
    var reg = new RegExp("(^|&)" + name + "=([^&]*)(&|$)");
    var r = window.location.search.substr(1).match(reg);
    if (r != null) {
        return decodeURI(r[2]);
    }
    return null;
}
function getQueryObject(url) {
    url = url == null ? window.location.href : url;
    var search = url.substring(url.lastIndexOf("?") + 1);
    var obj = {};
    var reg = /([^?&=]+)=([^?&=]*)/g;
    search.replace(reg, function (rs, $1, $2) {
        var name = decodeURIComponent($1);
        var val = decodeURIComponent($2);
        val = String(val);
        obj[name] = val;
        return rs;
    });
    return obj;
}
function replaceParamVal(paramName, replaceWith) {
    var oUrl = this.location.href.toString();
    var re = eval('/('+ paramName+'=)([^&]*)/gi');
    var nUrl = oUrl.replace(re,paramName+'='+replaceWith);
    if (oUrl == nUrl) {
        if (nUrl.indexOf("?") != -1) {
            nUrl += "&" + paramName + "=" + replaceWith;
        } else {
            nUrl += "?" + paramName + "=" + replaceWith;
        }
    }
    this.location = nUrl;
    window.location.href = nUrl;
}

function page_rotate(deg) {
    var navi = document.getElementById("navi");
    navi.classList.remove("full");
    var utter = document.getElementById("utter");
    utter.classList.remove("back");
}
function page_rotate_back() {
    var navi = document.getElementById("navi");
    navi.classList.add("full");
    var utter = document.getElementById("utter");
    utter.classList.add("back");
}

function show_navi_bar() {
    var bar = event.currentTarget.parentNode;
    if (bar.classList.contains("unfolded")) { // fold it
        bar.classList.replace("unfolded", "folded");
        bar.classList.remove("sub");
        bar.children[2].classList.remove("sub");
    } else if (bar.classList.contains("folded")) { // unfold it
        bar.classList.replace("folded", "unfolded");
    }
}
function show_options() {
    var options = event.currentTarget.parentNode.parentNode.children[1];
    var background = event.currentTarget.parentNode.children[0];
    if (options.classList.contains("unfolded")) { // fold it
        options.classList.replace("unfolded", "folded");
        background.classList.replace("close", "show");
    } else if (options.classList.contains("folded")) { // unfold it
        options.classList.replace("folded", "unfolded");
        background.classList.replace("show", "close");
    }
}
function accurate() {
    folder = document.getElementById("accurate_fold");
    options = folder.parentNode.parentNode.parentNode;
    bar = folder.parentNode.parentNode;
    input = folder.parentNode.children[0];
    searcher = folder.parentNode.children[1];
    if (bar.classList.contains("unfolded")) { // fold it
        bar.classList.replace("unfolded", "folded");
        input.classList.remove("hide");
        searcher.classList.replace("accurate", "normal");
        folder.classList.replace("accurate", "normal");
        options.classList.remove("accurate");
        bar.children[1].classList.replace("show","hide");
        bar.children[2].classList.replace("show","hide");
    } else if (bar.classList.contains("folded")) { // unfold it
        bar.classList.replace("folded", "unfolded");
        input.classList.add("hide");
        folder.classList.replace("normal", "accurate");
        searcher.classList.replace("normal", "accurate");
        options.classList.add("accurate");
        bar.children[1].classList.replace("hide", "show");
        bar.children[2].classList.replace("hide", "show");
    }
}
function show_datapack(uid) {
    var target = event.currentTarget;
    if (target.classList.contains("unfolded")) { // fold it
        setTimeout(function() {
            target.children[0].style.transition = "transform 0.75s;";
            target.children[0].style.transform = "scale(1.25) rotateX(180deg)";
        }, 200);
        target.classList.replace("unfolded", "folding");
        fold_datapack(uid);
        setTimeout(function() {
            target.children[0].style.transition = null;
            target.children[0].style.transform = null;
            target.children[0].classList.replace("button-down", "button");
            target.classList.replace("folding", "folded");
        }, 1000);
    } else if (target.classList.contains("folded")) { // unfold it
        setTimeout(function() {
            target.children[0].style.transition = "transform 0.75s;";
            target.children[0].style.transform = "scale(1.25) rotateX(180deg)";
        }, 200);
        target.classList.replace("folded", "unfolding");
        unfold_datapack(uid);
        setTimeout(function() {
            target.children[0].style.transition = null;
            target.children[0].style.transform = null;
            target.children[0].classList.replace("button", "button-down");
            target.classList.replace("unfolding", "unfolded");
        }, 1000);
    }
}
function unfold_datapack(uid) {
    var datapack = document.getElementById(uid);
    objs = datapack.children;
    var cover = objs[0];
    var intro = objs[1];
    var attachments = objs[2];
    //cover
    setTimeout(function() {
        cover.style.width = "652px";
        cover.style.height = "320px";
    }, 500);
    cover.children[1].style.opacity = "0.5";
    //intro
    intro.style.height = "auto";
    setTimeout(function() {
        intro.style.left = "4px";
        intro.style.width = "652px";
        intro.children[0].style.width = "652px";
        intro.children[1].style.width = "636px";
    }, 500);
    intro.style.top = "320px";
    intro.children[1].style.height = "auto";
    //attachments
    attachments.style.height = "auto";
    attachments.children[0].display = "block";
    setTimeout(function() {
        for (i = 0; i < attachments.children[1].children.length; i++) {
            if (attachments.children[1].children[i].classList.contains("tag-2") || attachments.children[1].children[i].classList.contains("tag-3"))
                attachments.children[1].children[i].classList.remove("invisible");
        }
        attachments.style.left = "4px";
        attachments.style.width = "652px";
        attachments.children[1].style.height = "auto";
        attachments.children[1].style.width = "476px";
    }, 500);
    //generic
    intro_height = Number(window.getComputedStyle(intro).getPropertyValue("height").replace("px",""));
    attachments_height = Number(window.getComputedStyle(attachments).getPropertyValue("height").replace("px",""));
    attachments.style.top = (320 + intro_height) + "px";
    datapack.style.height = (320 + intro_height + attachments_height) + "px";
    setTimeout(function() {
        //refine height
        intro_height = Number(window.getComputedStyle(intro).getPropertyValue("height").replace("px",""));
        attachments_height = Number(window.getComputedStyle(attachments).getPropertyValue("height").replace("px",""));
        attachments.style.top = (320 + intro_height) + "px";
        datapack.style.height = (320 + intro_height + attachments_height) + "px";
    }, 1000);
}
function fold_datapack(uid) {
    var datapack = document.getElementById(uid);
    objs = datapack.children;
    var cover = objs[0];
    var intro = objs[1];
    var attachments = objs[2];
    //cover
    setTimeout(function() {
        cover.children[1].style.opacity = "1";
    }, 500);
    cover.style.width = "216px";
    cover.style.height = "216px";
    //intro
    intro.style.height = "176px";
    setTimeout(function() {
        intro.style.top = "0";
        intro.children[1].style.height = "128px";
    }, 500);
    intro.style.left = "220px";
    intro.style.width = "436px";
    intro.children[0].style.width = "98%";
    intro.children[1].style.width = "422px";
    //attachments
    for (i = 0; i < attachments.children[1].children.length; i++) {
        if (attachments.children[1].children[i].classList.contains("tag-2") || attachments.children[1].children[i].classList.contains("tag-3"))
            attachments.children[1].children[i].classList.add("invisible");
    }
    attachments.style.left = "220px";
    attachments.style.width = "436px";
    attachments.children[1].style.height = "40px";
    attachments.children[1].style.width = "276px";
    setTimeout(function() {
        attachments.style.height = "40px";
        attachments.children[0].display = "inline-block";
    }, 500);
    //generic
    setTimeout(function() {
        attachments.style.top = "178px";
        datapack.style.height = "216px";
    }, 1000);
}
function glass_pane_close() {
    target = event.currentTarget;
    if (target.classList.contains("closed")) {
        target.classList.replace("closed", "open");
        target.parentNode.children[2].style.opacity = null;
        target.parentNode.children[3].style.opacity = null;
    } else {
        target.classList.replace("open", "closed");
        target.parentNode.children[2].style.opacity = "0";
        target.parentNode.children[3].style.opacity = "0";
    }
}