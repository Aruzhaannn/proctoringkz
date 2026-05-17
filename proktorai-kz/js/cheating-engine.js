// CheatEngine — Adaptive Cheating Severity System
// Features: Multi-behavior fusion · Behavior fingerprinting · Soft/Hard lock · Explainable AI

class CheatEngine {
  constructor(opts = {}) {
    this.onRiskChange   = opts.onRiskChange   || (() => {});
    this.onSoftLock     = opts.onSoftLock     || (() => {});
    this.onHardLock     = opts.onHardLock     || (() => {});
    this.onTeacherAlert = opts.onTeacherAlert || (() => {});

    this.riskScore        = 0;
    this._prevLevel       = 'low';
    this.hardLocked       = false;
    this.softLockCount    = 0;
    this.sessionStart     = Date.now();
    this.violationHistory = [];

    // Rolling 30-second event window for multi-behavior fusion
    this._recentEvents = [];
    this._EVENT_WINDOW = 30000;

    this.WEIGHTS = {
      NO_FACE: 40, MULTIPLE_FACES: 60, PERSON_ABSENT: 40, MULTIPLE_PERSONS: 50,
      GAZE_AWAY: 20, HEAD_TURNED: 25, HEAD_NOT_DETECTED: 15,
      PHONE_DETECTED: 70, BOOK_DETECTED: 40,
      VOICE_DETECTED: 30, MULTIPLE_VOICES: 50,
      TAB_SWITCH: 8, COPY_PASTE: 5, WINDOW_MINIMIZED: 30,
    };

    // Dangerous signal combinations → extra fusion bonus
    this.FUSION_COMBOS = [
      { events: ['TAB_SWITCH', 'NO_FACE', 'GAZE_AWAY'],   bonus: 35, label: 'Критикалық комбо: қойынды + бет жоқ + көз бұрылды' },
      { events: ['COPY_PASTE', 'VOICE_DETECTED', 'GAZE_AWAY'], bonus: 28, label: 'Шпаргалка комбосы: көшіру + дыбыс + экраннан алыс' },
      { events: ['PHONE_DETECTED', 'GAZE_AWAY'],          bonus: 22, label: 'Телефон + экраннан алыс қарау' },
      { events: ['MULTIPLE_PERSONS', 'VOICE_DETECTED'],   bonus: 30, label: 'Бөгде адам + дыбыс анықталды' },
      { events: ['TAB_SWITCH', 'COPY_PASTE'],             bonus: 15, label: 'Браузер ауыстыру + мәтін көшіру' },
      { events: ['NO_FACE', 'MULTIPLE_PERSONS'],          bonus: 25, label: 'Бет жоқ + бірнеше адам' },
      { events: ['BOOK_DETECTED', 'GAZE_AWAY'],           bonus: 20, label: 'Кітап + экраннан алыс қарау' },
      { events: ['WINDOW_MINIMIZED', 'COPY_PASTE'],       bonus: 18, label: 'Браузер жасырылды + мәтін көшіру' },
    ];

    // Kazakh explanation labels
    this.LABELS = {
      NO_FACE:          '"Бет анықталмады" — студент камера алдынан кетті',
      MULTIPLE_FACES:   '"Бірнеше бет" — жаныңызда бөгде адам бар',
      PERSON_ABSENT:    '"Адам жоқ" — студент жұмыс орнын тастап кетті',
      MULTIPLE_PERSONS: '"Бірнеше адам" — бөлмеде басқа адам анықталды',
      GAZE_AWAY:        '"Көз бұрылды" — 3+ секунд экраннан тыс қарады',
      HEAD_TURNED:      '"Бас бұрылды" — 30° астам бұрылыс анықталды',
      PHONE_DETECTED:   '"Телефон анықталды" — кадрда электрондық құрылғы бар',
      BOOK_DETECTED:    '"Кітап анықталды" — кадрда жазу материалы бар',
      VOICE_DETECTED:   '"Дыбыс анықталды" — фондық шу немесе сыбыр',
      MULTIPLE_VOICES:  '"Бірнеше дауыс" — бөлмеде бірнеше адам сөйлесуде',
      TAB_SWITCH:       '"Қойынды ауыстырылды" — браузерде басқа бетке өту',
      COPY_PASTE:       '"Ctrl+C/V" — мәтін көшіру немесе қою',
      WINDOW_MINIMIZED: '"Браузер жасырылды" — терезе жасырылды',
    };

    // Behavior fingerprinting
    this.fingerprint = { typingSpeed: 0, mouseSpeed: 0, gazeStability: 100 };
    this._keystrokeTimes = [];
    this._mousePositions = [];
    this._initFingerprinting();

    // Score heatmap: [minute → score]
    this.heatmap = {};
  }

