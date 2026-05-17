// EvidenceCollector — Screenshot capture · Video buffer · Evidence timeline · PDF generation
// Uses jsPDF (loaded from CDN in exam-room.html)

class EvidenceCollector {
  constructor(videoEl) {
    this.videoEl    = videoEl;
    this.timeline   = [];
    this._canvas    = document.createElement('canvas');
    this._canvas.width = 320;
    this._canvas.height = 240;

    // Rolling video buffer (MediaRecorder, 1-second chunks, keep ~15s)
    this._recorder  = null;
    this._buffer    = [];  // { data: Blob, time: number }
  }

  // Call once camera stream is available
  startBuffer(stream) {
    if (!stream || !window.MediaRecorder) return;
    let opts = null;
    for (const mime of ['video/webm;codecs=vp8', 'video/webm', '']) {
      if (!mime || MediaRecorder.isTypeSupported(mime)) { opts = mime ? { mimeType: mime } : {}; break; }
    }
    try {
      this._recorder = new MediaRecorder(stream, opts);
      this._recorder.ondataavailable = (e) => {
        if (e.data && e.data.size > 0) {
          this._buffer.push({ data: e.data, time: Date.now() });
          const cutoff = Date.now() - 15000;
          this._buffer = this._buffer.filter(c => c.time > cutoff);
        }
      };
      this._recorder.start(1000);
    } catch(e) {
      console.warn('EvidenceCollector: recorder init failed', e);
    }
  }

  // Capture JPEG screenshot from video feed
  screenshot() {
    try {
      this._canvas.getContext('2d').drawImage(this.videoEl, 0, 0, 320, 240);
      return this._canvas.toDataURL('image/jpeg', 0.75);
    } catch { return null; }
  }

  // Get last ~5s video clip as Blob
  clip() {
    const chunks = this._buffer.filter(c => c.time > Date.now() - 5000).map(c => c.data);
    if (!chunks.length) return null;
    return new Blob(chunks, { type: 'video/webm' });
  }

  // Record a violation evidence entry
  record(violationType, riskScore, riskLevel, explanation) {
    const now = new Date();
    const entry = {
      id:           Date.now(),
      timestamp:    now,
      timeStr:      now.toLocaleTimeString('kk-KZ'),
      violationType,
      riskScore,
      riskLevel,
      explanation,
      screenshot:   this.screenshot(),
      clip:         this.clip(),
    };
    this.timeline.push(entry);
    if (this.timeline.length > 60) this.timeline.shift();
    return entry;
  }

  count()          { return this.timeline.length; }
  getTimeline()    { return [...this.timeline]; }
  shouldMakePDF()  { return this.timeline.length >= 3; }

  // ─── FORENSIC HASH ─────────────────────────────────────────
  async _hash(str) {
    try {
      const buf = await crypto.subtle.digest('SHA-256', new TextEncoder().encode(str));
      return Array.from(new Uint8Array(buf)).map(b => b.toString(16).padStart(2,'0')).join('');
    } catch { return 'unavailable'; }
  }

  async forensicLog() {
    const log = this.timeline.map(e => ({
      id: e.id, timestamp: e.timestamp.toISOString(),
      type: e.violationType, score: e.riskScore, level: e.riskLevel,
    }));
    const hash = await this._hash(JSON.stringify(log));
    return {
      version: '1.0',
      generatedAt: new Date().toISOString(),
      entries: log,
      integrity: { hash, algorithm: 'SHA-256', count: log.length },
    };
  }

  // ─── TRANSLITERATION (Cyrillic → Latin for PDF) ─────────────
  _translit(text) {
    if (!text) return '';
    const map = {
      'А':'A','Ә':'A','Б':'B','В':'V','Г':'G','Ғ':'G','Д':'D','Е':'E','Ё':'Yo',
      'Ж':'Zh','З':'Z','И':'I','Й':'Y','К':'K','Қ':'Q','Л':'L','М':'M','Н':'N',
      'Ң':'N','О':'O','Ө':'O','П':'P','Р':'R','С':'S','Т':'T','У':'U','Ұ':'U',
      'Ү':'U','Ф':'F','Х':'Kh','Һ':'H','Ц':'Ts','Ч':'Ch','Ш':'Sh','Щ':'Shch',
      'Ъ':'','Ы':'Y','І':'I','Ь':'','Э':'E','Ю':'Yu','Я':'Ya',
      'а':'a','ә':'a','б':'b','в':'v','г':'g','ғ':'g','д':'d','е':'e','ё':'yo',
      'ж':'zh','з':'z','и':'i','й':'y','к':'k','қ':'q','л':'l','м':'m','н':'n',
      'ң':'n','о':'o','ө':'o','п':'p','р':'r','с':'s','т':'t','у':'u','ұ':'u',
      'ү':'u','ф':'f','х':'kh','һ':'h','ц':'ts','ч':'ch','ш':'sh','щ':'shch',
      'ъ':'','ы':'y','і':'i','ь':'','э':'e','ю':'yu','я':'ya',
    };
    return String(text).split('').map(c => map[c] || c).join('');
  }

