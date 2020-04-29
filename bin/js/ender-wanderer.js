let statistic = {}, // name -> id
    tags = [],      // { c: count, r: raw html, s: sub node count, k: arc_tan of height and width, p: placement { x, y, r, s }, d: [] } (sort by count)
    datapacks = [], // { n: name, u: uid, t: raw tags, _t: id list of tags }
    relations = []; // []{ c: relation count, w: summary of weight} relation table
let sum = 0, tag_raw_height = 0,// amount of tags
    root = null, tags_old = null; // root node
function getTagsInDatapack(tags) {
    let elements = []
    Array.prototype.forEach.call(tags.children, function (t) {
        if (t.classList.contains("tag-2") || t.classList.contains("tag-3")) {
            elements.push(t);

        }
    });
    return elements;
}

// Read
Array.prototype.forEach.call(document.querySelectorAll('.datapack-short'), function (d) {
    elements = getTagsInDatapack(d.children[1])
    for (let i = 0; i < elements.length; i++) {
        if (statistic.hasOwnProperty(elements[i].textContent)) {
            let id = statistic[elements[i].textContent], t = tags[id];
            t.c++;
            t.d.push(datapacks.length);
        }
        else {
            statistic[elements[i].textContent] = sum;
            tag_raw_height = elements[i].offsetHeight;
            tags.push({
                c: 1,
                r: elements[i].cloneNode(true),
                s: 0,
                k: Math.atan2(elements[i].offsetHeight, elements[i].offsetWidth),
                p: {
                    x: 0,   // position
                    y: 0,
                    r: 0,   // radius
                    s: 0    // sigma
                },
                d: [datapacks.length]
            });
            sum++;
        }
    }
    datapacks.push({
        n: d.children[0].textContent,
        u: d.children[0].id,
        t: d.children[1],
        _t: []
    });
}); // read data
tags.sort(function(a,b) {
    return b.c-a.c;
}) // set rank
for (let i = 0; i < sum; i++) {
    statistic[tags[i].r.textContent] = i;
} // update index of statistics, inverted
for (let i = 0; i < datapacks.length; i++) {
    Array.prototype.forEach.call(getTagsInDatapack(datapacks[i].t), function(t) {
        let j = statistic[t.textContent];
        datapacks[i]._t.push(j);
    });
    datapacks[i]._t.sort((a,b) => a - b);
}

// Calculate
for (let i = 0; i < sum; i++) {
    relations[i] = [];
    for (let j = 0; j < sum; j++)
        relations[i][j] = {
            c: 0,
            w: 0
        };
} // init relation table
Array.prototype.forEach.call(document.querySelectorAll('.datapack-short'), function (d) {
    elements = elements = getTagsInDatapack(d.children[1])
    for (let i = 0; i < elements.length; i++) {
        let vi = statistic[elements[i].textContent];
        for (let j = 0; j < elements.length; j++) {
            if (elements[j] !== elements[i]) {
                let vj = statistic[elements[j].textContent];
                if (vi < vj)
                    relations[vi][vj].c++;
            }
        }
    }
}); // build relation table in partial order
for (let i = sum - 1; i >= 0; i--) {
    let nw = tags[i].c;
    for (let j = i + 1; j < sum; j++) {
        if (relations[i][j].c > 0) {
            relations[i][j].w = relations[j][j].w - tags[j].c;
            nw += relations[i][j].w;
        }
    }
    for (let j = i + 1; j < sum; j++) {
        if (relations[i][j].c > 0) {
            relations[j][i].w = nw;
        }
    }
    relations[i][i].w = nw;
} // set weight

// Canvas
Array.prototype.forEach.call(document.querySelectorAll('.tag-unique'), function (e) {
    root = e.parentNode;
    tags_old = e;
}); // remove all
let canvas = document.createElement("canvas")
let tag_list = document.createElement("div")
canvas.id = "canvas";
tag_list.id = "tag_list";
document.body.appendChild(canvas); // add canvas
document.body.appendChild(tag_list); // add tags panel
datapack_box = document.createElement("div")
datapack_box.id = "datapack_box"; // add datapacks panel
document.body.appendChild(datapack_box);