  // ─── RISK LEVELS ────────────────────────────────────────────
  level(score) {
    if (score < 30) return 'low';
    if (score < 60) return 'medium';
    if (score < 85) return 'high';
    return 'critical';
  }

  levelMeta(lv) {
    return {
      low:      { label: '🟢 Төмен қауіп',    color: 'var(--accent-green)',   pct: '0–30%',   action: 'log' },
      medium:   { label: '🟡 Орта қауіп',     color: 'var(--accent-yellow)',  pct: '30–60%',  action: 'soft-lock' },
      high:     { label: '🟠 Жоғары қауіп',   color: '#ff8c00',               pct: '60–85%',  action: 'alert-teacher' },
      critical: { label: '🔴 Критикалық',     color: '#ff3333',               pct: '85–100%', action: 'terminate' },
    }[lv] || { label: '🟢 Төмен қауіп', color: 'var(--accent-green)', pct: '', action: 'log' };
  }

  // ─── ADD VIOLATION EVENT ─────────────────────────────────────
  addEvent(type, details = {}) {
    if (this.hardLocked) return;
    const now = Date.now();

    this._recentEvents.push({ type, time: now, details });
    // Trim to window
    this._recentEvents = this._recentEvents.filter(e => now - e.time < this._EVENT_WINDOW);

    this.violationHistory.push({ type, time: now, details });

    // Heatmap: track per minute
    const minute = Math.floor((now - this.sessionStart) / 60000);
    this.heatmap[minute] = (this.heatmap[minute] || 0) + (this.WEIGHTS[type] || 10);

    this._recalc();
  }

  // ─── MULTI-BEHAVIOR FUSION ────────────────────────────────────
  _recalc() {
    const types = this._recentEvents.map(e => e.type);
    const unique = [...new Set(types)];

    // Base score from individual weights (unique violations only)
    let score = unique.reduce((sum, t) => sum + (this.WEIGHTS[t] || 10), 0);

    // Fusion bonus
    let maxBonus = 0;
    let fusionLabel = '';
    for (const combo of this.FUSION_COMBOS) {
      if (combo.events.every(e => types.includes(e))) {
        if (combo.bonus > maxBonus) { maxBonus = combo.bonus; fusionLabel = combo.label; }
      }
    }
    score += maxBonus;
    score = Math.min(100, score);

    // Smooth transition: blend old score with new (hysteresis)
    this.riskScore = Math.min(100, Math.round(this.riskScore * 0.55 + score * 0.45));

    const newLevel = this.level(this.riskScore);
    const explanation = this._explain(unique, fusionLabel, this.riskScore);

    this.onRiskChange(this.riskScore, newLevel, explanation);

    // Level-based actions
    if (newLevel !== this._prevLevel) {
      this._act(newLevel, explanation);
    }
    this._prevLevel = newLevel;
  }

  _act(lv, explanation) {
    if (lv === 'medium') {
      this.triggerSoftLock('Орта деңгей қауіп анықталды — тексеру жүргізілуде');
    }
    if (lv === 'high') {
      this.triggerSoftLock('Жоғары қауіп — мұғалімге хабарлама жіберілді');
      this.onTeacherAlert(this.riskScore, explanation);
    }
    if (lv === 'critical') {
      this.onTeacherAlert(this.riskScore, explanation);
      this._hardLock(explanation);
    }
  }

