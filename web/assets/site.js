/* המתכונים של תמר — shared behavior (no dependencies). */
(function () {
  'use strict';

  // ---------- helpers ----------
  function norm(s) {
    return (s || '').toLowerCase()
      .replace(/[֑-ׇ]/g, '')          // nikud / cantillation
      .replace(/[׳'`´’״"]/g, '')               // geresh / gershayim / quotes
      .replace(/[-–—_.,:;!?()]/g, ' ')
      .replace(/\s+/g, ' ').trim();
  }
  function variants(token) {
    var v = [token];
    if (token.length > 2 && /ה$/.test(token)) v.push(token.slice(0, -1) + 'ת');
    if (token.length > 2 && /ת$/.test(token)) v.push(token.slice(0, -1) + 'ה');
    return v;
  }
  function store(key, val) {
    try {
      if (val === undefined) return JSON.parse(localStorage.getItem(key)) || {};
      localStorage.setItem(key, JSON.stringify(val));
    } catch (e) { return {}; }
  }
  var reduceMotion = window.matchMedia && matchMedia('(prefers-reduced-motion: reduce)').matches;
  var MADE_KEY = 'tamar.made';

  // ---------- filter + search ----------
  var grid = document.querySelector('[data-grid]');
  if (grid) {
    var cards = [].slice.call(grid.querySelectorAll('.card'));
    var chips = [].slice.call(document.querySelectorAll('.chip[data-filter]'));
    var q = document.getElementById('q');
    var countEl = document.querySelector('[data-count]');
    var emptyEl = document.querySelector('[data-empty]');
    var state = { cat: 'all', q: '' };

    var params = new URLSearchParams(location.hash.slice(1));
    if (params.get('cat')) state.cat = params.get('cat');
    if (params.get('q')) state.q = params.get('q');
    if (q) q.value = state.q;

    function apply(updateHash) {
      var tokens = norm(state.q).split(' ').filter(Boolean);
      var shown = 0;
      cards.forEach(function (c) {
        var okCat = state.cat === 'all' || c.getAttribute('data-cat') === state.cat;
        var hay = c.getAttribute('data-search') || '';
        var okText = tokens.every(function (t) {
          return variants(t).some(function (v) { return hay.indexOf(v) > -1; });
        });
        var on = okCat && okText;
        c.hidden = !on;
        if (on) shown++;
      });
      chips.forEach(function (ch) {
        ch.setAttribute('aria-pressed', ch.getAttribute('data-filter') === state.cat ? 'true' : 'false');
      });
      if (countEl) countEl.textContent = shown === cards.length ? cards.length + ' מתכונים' : 'נמצאו ' + shown + ' מתכונים';
      if (emptyEl) emptyEl.classList.toggle('show', shown === 0);
      if (updateHash) {
        var p = new URLSearchParams();
        if (state.cat !== 'all') p.set('cat', state.cat);
        if (state.q) p.set('q', state.q);
        var h = p.toString();
        history.replaceState(null, '', h ? '#' + h : location.pathname + location.search);
      }
    }
    chips.forEach(function (ch) {
      ch.addEventListener('click', function () { state.cat = ch.getAttribute('data-filter'); apply(true); });
    });
    if (q) q.addEventListener('input', function () { state.q = q.value; apply(true); });
    apply(false);
  }

  // ---------- "made it" marks on cards ----------
  var made = store(MADE_KEY);
  [].forEach.call(document.querySelectorAll('.card[data-id]'), function (c) {
    if (made[c.getAttribute('data-id')]) {
      var m = document.createElement('span');
      m.className = 'made-mark';
      m.textContent = '✓ הכנתי';
      c.appendChild(m);
    }
  });

  // ---------- surprise me ----------
  var spin = document.querySelector('[data-surprise]');
  if (spin) {
    var out = document.querySelector('[data-surprise-out]');
    spin.addEventListener('click', function () {
      var pool = [].filter.call(document.querySelectorAll('[data-grid] .card'), function (c) { return !c.hidden; });
      if (!pool.length) pool = [].slice.call(document.querySelectorAll('[data-grid] .card'));
      if (!pool.length) return;
      var pick = pool[Math.floor(Math.random() * pool.length)];
      var steps = reduceMotion ? 0 : 12, i = 0;
      spin.disabled = true;
      out.setAttribute('aria-live', 'off');
      (function tick() {
        if (i++ < steps) {
          out.textContent = pool[Math.floor(Math.random() * pool.length)].querySelector('h3').textContent;
          return setTimeout(tick, 50 + i * 15);
        }
        out.setAttribute('aria-live', 'polite');
        out.textContent = 'היום מבשלים: ';
        var a = document.createElement('a');
        a.href = pick.getAttribute('href');
        a.textContent = pick.querySelector('h3').textContent + ' ←';
        out.appendChild(a);
        spin.textContent = '🎲 עוד הצעה';
        spin.disabled = false;
      })();
    });
  }

  // ---------- recipe page ----------
  var page = document.body.getAttribute('data-page');
  if (page === 'recipe') {
    var id = document.body.getAttribute('data-id');
    var title = document.querySelector('h1').textContent;

    // back: return to the list (keeps filter + scroll) when we came from this site
    var back = document.querySelector('[data-back]');
    if (back) back.addEventListener('click', function (e) {
      try {
        if (document.referrer && new URL(document.referrer).origin === location.origin && history.length > 1) {
          e.preventDefault(); history.back();
        }
      } catch (err) {}
    });

    // cooking mode
    var cookBtn = document.querySelector('[data-cook]');
    if (cookBtn && window.HTMLDialogElement) {
      var dlg = document.createElement('dialog');
      dlg.className = 'cook';
      dlg.setAttribute('aria-label', 'מצב בישול: ' + title);
      dlg.innerHTML = '<div class="cook-bar"><span class="t"></span><span class="note" role="status"></span>' +
        '<button type="button" class="btn">✕ סגירה</button></div><div class="cook-scroll"><img alt=""></div>';
      dlg.querySelector('.t').textContent = title;
      var big = dlg.querySelector('img'), note = dlg.querySelector('.note'), lock = null;
      var scan = document.querySelector('figure.scan img');
      big.alt = scan ? scan.alt : '';
      big.title = 'הקישו להגדלה';
      var tr = document.querySelector('.transcript');
      if (tr) dlg.querySelector('.cook-scroll').appendChild(tr.cloneNode(true));
      document.body.appendChild(dlg);
      function awake() {
        if ('wakeLock' in navigator) navigator.wakeLock.request('screen').then(function (l) {
          lock = l; note.textContent = '☀️ המסך יישאר דלוק';
        }, function () {});
      }
      cookBtn.addEventListener('click', function () {
        big.src = cookBtn.getAttribute('data-src');
        dlg.showModal(); awake();
      });
      big.addEventListener('click', function () { big.classList.toggle('zoomed'); });
      dlg.querySelector('.cook-bar .btn').addEventListener('click', function () { dlg.close(); });
      dlg.addEventListener('close', function () { if (lock) { lock.release(); lock = null; } note.textContent = ''; cookBtn.focus(); });
      document.addEventListener('visibilitychange', function () { if (dlg.open && !document.hidden) awake(); });
    } else if (cookBtn) {
      cookBtn.addEventListener('click', function () { location.href = cookBtn.getAttribute('data-src'); });
    }

    // made it
    var madeBtn = document.querySelector('[data-made]');
    var madeMsg = document.querySelector('[data-made-msg]');
    function renderMade(cheer) {
      var m = store(MADE_KEY), d = m[id];
      madeBtn.setAttribute('aria-pressed', d ? 'true' : 'false');
      madeBtn.textContent = d ? '✓ הכנתי (' + d + ')' : '✓ הכנתי את זה!';
      madeMsg.textContent = cheer ? 'כל הכבוד! 🎉 שולחים תמונה למשפחה?' : '';
      if (cheer) { madeBtn.classList.remove('pop'); void madeBtn.offsetWidth; madeBtn.classList.add('pop'); }
    }
    if (madeBtn) {
      madeBtn.addEventListener('click', function () {
        var m = store(MADE_KEY);
        if (m[id]) delete m[id]; else m[id] = new Date().toLocaleDateString('he-IL');
        store(MADE_KEY, m);
        renderMade(!!m[id]);
      });
      renderMade(false);
    }

    // share
    var share = document.querySelector('[data-share]');
    if (share) share.addEventListener('click', function () {
      var m = store(MADE_KEY);
      var text = m[id] ? 'הכנתי ' + title + ' מהמתכונים של תמר 😋' : 'תראו איזה מתכון: ' + title;
      if (navigator.share) {
        navigator.share({ title: title, text: text, url: location.href }).catch(function () {});
      } else {
        window.open('https://wa.me/?text=' + encodeURIComponent(text + '\n' + location.href), '_blank', 'noopener');
      }
    });

    var pr = document.querySelector('[data-print]');
    if (pr) pr.addEventListener('click', function () { window.print(); });
  }

  // ---------- add-recipe form ----------
  var form = document.querySelector('form[data-recipe-form]');
  if (form) {
    var fsId = form.getAttribute('data-formspree');
    var ok = document.getElementById('form-ok'), err = document.getElementById('form-err');
    var submitBtn = form.querySelector('[type=submit]');
    if (!fsId) submitBtn.textContent = '💬 שליחה בוואטסאפ';
    function show(el, text) {
      [ok, err].forEach(function (x) { x.hidden = true; });
      if (text) el.querySelector('[data-text]').textContent = text;
      el.hidden = false; el.focus();
    }
    form.addEventListener('submit', function (e) {
      e.preventDefault();
      var fd = new FormData(form);
      if (!fsId) {
        var lines = ['מתכון חדש לאתר של תמר 🧡'];
        fd.forEach(function (v, k) {
          v = String(v).trim();
          if (v && k.charAt(0) !== '_') lines.push(k + ': ' + (v.indexOf('\n') > -1 ? '\n' + v : v));
        });
        window.open('https://wa.me/?text=' + encodeURIComponent(lines.join('\n')), '_blank', 'noopener');
        show(ok, 'נפתח וואטסאפ עם המתכון 📲 בחרו לשלוח לתמר, ואפשר לצרף שם גם תמונה של הדף. תודה!');
        return;
      }
      submitBtn.disabled = true;
      fetch('https://formspree.io/f/' + fsId, { method: 'POST', body: fd, headers: { 'Accept': 'application/json' } })
        .then(function (r) {
          if (!r.ok) throw new Error('bad status');
          form.reset();
          show(ok);
        })
        .catch(function () { show(err); })
        .then(function () { submitBtn.disabled = false; });
    });
  }
})();