// Draw
let progress = 0;
root.removeChild(tags_old);
let off_height = document.getElementById("navi").offsetHeight + root.offsetHeight;
canvas.width = document.documentElement.clientWidth;
canvas.height = document.documentElement.clientHeight - off_height;
let ctx = canvas.getContext("2d"),
    cx = document.documentElement.clientWidth / 2, cy = (document.documentElement.clientHeight - off_height) / 2, // client screen
    _cx = 0, _cy = 0,
    _dx = 0, _dy = 0;
ctx.lineWidth = 2;
let cx_ = 0, cy_ = 0, _cx_ = 0, _cy_ = 0, _dx_ = 0, _dy_ = 0; // mark for screen
let scale = 1, root_sigma = Math.PI / 2,
    x_min = 0, y_min = 0, x_max = 0, y_max = 0, // canvas params
    x_mass = 0, y_mass = 0; // mass of the whole
function place(i) {
    let n = 0, _j = 0, _x_mass = 0, _y_mass = 0, r = Math.sqrt(tags[i].c);
    for (let j = 0; j < i; j++) {
        if (relations[j][i].c > 0) {
            n++;
            _x_mass += tags[j].p.x;
            _y_mass += tags[j].p.y;
            _j = j;
        }
    }
    if (n === 1) { // expanding node, outside net
        let sigma = tags[_j].p.s, sw = - tags[_j].c, lw = 0;
        for (let j = 0; j <= _j; j++) sw += relations[_j][j].w; // sum of weight
        for (let j = _j + 1; j < i; j++) lw += relations[j][_j].w; // sum of weight of children of _j before i
        sigma += (sw + tags[_j].c - relations[_j][_j].w) / sw / 2 * Math.PI - Math.PI; // relative origin angle
        let _sigma = (lw + relations[_j][i].w / 2) / sw * Math.PI * 2 + sigma; // edge angle
        if (i === 1) {
            _sigma = root_sigma;
        }
        let px = tags[_j].p.x + Math.cos(_sigma) * (r + Math.sqrt(tags[_j].c)),
            py = tags[_j].p.y + Math.sin(_sigma) * (r + Math.sqrt(tags[_j].c));
        let __s = confine(i, px, py, r, _j);
        if (__s !== null) _sigma = __s;
        tags[i].p.x = tags[_j].p.x + Math.cos(_sigma) * (r + Math.sqrt(tags[_j].c));
        tags[i].p.y = tags[_j].p.y + Math.sin(_sigma) * (r + Math.sqrt(tags[_j].c));
    } else if (n > 1) { // binding node, inside net
        tags[i].p.x = _x_mass / n;
        tags[i].p.y = _y_mass / n;
    }
    tags[i].p.r = r;
    if (i === 0) {
        tags[i].p.s = root_sigma;
    } else {
        tags[i].p.s = Math.atan2(tags[i].p.y - _y_mass / n, tags[i].p.x - _x_mass / n);
    }
    if (i > 0) fix(i);

    x_mass += tags[i].p.x;
    y_mass += tags[i].p.y;

    x_min = Math.min(x_min, tags[i].p.x - r);
    y_min = Math.min(y_min, tags[i].p.y - r);
    x_max = Math.max(x_max, tags[i].p.x + r);
    y_max = Math.max(y_max, tags[i].p.y + r);
}
function confine(i, px, py, r, j) { // add a drag if exceeded max margin
    let _pr = Math.max(x_max, y_max), _nr = Math.min(x_min, y_min), dr = Math.max(Math.abs(_nr), _pr);
    let theta_1 = Math.atan2(tags[j].p.y - (x_min + x_max) / 2, tags[j].p.x - (y_min + y_max) / 2), // vector to center of graph
        theta_2 = Math.atan2(py - tags[j].p.y, px - tags[j].p.x);
    if (px * px + py * py > dr * dr) theta_1 = Math.atan2(tags[j].p.y - (y_mass / i) / 2, tags[j].p.x - (x_mass / i) / 2) // exceed
    if (Math.sin(theta_2 - theta_1) > 0) return theta_1 + Math.PI / 2;
    else return theta_1 - Math.PI / 2;
}
function fix(i) { // fix when being overlapped, find a gap to place it again and keep balance of the graph.
    let _x_mass = 0, _y_mass = 0, r = tags[i].p.r, n = 0;
    for (let j = 0; j < i; j++) { // collide detection
        if ((tags[j].p.x - tags[i].p.x) * (tags[j].p.x - tags[i].p.x) + (tags[j].p.y - tags[i].p.y) * (tags[j].p.y - tags[i].p.y) < (tags[j].p.r + r) * (tags[j].p.r + r)) {
            _x_mass += tags[j].p.x;
            _y_mass += tags[j].p.y;
            n++;
        }
    }
    if (n === 0) {
        return
    }
    if (_x_mass === 0 && _y_mass === 0) _x_mass = 1;
    let v = vector_add([_x_mass / n - x_mass / i, _y_mass / n - y_mass / i], [(x_min + x_max) / 2 - x_mass / i, (y_min + y_max) / 2 - y_mass / i]),
        _diff_x = (v[0] === 0) ? 1e-16 : 0, _diff_y = (v[1] === 0) ? 1e-16 : 0;
    let k = - (v[0] + _diff_x) / (v[1] + _diff_y), b = _y_mass / n - k * _x_mass / n,
        c = (tags[i].p.x / k + tags[i].p.y - b) / (k + 1 / k), clipped = [];
    function vector_add(a, b) {
        return [(a[0] + b[0]) / 2, (a[1] + b[1]) / 2];
    }
    function find_gap() {
        for (let j = 0; j < i; j++) {
            let d = Math.abs(k * tags[j].p.x - tags[j].p.y + b) / Math.sqrt(k * k + 1);
            if (d < tags[j].p.r + r) { // if connect to the line
                let l = Math.sqrt((tags[j].p.r + r) * (tags[j].p.r + r) - d * d) / Math.sqrt(k * k + 1),
                    cl = (tags[j].p.x / k + tags[j].p.y - b) / (k + 1 / k);
                clipped.push({l: cl-l, r: cl+l});
            }
        }
        clipped.sort(function(a,b) {
            return a.l-b.l;
        });
        let ans_l = c, ans_r = c;
        if (clipped.length > 0) {
            ans_l = clipped[0].l;
            ans_r = clipped[0].r;
        }
        for (let j = 1; j < clipped.length; j++) {
            if (clipped[j].l >= ans_r) { // find gap
                if (ans_r > c) break; // get answer
                ans_l = clipped[j].l;
                if (ans_l > c) break; // get answer
                ans_r = clipped[j].r;
            } else { // connecting clip
                if (clipped[j].r > ans_r) ans_r = clipped[j].r;
            }
        }
        if (ans_l < ans_r) { // dilemma
            if (c - ans_l < ans_r - c) tags[i].p.x = ans_l;
            else tags[i].p.x = ans_r;
        } else tags[i].p.x = c;
        tags[i].p.y = k * tags[i].p.x + b;
    }
    find_gap();
}
function place_on_tags(i) {
    let tag = tag_list.children[i],
        width = tags[i].p.r * Math.cos(tags[i].k) * 2 * scale,
        height = tags[i].p.r * Math.sin(tags[i].k) * 2 * scale;
    tag.style.setProperty("--s", (height / tag_raw_height).toString());
    tag.style.setProperty("--l", cx + (tags[i].p.x - _cx) * scale - width / 2 + "px");
    tag.style.setProperty("--t", cy + (tags[i].p.y - _cy) * scale - height / 2 + "px");
}
function update(i) {
    for (let j = 0; j <= i; j++) {
        place_on_tags(j);
    }
    // draw relation again
    if (current_tag_uid !== "") {
        draw_relation_on();
    }
}

