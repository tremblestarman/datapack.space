let elements = document.querySelectorAll('.tags .tag-2, .tags .tag-3')
let statistic = {}, rank = [], datapacks = [];
for (let i = 0; i < elements.length; i++) {
    if (statistic.hasOwnProperty(elements[i].textContent)) {
        statistic[elements[i].textContent].v++;
        elements[i].parentNode.removeChild(elements[i]);
    }
    else statistic[elements[i].textContent] = { v: 1, i: i};
}
Array.prototype.forEach.call(Object.keys(statistic).sort(function(a,b) {
        return statistic[b].v-statistic[a].v
    }), function (k) {
    rank.push({
        el: elements[statistic[k].i],
        c: statistic[k].v
    })
});
Array.prototype.forEach.call(document.querySelectorAll('.name'), function (d) {
    datapacks.push({
        name: d.textContent,
        id: d.id
    });
})

Array.prototype.forEach.call(document.querySelectorAll('.tag-unique'), function (e) {
    e.parentNode.removeChild(e);
});