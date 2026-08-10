(function () {
  const form = document.getElementById("site-search");
  const input = document.getElementById("search-input");
  const results = document.getElementById("search-results");
  if (!form || !input || !results) return;

  let index = [];
  let loaded = false;

  function render(query) {
    const normalized = query.trim().toLowerCase();
    if (!normalized) {
      results.hidden = true;
      results.innerHTML = "";
      return;
    }
    const matches = index
      .filter((item) => `${item.title} ${item.text}`.toLowerCase().includes(normalized))
      .slice(0, 8);
    results.innerHTML = matches.length
      ? matches.map((item) => `<a class="search-result" href="${item.url}"><strong>${item.title}</strong><small>${item.text.slice(0, 100)}</small></a>`).join("")
      : '<div class="search-result"><small>没有匹配的研究文档</small></div>';
    results.hidden = false;
  }

  form.addEventListener("submit", (event) => event.preventDefault());
  input.addEventListener("focus", () => {
    if (loaded) render(input.value);
    if (!loaded) {
      fetch(`${document.body.dataset.baseurl || ""}index.json`)
        .then((response) => response.json())
        .then((data) => { index = data; loaded = true; render(input.value); });
    }
  });
  input.addEventListener("input", () => { if (loaded) render(input.value); });
  document.addEventListener("click", (event) => {
    if (!form.contains(event.target)) results.hidden = true;
  });
})();
