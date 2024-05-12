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

function getSearchRegex(searchTerm) {
  const regexParts = searchTerm.match(/^\/(.*)\/([dgimsuvy]*)$/);
  try {
    return regexParts && new RegExp(regexParts[1], regexParts[2]);
  } catch(err) { console.error(err); }
}

function channelSearch() {
  let searchTerm = document.querySelector(".search").value;

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

  const searchRegex = getSearchRegex(searchTerm);
  searchTerm = searchTerm.toLowerCase();

  document.querySelectorAll('.searchable').forEach((e) => {
    let filtered = false;
    for (const c of allowedClasses) {
      if (!e.querySelector(`.${c}`)) filtered = true;
    }
    for (const c of filteredClasses) {
      if (e.querySelector(`.${c}`)) filtered = true;
    }

    if (!filtered && (searchTerm === "" ||
        (!searchRegex && e.dataset.search.toLowerCase().includes(searchTerm)) ||
        (searchRegex && searchRegex.test(e.dataset.search))
      )) {
      e.classList.remove("hide");
    } else {
      e.classList.add("hide");
    }
  });
}

window.addEventListener("load", () => {
  channelSearch();
});
