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

document.querySelectorAll('.topnav a').forEach((link) => {
  const linkPath = new URL(link.href).pathname;
  const exactPage = link.href === location.href.split('#')[0];
  const sectionPage = (location.pathname.includes('/tutorials/') && linkPath.endsWith('/tutorials.html'))
    || (location.pathname.includes('/papers/') && linkPath.endsWith('/papers.html'));
  if (exactPage || sectionPage) link.setAttribute('aria-current', 'page');
});

const zoomButtons = document.querySelectorAll('.media-zoom');
if (zoomButtons.length) {
  const lightbox = document.createElement('div');
  lightbox.className = 'media-lightbox';
  lightbox.setAttribute('role', 'dialog');
  lightbox.setAttribute('aria-modal', 'true');
  lightbox.setAttribute('aria-label', '圖片放大檢視');
  const enlarged = document.createElement('img');
  const close = document.createElement('button');
  close.className = 'lightbox-close';
  close.type = 'button';
  close.setAttribute('aria-label', '關閉放大圖片');
  close.textContent = '×';
  lightbox.appendChild(enlarged);
  lightbox.appendChild(close);
  document.body.appendChild(lightbox);
  let trigger = null;

  const closeLightbox = () => {
    lightbox.classList.remove('open');
    document.body.style.overflow = '';
    enlarged.removeAttribute('src');
    if (trigger) trigger.focus();
  };

  zoomButtons.forEach((button) => {
    button.addEventListener('click', () => {
      const image = button.querySelector('img');
      trigger = button;
      enlarged.src = image.src;
      enlarged.alt = image.alt;
      lightbox.classList.add('open');
      document.body.style.overflow = 'hidden';
      close.focus();
    });
  });
  close.addEventListener('click', closeLightbox);
  lightbox.addEventListener('click', (event) => {
    if (event.target === lightbox) closeLightbox();
  });
  document.addEventListener('keydown', (event) => {
    if (event.key === 'Escape' && lightbox.classList.contains('open')) closeLightbox();
  });
}
