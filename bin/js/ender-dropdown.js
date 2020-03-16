/*Copyright (c) 2020 by Aaron Iker (https://codepen.io/aaroniker/pen/MWgjERQ)
Permission is hereby granted, free of charge, to any person obtaining a copy of this software and associated documentation files (the "Software"), to deal in the Software without restriction, including without limitation the rights to use, copy, modify, merge, publish, distribute, sublicense, and/or sell copies of the Software, and to permit persons to whom the Software is furnished to do so, subject to the following conditions:
The above copyright notice and this permission notice shall be included in all copies or substantial portions of the Software.
THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.*/
/*Rewritten and adapted using raw javascript*/
combo_default();
function combo_default() {
    let order = document.getElementById("order"),
        source_el = document.getElementById("filter-source"),
        version_el = document.getElementById("filter-version"),
        post_time = document.getElementById("filter-post-time"),
        update_time = document.getElementById("filter-update-time");
    function clear_options(obj) {
        while(obj.firstChild)
            obj.removeChild(obj.firstChild);
        let option = document.createElement('option');
        option.value = '0';
        option.innerText = '-';
        obj.appendChild(option);
    }
    if (GetQueryStringDecode("search") != null ||
        GetQueryStringDecode("name") != null ||
        GetQueryStringDecode("author") != null ||
        GetQueryStringDecode("intro") != null) {
        clear_options(order);
    } else {
        if (order != null && GetQueryString("order") != null) {
            order.children[order.selectedIndex].selected = false;
            order.children[Number(GetQueryString("order"))].selected = true;
        }
    }
    if (source_el != null && GetQueryString("source") != null) {
        let source = GetQueryString("source");
        source_el.children[source_el.selectedIndex].selected = false;
        Array.prototype.forEach.call(source_el.children, function(el) {
            if (el.value === source) el.selected = true;
        });
    }
    if (version_el != null && GetQueryString("version") != null) {
        let version = GetQueryString("version");
        version_el.children[version_el.selectedIndex].selected = false;
        Array.prototype.forEach.call(version_el.children, function(el) {
            if (el.value === version) el.selected = true;
        });
    }
    if (post_time != null && GetQueryString("p_time") != null) {
        post_time.children[post_time.selectedIndex].selected = false;
        post_time.children[Number(GetQueryString("p_time"))].selected = true;
    }
    if (update_time != null && GetQueryString("u_time") != null) {
        update_time.children[post_time.selectedIndex].selected = false;
        update_time.children[Number(GetQueryString("u_time"))].selected = true;
    }
}
function get_index(el) {
    if (!el) return -1;
    var i = 0;
    do {
        i++;
    } while (el = el.previousElementSibling);
    return i;
}
var elements = document.querySelectorAll('select[data-menu]');
Array.prototype.forEach.call(elements, function(select){
    let options = select.querySelectorAll('option'),
        menu = document.createElement('div'),
        button = document.createElement('div'),
        list = document.createElement('ul'),
        arrow = document.createElement('em');
    menu.classList.add('select-menu');
    button.classList.add('button');
    button.appendChild(arrow);
    select.parentNode.insertBefore(menu, select);
    menu.parentNode.removeChild(select);
    menu.appendChild(select);
    menu.appendChild(button);
    Array.prototype.forEach.call(options, function(option, i) {
        let li = document.createElement('li');
        li.textContent = option.textContent;
        list.append(li);
    });
    button.appendChild(list);
    menu.appendChild(list.cloneNode(true));
    menu.style.setProperty('--t', select.selectedIndex * -36 + 'px');
});
document.addEventListener('click', function(e) {
    for (var target = e.target; target && target != this; target = target.parentNode) {
        if (target.matches('.select-menu')) {
            let menu = target;
            if(!menu.classList.contains('open')) {
                menu.classList.add('open');
            }
            break;
        }
    }
}, false);
document.addEventListener('click', function(e) {
    for (var target = e.target; target && target != this; target = target.parentNode) {
        if (target.matches('.select-menu > ul > li')) {
            let li = target,
                menu = li.parentNode.parentNode,
                select = menu.children[0],
                selected = select.children[select.selectedIndex],
                index = get_index(li) - 1;
            menu.style.setProperty('--t', index * -36 + 'px');
            selected.selected = false;
            select.children[index].selected = true;
            menu.classList.add(index > get_index(selected) - 1 ? 'tilt-down' : 'tilt-up');
            setTimeout(() => {
                menu.classList.remove('open', 'tilt-up', 'tilt-down');
            }, 500);
            break;
        }
    }
}, false);
document.addEventListener('click', function(e) {
    e.stopPropagation();
    menus = document.querySelectorAll('.select-menu');
    Array.prototype.forEach.call(menus, function(menu) {
        if (!menu.contains(e.target)) {
            menu.classList.remove('open');
        }
    });
}, false);
