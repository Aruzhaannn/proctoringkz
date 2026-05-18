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

// ── Demo mode local data store ────────────────────────────────
const _demoStore = {
  exams: JSON.parse(localStorage.getItem('_demoExams') || '[]'),
  _nextId: parseInt(localStorage.getItem('_demoNextId') || '100'),
  _save() {
    localStorage.setItem('_demoExams', JSON.stringify(this.exams));
    localStorage.setItem('_demoNextId', String(this._nextId));
  }
};

function _demoHandler(url, options = {}) {
  const method = (options.method || 'GET').toUpperCase();
  const body = options.body ? JSON.parse(options.body) : {};
  const path = url.replace(API_BASE, '').replace(ANALYTICS_BASE || '', '');

  // ── Exams ────────────────────────────────────────────────
  if (path === '/exams' && method === 'GET')        return _demoStore.exams;
  if (path === '/exams/my' && method === 'GET')      return _demoStore.exams;
  if (path === '/exams/active' && method === 'GET')  return _demoStore.exams.filter(e => e.status === 'ACTIVE');
  if (path.match(/^\/exams\/\d+$/) && method === 'GET') {
    const id = parseInt(path.split('/').pop());
    return _demoStore.exams.find(e => e.id === id) || {};
  }
  if (path === '/exams' && method === 'POST') {
    const exam = {
      id: _demoStore._nextId++,
      title: body.title || 'Жаңа емтихан',
      description: body.description || '',
      durationMinutes: body.durationMinutes || 60,
      status: 'PLANNED',
      createdByName: Auth.user()?.fullName || 'Оқытушы',
      createdAt: new Date().toISOString()
    };
    _demoStore.exams.push(exam);
    _demoStore._save();
    return exam;
  }
  if (path.match(/\/exams\/\d+\/activate/) && method === 'PATCH') {
    const id = parseInt(path.split('/')[2]);
    const exam = _demoStore.exams.find(e => e.id === id);
    if (exam) { exam.status = 'ACTIVE'; _demoStore._save(); }
    return exam || {};
  }
  if (path.match(/\/exams\/\d+\/finish/) && method === 'PATCH') {
    const id = parseInt(path.split('/')[2]);
    const exam = _demoStore.exams.find(e => e.id === id);
    if (exam) { exam.status = 'FINISHED'; _demoStore._save(); }
    return exam || {};
  }

  // ── Sessions ─────────────────────────────────────────────
  if (path.includes('/sessions'))  return method === 'GET' ? [] : {};

  // ── Audit ────────────────────────────────────────────────
  if (path.includes('/audit'))     return method === 'GET' ? [] : {};

  // ── Analytics ────────────────────────────────────────────
  if (path.includes('/analytics') || path.includes('/dashboard'))
    return method === 'GET' ? [] : {};

  // ── Default ──────────────────────────────────────────────
  return method === 'GET' ? [] : {};
}

// ── Generic fetch wrapper ─────────────────────────────────────
let _refreshing = false;
async function apiFetch(url, options = {}, _retry = false) {
  // ── Demo mode: work with local data without backend ─────────
  const currentToken = Auth.token();
  if (currentToken === 'demo-token' && !url.includes('/auth/login')) {
    return _demoHandler(url, options);
  }

  const headers = { ...options.headers };
  if (!(options.body instanceof FormData)) {
      headers['Content-Type'] = headers['Content-Type'] || 'application/json';
  }
  if (currentToken) headers['Authorization'] = 'Bearer ' + currentToken;

  const res = await fetch(url, { ...options, headers });

  if (res.status === 401 && !_retry && !_refreshing) {
    if (url.includes('/auth/login')) {
      const err = await res.text();
      throw new Error(err || `HTTP ${res.status}`);
    }

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
    Auth.clear();
    const inPages = window.location.pathname.includes('/pages/');
    window.location.href = inPages ? '../index.html' : 'index.html';
    return;
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

// ── User API ─────────────────────────────────────────────────
const UserAPI = {
  getStudents: () => apiFetch(`${API_BASE}/users/students`),
  getAll:      () => apiFetch(`${API_BASE}/users`)
};

// ── Group API ────────────────────────────────────────────────
const GroupAPI = {
  getAll:        ()          => apiFetch(`${API_BASE}/groups`),
  create:        (name)      => apiFetch(`${API_BASE}/groups`, { method:'POST', body: JSON.stringify({name}) }),
  addStudents:   (id, ids)   => apiFetch(`${API_BASE}/groups/${id}/students`, { method:'POST', body: JSON.stringify({studentIds: ids}) })
};

// ── Exam API ─────────────────────────────────────────────────
const ExamAPI = {
  getAll:         ()         => apiFetch(`${API_BASE}/exams`),
  getActive:      ()         => apiFetch(`${API_BASE}/exams/active`),
  getById:        (id)       => apiFetch(`${API_BASE}/exams/${id}`),
  getMine:        ()         => apiFetch(`${API_BASE}/exams/my`),
  create:         (data)     => apiFetch(`${API_BASE}/exams`,            { method:'POST', body: JSON.stringify(data) }),
  createWithFile: (formData) => apiFetch(`${API_BASE}/exams/with-file`,  { method:'POST', body: formData }),
  activate:       (id)       => apiFetch(`${API_BASE}/exams/${id}/activate`, { method:'PATCH' }),
  finish:         (id)       => apiFetch(`${API_BASE}/exams/${id}/finish`,   { method:'PATCH' }),
};

// ── Session API ───────────────────────────────────────────────
const SessionAPI = {
  start:         (examId)        => apiFetch(`${API_BASE}/sessions/start/${examId}`, { method:'POST' }),
  finish:        (id, answers)   => apiFetch(`${API_BASE}/sessions/${id}/finish`,    { method:'PATCH', body: answers ? JSON.stringify({answers}) : null }),
  getMy:         ()        => apiFetch(`${API_BASE}/sessions/my`),
  getByExam:     (examId)  => apiFetch(`${API_BASE}/sessions/exam/${examId}`),
  getViolations: (id)      => apiFetch(`${API_BASE}/sessions/${id}/violations`),
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