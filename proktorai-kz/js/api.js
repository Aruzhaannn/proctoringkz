// Docker-да nginx proxy арқылы, local-да тікелей
const IS_DOCKER  = window.location.port === '80' || window.location.port === '';
const API_BASE   = IS_DOCKER ? '/api/v1'              : 'http://localhost:8080/api/v1';
const AI_BASE    = IS_DOCKER ? '/ai'                  : 'http://localhost:8000/api/v1';

// ── Token helpers ─────────────────────────────────────────────
const Auth = {
  save(data) {
    localStorage.setItem('accessToken',  data.accessToken);
    localStorage.setItem('refreshToken', data.refreshToken);
    localStorage.setItem('user', JSON.stringify({
      id: data.userId, email: data.email,
      fullName: data.fullName, role: data.role
    }));
  },
  token()   { return localStorage.getItem('accessToken'); },
  user()    { const u = localStorage.getItem('user'); return u ? JSON.parse(u) : null; },
  role()    { const u = Auth.user(); return u ? u.role : null; },
  clear()   { localStorage.removeItem('accessToken'); localStorage.removeItem('refreshToken'); localStorage.removeItem('user'); },
  check()   {
    if (!Auth.token()) {
      const inPages = window.location.pathname.includes('/pages/');
      window.location.href = inPages ? '../index.html' : 'index.html';
      return false;
    }
    return true;
  }
};

// ── Generic fetch wrapper ─────────────────────────────────────
let _refreshing = false;
async function apiFetch(url, options = {}, _retry = false) {
  const headers = { 'Content-Type': 'application/json', ...options.headers };
  if (Auth.token()) headers['Authorization'] = 'Bearer ' + Auth.token();

  const res = await fetch(url, { ...options, headers });

  if (res.status === 401 && !_retry && !_refreshing) {
    const refreshToken = localStorage.getItem('refreshToken');
    if (refreshToken && refreshToken !== 'demo-refresh') {
      _refreshing = true;
      try {
        const r = await fetch(`${API_BASE}/auth/refresh`, {
          method: 'POST', headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ refreshToken })
        });
        if (r.ok) {
          const data = await r.json();
          Auth.save(data);
          _refreshing = false;
          return apiFetch(url, options, true);
        }
      } catch (_) {}
      _refreshing = false;
    }
    Auth.clear(); window.location.href = '/index.html'; return;
  }
  if (!res.ok) {
    const err = await res.text();
    throw new Error(err || `HTTP ${res.status}`);
  }
  const text = await res.text();
  return text ? JSON.parse(text) : null;
}

// ── Auth API ─────────────────────────────────────────────────
const AuthAPI = {
  login:    (email, password) => apiFetch(`${API_BASE}/auth/login`,    { method:'POST', body: JSON.stringify({email, password}) }),
  register: (data)            => apiFetch(`${API_BASE}/auth/register`, { method:'POST', body: JSON.stringify(data) }),
  me:       ()                => apiFetch(`${API_BASE}/auth/me`),
};

// ── Exam API ─────────────────────────────────────────────────
const ExamAPI = {
  getAll:     ()       => apiFetch(`${API_BASE}/exams`),
  getActive:  ()       => apiFetch(`${API_BASE}/exams/active`),
  getById:    (id)     => apiFetch(`${API_BASE}/exams/${id}`),
  getMine:    ()       => apiFetch(`${API_BASE}/exams/my`),
  create:     (data)   => apiFetch(`${API_BASE}/exams`,            { method:'POST', body: JSON.stringify(data) }),
  activate:   (id)     => apiFetch(`${API_BASE}/exams/${id}/activate`, { method:'PATCH' }),
  finish:     (id)     => apiFetch(`${API_BASE}/exams/${id}/finish`,   { method:'PATCH' }),
};

// ── Session API ───────────────────────────────────────────────
const SessionAPI = {
  start:         (examId)  => apiFetch(`${API_BASE}/sessions/start/${examId}`, { method:'POST' }),
  finish:        (id)      => apiFetch(`${API_BASE}/sessions/${id}/finish`,    { method:'PATCH' }),
  getMy:         ()        => apiFetch(`${API_BASE}/sessions/my`),
  getByExam:     (examId)  => apiFetch(`${API_BASE}/sessions/exam/${examId}`),
  addViolation:  (data)    => apiFetch(`${API_BASE}/sessions/violations`, { method:'POST', body: JSON.stringify(data) }),
  phoneUnlock:   (id)      => apiFetch(`${API_BASE}/sessions/${id}/phone-unlock`, { method:'PATCH' }),
  phoneLock:     (id)      => apiFetch(`${API_BASE}/sessions/${id}/phone-lock`,   { method:'PATCH' }),
};

// ── Audit Log API ────────────────────────────────────────────
const AuditAPI = {
  log: (action, sessionId, details) => apiFetch(`${API_BASE}/audit`, {
    method: 'POST',
    body: JSON.stringify({ action, sessionId, details, browserInfo: navigator.userAgent.substring(0, 200) })
  }).catch(() => {}),
  getAll:       ()   => apiFetch(`${API_BASE}/audit`),
  getBySession: (id) => apiFetch(`${API_BASE}/audit/session/${id}`),
};

// ── Analytics API ─────────────────────────────────────────────
const ANALYTICS_BASE = IS_DOCKER ? '/api/v1/analytics' : 'http://localhost:8082/api/v1/analytics';
const AnalyticsAPI = {
  getDashboard:    ()           => apiFetch(`${ANALYTICS_BASE}/dashboard`),
  getAllExams:      ()           => apiFetch(`${ANALYTICS_BASE}/exams`),
  getExam:         (id)         => apiFetch(`${ANALYTICS_BASE}/exams/${id}`),
  getAllStudents:   ()           => apiFetch(`${ANALYTICS_BASE}/students`),
  getHighRisk:     ()           => apiFetch(`${ANALYTICS_BASE}/students/high-risk`),
  getViolations:   ()           => apiFetch(`${ANALYTICS_BASE}/violations/summary`),
};

// ── AI Service ────────────────────────────────────────────────
const AiAPI = {
  async analyzeFrame(sessionId, blob, { tabSwitches = 0, copyPasteCount = 0, windowMinimized = 0, gazeBaselineH = 0.0, gazeBaselineV = 0.0 } = {}) {
    const fd = new FormData();
    fd.append('session_id', String(sessionId));
    fd.append('frame', blob, 'frame.jpg');
    fd.append('tab_switches', String(tabSwitches));
    fd.append('copy_paste_count', String(copyPasteCount));
    fd.append('window_minimized', String(windowMinimized));
    fd.append('gaze_baseline_h', String(gazeBaselineH));
    fd.append('gaze_baseline_v', String(gazeBaselineV));
    const res = await fetch(`${AI_BASE}/analyze`, {
      method: 'POST', body: fd
    });
    if (!res.ok) return null;
    return res.json();
  },
  async analyzeAudio(sessionId, blob) {
    const fd = new FormData();
    fd.append('session_id', String(sessionId));
    fd.append('audio', blob, 'audio.wav');
    const res = await fetch(`${AI_BASE}/analyze/audio`, {
      method: 'POST', body: fd
    });
    if (!res.ok) return null;
    return res.json();
  }
};