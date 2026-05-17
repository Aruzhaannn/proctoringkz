// ── Login page logic ─────────────────────────────────────────
(function () {
  // If already logged in, redirect to dashboard
  const existing = Auth.token();
  if (existing && existing !== 'demo-token') {
    const role = Auth.role();
    redirectToDashboard(role);
    return;
  }

  // ── Role tabs: auto-fill demo credentials ────────────────
  const demoCredentials = {
    student: { email: 'student@demo.kz', password: 'demo123' },
    teacher: { email: 'teacher@demo.kz', password: 'demo123' },
    admin:   { email: 'admin@demo.kz',   password: 'demo123' }
  };

  let selectedRole = 'student';

  document.querySelectorAll('.role-tab').forEach(tab => {
    tab.addEventListener('click', () => {
      document.querySelectorAll('.role-tab').forEach(t => t.classList.remove('active'));
      tab.classList.add('active');
      selectedRole = tab.dataset.role;

      // Auto-fill demo credentials
      const creds = demoCredentials[selectedRole];
      if (creds) {
        const emailInput = document.querySelector('#loginForm input[type="email"]');
        const passInput  = document.getElementById('passInput');
        if (emailInput) emailInput.value = creds.email;
        if (passInput)  passInput.value  = creds.password;
      }
    });
  });

  // ── Form submit ──────────────────────────────────────────
  const form = document.getElementById('loginForm');
  if (form) {
    form.addEventListener('submit', async (e) => {
      e.preventDefault();

      const emailInput = form.querySelector('input[type="email"]');
      const passInput  = document.getElementById('passInput');
      const loginBtn   = document.getElementById('loginBtn');

      const email    = emailInput?.value?.trim();
      const password = passInput?.value;

      if (!email || !password) {
        showLoginError('Электрондық пошта мен құпия сөзді енгізіңіз');
        return;
      }

      // Show loading state
      if (loginBtn) {
        loginBtn.disabled = true;
        loginBtn.querySelector('.btn-text').textContent = 'Кіруде...';
      }

      try {
        const data = await AuthAPI.login(email, password);
        Auth.save(data);
        redirectToDashboard(data.role);
      } catch (err) {
        console.error('Login error:', err);
        showLoginError(getErrorMessage(err));
      } finally {
        if (loginBtn) {
          loginBtn.disabled = false;
          loginBtn.querySelector('.btn-text').textContent = 'Жүйеге кіру';
        }
      }
    });
  }

  // ── Helpers ───────────────────────────────────────────────
  function redirectToDashboard(role) {
    const roleStr = String(role || '').toUpperCase();
    switch (roleStr) {
      case 'TEACHER': window.location.href = 'pages/teacher-dashboard.html'; break;
      case 'ADMIN':   window.location.href = 'pages/admin-dashboard.html';   break;
      case 'STUDENT':
      default:        window.location.href = 'pages/student-dashboard.html'; break;
    }
  }

  function getErrorMessage(err) {
    const msg = err?.message || '';
    if (msg.includes('401') || msg.includes('Bad credentials') || msg.includes('Unauthorized')) {
      return 'Қате электрондық пошта немесе құпия сөз';
    }
    if (msg.includes('Failed to fetch') || msg.includes('NetworkError')) {
      return 'Сервермен байланыс жоқ. Backend жұмыс істеп тұрғанын тексеріңіз.';
    }
    return msg || 'Кіру кезінде қате орын алды';
  }

  function showLoginError(message) {
    // Remove existing error
    const existing = document.querySelector('.login-error');
    if (existing) existing.remove();

    const errorDiv = document.createElement('div');
    errorDiv.className = 'login-error';
    errorDiv.style.cssText = 'background:rgba(255,50,50,0.1);border:1px solid rgba(255,50,50,0.3);color:#ff5050;padding:10px 14px;border-radius:8px;font-size:0.82rem;margin-bottom:12px;animation:fadeIn 0.3s ease;';
    errorDiv.textContent = '⚠ ' + message;

    const form = document.getElementById('loginForm');
    if (form) form.insertBefore(errorDiv, form.firstChild);

    setTimeout(() => {
      errorDiv.style.opacity = '0';
      errorDiv.style.transition = 'opacity 0.3s ease';
      setTimeout(() => errorDiv.remove(), 300);
    }, 5000);
  }
})();

// ── Password toggle ──────────────────────────────────────────
function togglePass() {
  const input = document.getElementById('passInput');
  if (input) input.type = input.type === 'password' ? 'text' : 'password';
}
