let statistic = {}, // name -> id
    tags = [],      // { c: count, r: raw html, s: sub node count } (sort by count)
    datapacks = [], // { n: name, u: uid }
    relations = []; // [][] relation table
let sum = 0, root = null;
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
                s: 0
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
for (let i = 0; i < sum; i++) {
    relations[i] = [];
    for (let j = 0; j < sum; j++)
        relations[i][j] = 0;
} // init relation table
Array.prototype.forEach.call(document.querySelectorAll('.datapack-short'), function (d) {
    elements = getTagsInDatapack(d)
    for (let i = 0; i < elements.length; i++) {
        let vi = statistic[elements[i].textContent];
        for (let j = 0; j < elements.length; j++) {
            if (elements[j] !== elements[i]) {
                let vj = statistic[elements[j].textContent];
                if (vi < vj)
                    relations[vi][vj]++;
            }
        }
    }
}); // build relation table in partial order
for (let i = 0; i < sum; i++) {
    for (let j = 0; j < sum; j++) {
        for (let k = 0; k < sum; k++) {
            if (relations[i][k] > 0 && relations[k][j] > 0) {
                relations[i][j] = 0;
            }
        }
        if (relations[i][j] > 0) {
            tags[i].s++;
        }
    }
    console.log(tags[i].r.textContent, tags[i].s, relations[i].join(" "));
} // hasse it

Array.prototype.forEach.call(document.querySelectorAll('.tag-unique'), function (e) {
    root = e.parentNode;
    root.removeChild(e);
}); // remove all
tags = document.createElement("canvas")
tags.id = "tags";
root.appendChild(tags); // add tags panel
datapacks = document.createElement("div")
datapacks.id = "datapacks"; // add datapacks panel
root.appendChild(datapacks);