  // ─── PDF REPORT ─────────────────────────────────────────────
  async makePDF(student, exam) {
    const lib = (typeof window.jspdf !== 'undefined') ? window.jspdf :
                (typeof window.jsPDF !== 'undefined') ? { jsPDF: window.jsPDF } : null;
    if (!lib) { console.warn('jsPDF not loaded'); return null; }

    const { jsPDF } = lib;
    const doc = new jsPDF({ unit: 'mm', format: 'a4' });
    const T = (s) => this._translit(s); // shorthand

    const R = [220, 50, 50], O = [255, 140, 0], G = [45, 190, 140],
          GR = [100, 100, 100], DK = [25, 28, 42], LB = [248, 249, 255];

    // ── Header ──────────────────────────────────────────────
    doc.setFillColor(...DK);
    doc.rect(0, 0, 210, 42, 'F');
    doc.setTextColor(255, 255, 255);
    doc.setFontSize(22); doc.setFont('helvetica', 'bold');
    doc.text('ProctorAI', 14, 18);
    doc.setFontSize(11); doc.setFont('helvetica', 'normal');
    doc.text('Buzushylyk Eseby — Avtomatty', 14, 27);
    doc.setFontSize(8);
    doc.text(new Date().toLocaleString('ru-RU'), 14, 36);

    const maxScore = this.timeline.reduce((m, e) => Math.max(m, e.riskScore), 0);
    const verdict  = maxScore >= 85 ? 'ALAYAQTYK ANYKTALDY' :
                     maxScore >= 60 ? 'KUYALI AREKETTER BAR' : 'TEKSERU USYNYLADY';
    const vc = maxScore >= 85 ? R : maxScore >= 60 ? O : [200, 160, 0];
    doc.setFontSize(11); doc.setFont('helvetica', 'bold');
    doc.setTextColor(...vc);
    doc.text(verdict, 135, 22);
    doc.setFontSize(9); doc.setFont('helvetica', 'normal');
    doc.setTextColor(180, 180, 200);
    doc.text(`Qauip: ${maxScore}%`, 135, 30);

    let y = 52;

    // ── Student/Exam Info ────────────────────────────────────
    doc.setFillColor(...LB);
    doc.roundedRect(10, y, 90, 52, 3, 3, 'F');
    doc.roundedRect(108, y, 92, 52, 3, 3, 'F');

    doc.setFontSize(9); doc.setFont('helvetica', 'bold'); doc.setTextColor(...DK);
    doc.text('STUDENT', 15, y + 8);
    doc.setFont('helvetica', 'normal'); doc.setTextColor(...GR); doc.setFontSize(8);
    [['Aty-joni:', T(student.name) || 'Belgisiz'],
     ['Email:',   student.email || '-'],
     ['ID:',      String(student.id || '-')]].forEach(([k, v], i) => {
      doc.setFont('helvetica', 'bold'); doc.setTextColor(...DK);
      doc.text(k, 15, y + 16 + i * 10);
      doc.setFont('helvetica', 'normal'); doc.setTextColor(...GR);
      doc.text(String(v), 40, y + 16 + i * 10);
    });

    doc.setFontSize(9); doc.setFont('helvetica', 'bold'); doc.setTextColor(...DK);
    doc.text('EMTIXAN', 113, y + 8);
    doc.setFont('helvetica', 'normal'); doc.setTextColor(...GR); doc.setFontSize(8);
    [['Atauhy:', T(exam.title) || 'Belgisiz'],
     ['Kuni:',   exam.date  || new Date().toLocaleDateString('ru-RU')],
     ['Uaqyt:',  exam.startTime || '-']].forEach(([k, v], i) => {
      doc.setFont('helvetica', 'bold'); doc.setTextColor(...DK);
      doc.text(k, 113, y + 16 + i * 10);
      doc.setFont('helvetica', 'normal'); doc.setTextColor(...GR);
      doc.text(String(v).substring(0, 30), 133, y + 16 + i * 10);
    });

    y += 62;

    // ── Summary Stats ────────────────────────────────────────
    const critCount = this.timeline.filter(e => e.riskLevel === 'critical').length;
    const highCount = this.timeline.filter(e => e.riskLevel === 'high').length;
    const stats = [
      ['Jalpy buzushylyk:', String(this.timeline.length), DK],
      ['Kritikalyk:',       String(critCount),             R],
      ['Zhogary qauip:',   String(highCount),             O],
      ['Max score:',        `${maxScore}%`,                vc],
    ];

    doc.setFillColor(255, 242, 242);
    doc.roundedRect(10, y, 190, 22, 3, 3, 'F');
    stats.forEach(([k, v, c], i) => {
      const x = 15 + i * 47;
      doc.setFontSize(7); doc.setFont('helvetica', 'normal'); doc.setTextColor(...GR);
      doc.text(k, x, y + 8);
      doc.setFontSize(12); doc.setFont('helvetica', 'bold'); doc.setTextColor(...c);
      doc.text(v, x, y + 18);
    });

    y += 32;

    // ── Violations List ──────────────────────────────────────
    doc.setFontSize(11); doc.setFont('helvetica', 'bold'); doc.setTextColor(...DK);
    doc.text('Buzushylyqtar tizimy', 14, y);
    y += 8;

    for (let i = 0; i < Math.min(this.timeline.length, 18); i++) {
      if (y > 240) { doc.addPage(); y = 20; }
      const ev = this.timeline[i];
      const lc = ev.riskLevel === 'critical' ? R : ev.riskLevel === 'high' ? O :
                 ev.riskLevel === 'medium' ? [200, 160, 0] : G;
      doc.setFillColor(250, 250, 255);
      doc.roundedRect(10, y, 190, 20, 2, 2, 'F');
      doc.setFillColor(...lc);
      doc.rect(10, y, 3, 20, 'F');

      doc.setFontSize(9); doc.setFont('helvetica', 'bold'); doc.setTextColor(...lc);
      doc.text(`${i+1}. ${T(ev.violationType)}`, 17, y + 8);
      doc.setFontSize(7); doc.setFont('helvetica', 'normal'); doc.setTextColor(...GR);
      doc.text(ev.timeStr, 160, y + 8);
      doc.text(`Score: ${ev.riskScore}%  |  ${ev.riskLevel.toUpperCase()}`, 17, y + 16);
      y += 24;
    }

    y += 4;

    // ── Screenshots ──────────────────────────────────────────
    const shots = this.timeline.filter(e => e.screenshot).slice(0, 8);
    if (shots.length) {
      if (y > 200) { doc.addPage(); y = 20; }
      doc.setFontSize(11); doc.setFont('helvetica', 'bold'); doc.setTextColor(...DK);
      doc.text('Skrinshot Dalelderi', 14, y);
      y += 8;

      let xp = 14;
      shots.forEach((ev, i) => {
        if (xp + 56 > 210) { xp = 14; y += 52; }
        if (y > 240) { doc.addPage(); y = 20; xp = 14; }
        try {
          doc.addImage(ev.screenshot, 'JPEG', xp, y, 54, 38);
          doc.setFontSize(6); doc.setTextColor(...GR);
          doc.text(ev.timeStr, xp, y + 41);
        } catch {}
        xp += 60;
      });
      y += 52;
    }

    // ── AI Conclusion ────────────────────────────────────────
    if (y > 250) { doc.addPage(); y = 20; }
    doc.setFontSize(11); doc.setFont('helvetica', 'bold'); doc.setTextColor(...DK);
    doc.text('AI Qorytyndysy', 14, y);
    y += 8;
    doc.setFillColor(255, 245, 245);
    doc.roundedRect(10, y, 190, 26, 3, 3, 'F');
    doc.setFontSize(13); doc.setFont('helvetica', 'bold'); doc.setTextColor(...vc);
    doc.text(verdict, 14, y + 10);
    doc.setFontSize(8); doc.setFont('helvetica', 'normal'); doc.setTextColor(...GR);
    doc.text(`Alayaqtyk yktymaldygy: ${maxScore}%  |  Buzushylyk sany: ${this.timeline.length}  |  ProctorAI v1.0`, 14, y + 20);

    // ── Forensic Footer ──────────────────────────────────────
    const flog = await this.forensicLog();
    doc.setFontSize(6); doc.setTextColor(150, 150, 160);
    doc.text(`Integrity Hash (SHA-256): ${flog.integrity.hash.substring(0, 40)}...`, 14, 288);
    doc.text(`Generated: ${flog.generatedAt}  |  Entries: ${flog.integrity.count}  |  ProctorAI Forensic Audit v1.0`, 14, 293);

    return doc;
  }

  async downloadPDF(student, exam) {
    const doc = await this.makePDF(student, exam);
    if (!doc) return false;
    const name = `proktorai_${(student.name || 'student').replace(/\s+/g,'_')}_${Date.now()}.pdf`;
    doc.save(name);
    return true;
  }
}