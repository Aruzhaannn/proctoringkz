// Егер token бар болса — тікелей бетке жіберу
(function () {
  const token = localStorage.getItem('accessToken');
  const role  = (() => { try { return JSON.parse(localStorage.getItem('user'))?.role; } catch { return null; } })();
  if (token && role) redirectByRole(role);
})();

function redirectByRole(role) {
  if      (role === 'STUDENT') window.location.href = 'pages/student-dashboard.html';
  else if (role === 'TEACHER') window.location.href = 'pages/teacher-dashboard.html';
  else if (role === 'ADMIN')   window.location.href = 'pages/admin-dashboard.html';
}

// Role tabs
document.querySelectorAll('.role-tab').forEach(tab => {
  tab.addEventListener('click', () => {
    document.querySelectorAll('.role-tab').forEach(t => t.classList.remove('active'));
    tab.classList.add('active');
  });
});

function togglePass() {
  const input = document.getElementById('passInput');
  input.type = input.type === 'password' ? 'text' : 'password';
}

function showError(msg) {
  let el = document.getElementById('loginError');
  if (!el) {
    el = document.createElement('div');
    el.id = 'loginError';
    el.style.cssText = 'color:#ff5050;font-size:0.85rem;margin-top:8px;text-align:center;';
    document.getElementById('loginBtn').insertAdjacentElement('afterend', el);
  }
  el.textContent = msg;
}

document.getElementById('loginForm').addEventListener('submit', async function (e) {
  e.preventDefault();

  const btn       = document.getElementById('loginBtn');
  const emailVal  = this.querySelector('input[type="email"]').value.trim();
  const passVal   = document.getElementById('passInput').value;

  if (!emailVal || !passVal) { showError('Email және пароль енгізіңіз'); return; }

  btn.innerHTML  = '<span class="btn-text">Кірілуде...</span>';
  btn.disabled   = true;

  try {
    const data = await AuthAPI.login(emailVal, passVal);
    Auth.save(data);
    redirectByRole(data.role);
  } catch (err) {
    showError('Email немесе пароль қате');
    btn.innerHTML = '<span class="btn-text">Жүйеге кіру</span><div class="btn-arrow">→</div>';
    btn.disabled  = false;
  }
});