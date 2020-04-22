let statistic = {}, // name -> id
    tags = [],      // { c: count, r: raw html, s: sub node count, p: placement { x, y, r, t } } (sort by count)
    datapacks = [], // { n: name, u: uid }
    relations = []; // []{ c: relation count, w: summary of weight} relation table
let sum = 0, // amount of tags
    scale = 1, root_sigma = Math.PI / 2, x_min = 0, y_min = 0, x_max = 0, y_max = 0, // canvas params
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
function place(i, sigma, x, y) {
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
            place(j, _sigma, _x, _y);
        }
    }
    tags[i].p.x = x; tags[i].p.y = y; tags[i].p.r = r; tags[i].p.s = sigma;
}
place(0, root_sigma, 0, 0);
for (let i = 0; i < sum; i++) {
    console.log(tags[i].p.x, tags[i].p.y, tags[i].p.r, tags[i].p.s);
}

// Reflect
Array.prototype.forEach.call(document.querySelectorAll('.tag-unique'), function (e) {
    root = e.parentNode;
    root.removeChild(e);
}); // remove all
tags = document.createElement("canvas")
tags.style.width = "100%";
tags.style.height = "100%";
tags.id = "tags";
root.appendChild(tags); // add tags panel
datapacks = document.createElement("div")
datapacks.id = "datapacks"; // add datapacks panel
root.appendChild(datapacks);