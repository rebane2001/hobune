/*
TODO: Implement sorting
var toSort = document.getElementById('list').children;
toSort = Array.prototype.slice.call(toSort, 0);

toSort.sort(function(a, b) {
    var aord = +a.id.split('-')[1];
    var bord = +b.id.split('-')[1];
    // two elements never have the same ID hence this is sufficient:
    return (aord > bord) ? 1 : -1;
});

var parent = document.getElementById('list');
parent.innerHTML = "";

for(var i = 0, l = toSort.length; i < l; i++) {
    parent.appendChild(toSort[i]);
}
*/