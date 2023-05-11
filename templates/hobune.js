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

function channelSort() {
	const sortOption = document.querySelector(".sort").value;
	const [sortBy, direction] = sortOption.split("-");
	const isInt = sortBy !== "search";
	const container = document.querySelector(".channels.flex-grid");
	[...container.children]
		.sort((a,b)=>{
			const dir = direction ? 1 : -1;
			let valA = a.dataset[sortBy];
			let valB = b.dataset[sortBy];
			if (isInt) {
				valA = parseInt(valA);
				valB = parseInt(valB);
			}
			return (valA>valB?1:-1)*dir;
		})
		.forEach(node=>container.appendChild(node));
}

function channelSearch() {
	let searchTerm = document.querySelector(".search").value.toLowerCase();
	const allowedClasses = [];
	const filteredClasses = [];
	const availableClasses = ["unlisted", "removed"];
	for (const availableClass of availableClasses) {
		if (searchTerm.includes("!" + availableClass)) {
			filteredClasses.push(availableClass);
			searchTerm = searchTerm.replace("!" + availableClass, "");
		} else if (searchTerm.includes(availableClass)) {
			allowedClasses.push(availableClass);
			searchTerm = searchTerm.replace(availableClass, "");
		}
	}

	document.querySelectorAll('.searchable').forEach((e) => {
		let filtered = false;
		for (const c of allowedClasses) {
			if (!e.classList.contains(c)) filtered = true;
		}
		for (const c of filteredClasses) {
			if (e.classList.contains(c)) filtered = true;
		}

    	if (!filtered && (searchTerm === "" || e.dataset.search.toLowerCase().includes(searchTerm))) {
    		e.classList.remove("hide");
    	} else {
    		e.classList.add("hide");
    	}
	});
}

window.addEventListener("load", () => {
	channelSearch();
});