function onSubScreenChanged() {
    if (cx_ !== cx || cy_ !== cy || _cx_ !== _cx || _cy_ !== _cy || _dx_ !== _dx || _dy_ !== _dy) {
        cx_ = cx; cy_ = cy; _cx_ = _cx; _cy_ = _cy; _dx_ = _dx; _dy_ = _dy;
        return true
    }
    return false
} // test sub screen changed, and re-draw relation on canvas
function Animation() {
    tag_list.style.setProperty("--w", document.documentElement.clientWidth + "px");
    tag_list.style.setProperty("--h", (document.documentElement.clientHeight - off_height) + "px");
    cx = document.documentElement.clientWidth / 2;
    cy = (document.documentElement.clientHeight - off_height) / 2;
    if (progress < sum) {
        place(progress);
        tag_list.appendChild(tags[progress].r.cloneNode(true)); // add child
        place_on_tags(progress);
        progress += 1;
        if (current_tag_uid !== "" && datapacks[current_datapack_id]._t.indexOf(progress - 1) > -1) { // update again when new tag occurs
            screen_relation_on();
            draw_relation_on();
        }
    } // draw new tag
    if (current_tag_uid === "") { // not fixed view
        _cx = (x_max + x_min) / 2; _cy = (y_max + y_min) / 2;
        _dx = (x_max - x_min); _dy = (y_max - y_min);
    } // normal view

    scale = Math.min( cx / _dx * 2, cy / _dy * 2);
    if (onSubScreenChanged())
        update(progress - 1);
    window.requestAnimationFrame(Animation);
}
window.requestAnimationFrame(Animation);

