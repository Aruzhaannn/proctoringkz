// Theme initializer — runs before paint to prevent flash
(function () {
  const saved = localStorage.getItem('proktorai-theme');
  if (saved === 'light') {
    document.documentElement.setAttribute('data-theme', 'light');
  }
})();

function toggleTheme() {
  const html = document.documentElement;
  const isLight = html.getAttribute('data-theme') === 'light';
  if (isLight) {
    html.removeAttribute('data-theme');
    localStorage.setItem('proktorai-theme', 'dark');
  } else {
    html.setAttribute('data-theme', 'light');
    localStorage.setItem('proktorai-theme', 'light');
  }
}