let statistic = {}, // name -> id
    tags = [],      // { c: count, r: raw html, s: sub node count, p: placement { x, y, r, s } } (sort by count)
    datapacks = [], // { n: name, u: uid }
    relations = []; // []{ c: relation count, w: summary of weight} relation table
let sum = 0, // amount of tags
    root = null; // root node

// Read
function getTagsInDatapack(d) {
    let elements = []
    Array.prototype.forEach.call(d.children[1].children, function (t) {
        if (t.classList.contains("tag-2") || t.classList.contains("tag-3")) {
            elements.push(t);
        }
    });
    return elements;
}
Array.prototype.forEach.call(document.querySelectorAll('.datapack-short'), function (d) {
    elements = getTagsInDatapack(d)
    for (let i = 0; i < elements.length; i++) {
        if (statistic.hasOwnProperty(elements[i].textContent)) {
            tags[statistic[elements[i].textContent]].c++;
        }
        else {
            statistic[elements[i].textContent] = sum;
            tags.push({
                c: 1,
                r: elements[i],
                s: 0,
                p: {
                    x: 0,   // position
                    y: 0,
                    r: 0,   // radius
                    s: 0    // sigma
                }
            })
            sum++;
        }
    }
    datapacks.push({
        n: d.children[0].textContent,
        u: d.children[0].id,
        t: d.children[1]
    });
}); // read data
tags.sort(function(a,b) {
    return b.c-a.c;
}) // set rank
for (let i = 0; i < sum; i++) {
    statistic[tags[i].textContent] = i;
} // update index of statistics, inverted

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
    elements = getTagsInDatapack(d)
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
for (let i = 0; i < sum; i++) {
    for (let j = 0; j < sum; j++) {
        for (let k = 0; k < sum; k++) {
            if (relations[i][j].c > 0 && relations[i][k].c > 0 && relations[k][j].c > 0) {
                relations[i][j].c = -relations[i][j].c;
            }
        }
        if (relations[i][j].c > 0) {
            tags[i].s++;
        }
    }
} // hasse it
function setWeight(i, p, pw) {
    let nw = tags[i].c;
    if (relations[i][p].w > 0)
        return relations[i][i].w;
    relations[i][p].w = pw;
    for (let j = i + 1; j < sum; j++) {
        if (relations[i][j].c > 0) {
            relations[i][j].w = setWeight(j, i, pw + tags[i].c);
            nw += relations[i][j].w;
        }
    }
    relations[i][i].w = nw;
    return nw;
}
setWeight(0, 0, 0);

// Draw
let scale = 1, root_sigma = Math.PI / 2, x_min = 0, y_min = 0, x_max = 0, y_max = 0, // canvas params
    x_mass = 0, y_mass = 0; // mass of the whole
function place(i) {
    let n = 0, _j = 0, _x_mass = 0, _y_mass = 0, r = Math.sqrt(tags[i].c);
    for (let j = 0; j < i; j++) {
        if (relations[j][i].c > 0) {
            n++;
            _x_mass += tags[j].p.x * tags[j].p.r * tags[j].p.r;
            _y_mass += tags[j].p.y * tags[j].p.r * tags[j].p.r;
            _j = j;
        }
    }
    if (n === 1) { // expanding node
        let sigma = tags[_j].p.s, sw = - tags[_j].c, lw = 0;
        for (let j = 0; j <= _j; j++) sw += relations[_j][j].w; // sum of weight
        for (let j = _j + 1; j < i; j++) lw += relations[j][_j].w; // sum of weight of children of _j before i
        sigma += (sw + tags[_j].c - relations[_j][_j].w) / sw / 2 * Math.PI - Math.PI; // relative origin angle
        let _sigma = (lw + relations[_j][i].w / 2) / sw * Math.PI * 2 + sigma;  // edge angle
        if (i === 1) {
            _sigma = root_sigma;
        }
        tags[i].p.x = tags[_j].p.x + Math.cos(_sigma) * (r + Math.sqrt(tags[_j].c));
        tags[i].p.y = tags[_j].p.y + Math.sin(_sigma) * (r + Math.sqrt(tags[_j].c));
    } else if (n > 1) { // binding node
        tags[i].p.x = _x_mass / n;
        tags[i].p.y = _y_mass / n;
    }
    tags[i].p.r = r;
    if (i === 0) {
        tags[i].p.s = root_sigma;
    }
    tags[i].p.s = Math.atan2(tags[i].p.y - _y_mass / n, tags[i].p.x - _x_mass / n);
    if (i > 0) fix(i);

    x_mass += tags[i].p.x;
    y_mass += tags[i].p.y;
    /*
    let t = tags[i],
        r = Math.sqrt(t.c),                             // radius of the tag
        sw = - t.c,                                     // total weight of sub nodes and parent nodes
        lw = 0;                                         // last weight
    for (let j = 0; j <= i; j++) sw += relations[i][j].w;
    sigma = sigma + (sw + t.c - relations[i][i].w) / sw / 2 * Math.PI - Math.PI; // relative origin angle
    for (let j = i + 1; j < sum; j++) {
        if (relations[i][j].c > 0) {
            let _r = Math.sqrt(tags[j].c),
                _sigma = (lw + relations[i][j].w / 2) / sw * Math.PI * 2 + sigma,  // edge angle
                _x = x + Math.cos(_sigma) * (r + _r) * 2,
                _y = y + Math.sin(_sigma) * (r + _r) * 2;
            lw += relations[i][j].w;
            tags[j].p.p.push(i);
            tags[i].p.x = x; tags[i].p.y = y; tags[i].p.r = r; tags[i].p.s = sigma;
        }
    }*/
}
function fix(i) {
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
    let k = (_y_mass / n - y_mass / i) / (_x_mass / n - x_mass / i), b = _y_mass / n - k * _x_mass / n,
        theta = Math.atan(k), c = (tags[i].p.x / k + tags[i].p.y - b) / (k + 1 / k), clipped = [];
    for (let j = 0; j < i; j++) {
        let d = distanceToLine(k, b, tags[j].p.x, tags[j].p.y);
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
function distanceToLine(k, b, x, y) {
    return Math.abs(k * x - y + b) / Math.sqrt(k * k + 1);
}
for (let i = 0; i < sum; i++) {
    place(i);
}

// Reflect
Array.prototype.forEach.call(document.querySelectorAll('.tag-unique'), function (e) {
    root = e.parentNode;
    root.removeChild(e);
}); // remove all
canvas = document.createElement("canvas")
canvas.width = document.documentElement.clientWidth;
canvas.height = document.documentElement.clientHeight;
canvas.style.zIndex = "1000";
canvas.id = "tags";
document.body.appendChild(canvas); // add tags panel
datapacks = document.createElement("div")
datapacks.id = "datapacks"; // add datapacks panel
document.body.appendChild(datapacks);
let ctx = canvas.getContext("2d"), cx = document.documentElement.clientWidth / 2, cy = document.documentElement.clientHeight / 2;

let progress = 0;
function buildAnimation() {
    let t = tags[progress];
    //console.log(t.p.x, t.p.y, t.p.r)
    ctx.beginPath();
    ctx.arc(t.p.x * 5 + cx, t.p.y * 5 + cy, t.p.r * 5, 0 ,2*Math.PI);
    ctx.stroke();
    if (progress < sum) {
        progress += 1;
        window.requestAnimationFrame(buildAnimation);
    }
}
window.requestAnimationFrame(buildAnimation);