// Interaction
let current_tag_uid = "", selected_tag_content = "", selected_tag_id = 0,
    current_datapack_id = 0, selected_datapack_id = 0;
function jump_tag(id) {
    if (current_tag_uid === id) { // double clicked, jump
        let params = getQueryObject();
        let url = window.location.protocol + "//" + window.location.host + "/tag/" + id;
        if (params.hasOwnProperty('language')) url += "?language=" + params['language'];
        location.href = url;
        return;
    }
    reset_related()
    // set current tag
    current_tag_uid = id;
    selected_tag_id = statistic[event.currentTarget.textContent];
    selected_tag_content = event.currentTarget.textContent;
    tag_list.children[selected_tag_id].classList.add("center");
    current_datapack_id = tags[selected_tag_id].d[0];
    selected_datapack_id = 0
    // calculate screen
    datapack_box_on();
    screen_relation_on();
    draw_relation_on();
} // click tag
function reset_related() {
    for (let i = 0; i < datapacks[current_datapack_id]._t.length; i++) {
        let _i = datapacks[current_datapack_id]._t[i];
        if (_i >= progress) break;
        tag_list.children[_i].classList.remove("related");
    }
    tag_list.children[selected_tag_id].classList.remove("center");
} // reset current related tags
function datapack_box_on() {
    let datapack_id = tags[selected_tag_id].d[selected_datapack_id];
    while(datapack_box.hasChildNodes()) datapack_box.removeChild(datapack_box.firstChild); // clear datapack box
    let title = document.createElement("div"), cover = document.createElement("div"),
        _tags = datapacks[current_datapack_id].t.cloneNode(true);
    let name = document.createElement("div"), goto = document.createElement("div");
    let head = document.createElement("div"), info = document.createElement("span"),
        left = document.createElement("span"), right = document.createElement("span");
    // head
    head.classList.add("head"); info.classList.add("info"); left.classList.add("left"); right.classList.add("right");
    info.textContent = (selected_datapack_id + 1) + " | " + tags[selected_tag_id].d.length;
    left.setAttribute("onclick", "turn_left(true);"); right.setAttribute("onclick", "turn_left(false);");
    if (selected_datapack_id > 0) head.appendChild(left);
    head.appendChild(tags[selected_tag_id].r.cloneNode(true));
    if (selected_datapack_id < tags[selected_tag_id].d.length - 1) head.appendChild(right);
    head.appendChild(info);
    // name
    title.classList.add("title"); cover.classList.add("cover");
    name.textContent = datapacks[datapack_id].n;
    name.setAttribute("onclick", "jump_datapack('" + datapacks[datapack_id].u + "')")
    name.classList.add("name"); goto.classList.add("_goto"); goto.classList.add("mask-attach");
    goto.setAttribute("onclick", "jump_datapack('" + datapacks[datapack_id].u + "')")
    title.appendChild(name); title.appendChild(goto);
    // cover
    let img = document.createElement("img")
    img.setAttribute("src", "/bin/img/cover/" + datapacks[datapack_id].u + ".png");
    cover.appendChild(img);
    // append
    for(let j = _tags.children.length - 1; j >= 0; j--) {
        if (_tags.children[j].classList.contains("tag-0") || _tags.children[j].classList.contains("tag-1")) {
            _tags.removeChild(_tags.children[j]);
        }
        if (_tags.children[j].textContent === selected_tag_content) _tags.children[j].classList.add("center");
    }
    datapack_box.appendChild(head); datapack_box.appendChild(title); datapack_box.appendChild(cover); datapack_box.appendChild(_tags);
}// update datapack box
function screen_relation_on() {
    let ct = tags[selected_tag_id];
    let _x_min = ct.p.x - ct.p.r, _x_max = ct.p.x + ct.p.r,
        _y_min = ct.p.y - ct.p.r, _y_max = ct.p.y + ct.p.r;
    for (let i = 0; i < datapacks[current_datapack_id]._t.length; i++) {
        if (datapacks[current_datapack_id]._t[i] >= progress) break;
        ct = tags[datapacks[current_datapack_id]._t[i]];
        _x_min = Math.min(ct.p.x - ct.p.r, _x_min);
        _x_max = Math.max(ct.p.x + ct.p.r, _x_max);
        _y_min = Math.min(ct.p.y - ct.p.r, _y_min);
        _y_max = Math.max(ct.p.y + ct.p.r, _y_max);
    } // for each tag
    // set sub screen
    _cx = (_x_max + _x_min) / 2; _cy = (_y_max + _y_min) / 2;
    _dx = (_x_max - _x_min); _dy = (_y_max - _y_min);
    scale = Math.min( cx / _dx * 2, cy / _dy * 2);
    datapack_box.style.display = null;
    datapack_box.style.setProperty("--t", document.documentElement.clientHeight + "px");
} // select all related tags, then update screen size and place datapack box
function draw_relation_on() {
    canvas.width = document.documentElement.clientWidth;
    canvas.height = document.documentElement.clientHeight - off_height;
    if (current_tag_uid === "") {
        tag_list.classList.remove("transparent");
        return;
    } // reset
    let ct = tag_list.children[selected_tag_id];
    if (!tag_list.classList.contains("transparent"))
        tag_list.classList.add("transparent");// make all tags transparent
    for (let i = 0; i < datapacks[current_datapack_id]._t.length; i++) {
        let _i = datapacks[current_datapack_id]._t[i];
        if (_i >= progress) break;
        let cl = tag_list.children[_i];
        cl.classList.add("related");
        if (cl.classList.contains("tag-2")) {
            ctx.strokeStyle = "rgba(22, 135, 146, 0.2)";
        } else if (cl.classList.contains("tag-3")) {
            ctx.strokeStyle = "rgba(158, 113, 158, 0.2)";
        }
        ctx.beginPath();
        ctx.moveTo(Number(ct.style.getPropertyValue("--l").replace("px","")), Number(ct.style.getPropertyValue("--t").replace("px","")));
        ctx.lineTo(Number(cl.style.getPropertyValue("--l").replace("px","")), Number(cl.style.getPropertyValue("--t").replace("px","")));
        ctx.stroke();
    } // link all related tags
} // draw relations between all selected tags
document.addEventListener("click", function (e) {
    if (e.target === tag_list) {
        // reset current related tags
        reset_related()
        current_tag_uid = ""; selected_tag_id = 0; current_datapack_id = 0;
        draw_relation_on();
        datapack_box.style.display = "none";
    }
}) // cancel select
function turn_left(isLeft) {
    reset_related()
    if (isLeft && selected_datapack_id > 0) selected_datapack_id--;
    else if (selected_datapack_id < tags[selected_tag_id].d.length - 1) selected_datapack_id++;
    current_datapack_id = tags[selected_tag_id].d[selected_datapack_id];
    // calculate screen
    datapack_box_on();
    screen_relation_on();
    draw_relation_on();
}