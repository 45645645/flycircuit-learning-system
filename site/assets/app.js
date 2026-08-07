const search = document.querySelector('#paper-search');
if (search) {
  search.addEventListener('input', () => {
    const term = search.value.trim().toLowerCase();
    document.querySelectorAll('.paper-card').forEach((card) => {
      card.hidden = term && !card.dataset.search.includes(term);
    });
  });
}

if (location.hash) {
  const target = document.querySelector(location.hash);
  if (target) target.classList.add('targeted');
}