  // ─── SOFT LOCK ───────────────────────────────────────────────
  triggerSoftLock(reason) {
    if (this.hardLocked) return;
    this.softLockCount++;
    this.onSoftLock(reason, this.softLockCount);
  }

  // ─── HARD LOCK ───────────────────────────────────────────────
  _hardLock(explanation) {
    if (this.hardLocked) return;
    this.hardLocked = true;
    this.onHardLock(explanation);
  }

  forceHardLock(reason) {
    if (this.hardLocked) return;
    this.hardLocked = true;
    this.onHardLock(reason);
  }

  // ─── EXPLAINABLE AI ──────────────────────────────────────────
  _explain(uniqueTypes, fusionLabel, score) {
    const lines = uniqueTypes.slice(0, 4).map(t => '• ' + (this.LABELS[t] || t));
    if (fusionLabel) lines.push('⚡ Комбо: ' + fusionLabel);
    lines.push(`📊 Қауіп баллы: ${score}/100`);
    return lines.join('\n');
  }

  explainCurrent() {
    const types = [...new Set(this._recentEvents.map(e => e.type))];
    let fusionLabel = '';
    for (const combo of this.FUSION_COMBOS) {
      if (combo.events.every(e => types.includes(e))) { fusionLabel = combo.label; break; }
    }
    return this._explain(types, fusionLabel, this.riskScore);
  }

  // ─── BEHAVIOR FINGERPRINTING ──────────────────────────────────
  _initFingerprinting() {
    document.addEventListener('keydown', () => {
      const now = Date.now();
      this._keystrokeTimes.push(now);
      if (this._keystrokeTimes.length > 30) this._keystrokeTimes.shift();
      this._updateTypingSpeed();
    });

    document.addEventListener('mousemove', (e) => {
      this._mousePositions.push({ x: e.clientX, y: e.clientY, t: Date.now() });
      if (this._mousePositions.length > 60) this._mousePositions.shift();
      this._updateMouseSpeed();
    });
  }

  _updateTypingSpeed() {
    const t = this._keystrokeTimes;
    if (t.length < 3) return;
    const intervals = [];
    for (let i = 1; i < t.length; i++) intervals.push(t[i] - t[i-1]);
    const avg = intervals.reduce((a, b) => a + b, 0) / intervals.length;
    // 60-600ms → speed 1-100
    this.fingerprint.typingSpeed = Math.round(Math.max(1, Math.min(100, 100 - (avg - 60) / 5.4)));
  }

  _updateMouseSpeed() {
    const p = this._mousePositions;
    if (p.length < 2) return;
    const last = p[p.length-1], prev = p[p.length-2];
    const dt = last.t - prev.t;
    if (dt < 1) return;
    const speed = Math.sqrt((last.x-prev.x)**2 + (last.y-prev.y)**2) / dt * 100;
    this.fingerprint.mouseSpeed = Math.round(this.fingerprint.mouseSpeed * 0.85 + speed * 0.15);
  }

  updateGazeStability(stable) {
    const target = stable ? 100 : 50;
    this.fingerprint.gazeStability = Math.round(this.fingerprint.gazeStability * 0.9 + target * 0.1);
  }

  getFingerprint() { return { ...this.fingerprint }; }

  // ─── SCORE DECAY ────────────────────────────────────────────
  decay() {
    if (this.hardLocked || this.riskScore <= 0) return;
    this.riskScore = Math.max(0, this.riskScore - 3);
    const lv = this.level(this.riskScore);
    this.onRiskChange(this.riskScore, lv, null);
  }

  // ─── HEATMAP DATA ───────────────────────────────────────────
  getHeatmap() { return { ...this.heatmap }; }

  getStats() {
    return {
      riskScore: this.riskScore,
      riskLevel: this.level(this.riskScore),
      softLockCount: this.softLockCount,
      hardLocked: this.hardLocked,
      totalViolations: this.violationHistory.length,
      durationSec: Math.round((Date.now() - this.sessionStart) / 1000),
      fingerprint: this.fingerprint,
    };
  }
}