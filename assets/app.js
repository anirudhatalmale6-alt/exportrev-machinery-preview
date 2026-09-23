/* ExportRev machinery marketplace preview — same engine as the aircraft one.
   Vanilla. No library, no build step. */
(function () {
  'use strict';

  var $ = function (s, r) { return (r || document).querySelector(s); };
  var all = window.JX || [];

  var photos = window.JX_PHOTOS || {};
  all.forEach(function (l) {
    var ph = photos[l.ref];
    if (ph) { l.img = ph.img; l.credit = ph; }
  });

  var f = { q: '', cat: '', mfr: '', sort: 'price-desc', maxPrice: Infinity, minYear: 0 };
  var nf = new Intl.NumberFormat('en-US');
  function eur(n) { return '€' + nf.format(n); }

  function esc(s) {
    return String(s).replace(/[&<>"']/g, function (c) {
      return { '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[c];
    });
  }

  /* One outline per machine family. A crane drawn as a dumper is the sort of
     thing a plant buyer notices before he reads a single word, so each family
     gets its own shape rather than a shared box. */
  function silhouette(kind) {
    switch (kind) {
      case 'excavator':
        return '<path d="M52 150 h150 q10 0 10 -9 v-16 q0 -9 -10 -9 h-150 q-10 0 -10 9 v16 q0 9 10 9 Z"/>' +
               '<path d="M74 116 h74 q10 0 10 -10 v-22 q0 -10 -10 -10 h-52 q-10 0 -10 10 v32"/>' +
               '<path d="M158 96 L232 58 M232 58 L266 112 M266 112 l-16 22 l-26 -12"/>' +
               '<path d="M224 122 l14 22 l22 -6"/>';
      case 'crane':
        return '<path d="M44 150 h132 q9 0 9 -9 v-14 q0 -9 -9 -9 h-132 q-9 0 -9 9 v14 q0 9 9 9 Z"/>' +
               '<path d="M70 118 h56 q9 0 9 -9 v-18 q0 -9 -9 -9 h-40 q-9 0 -9 9 v27"/>' +
               '<path d="M132 98 L276 52"/><path d="M262 56 l0 44 l-16 0"/>' +
               '<path d="M136 92 L262 56"/>';
      case 'truck':
        return '<path d="M46 144 h96 v-46 h-58 q-10 0 -14 9 l-16 26 q-8 4 -8 11 Z"/>' +
               '<path d="M150 144 h124 v-58 h-124 Z"/>' +
               '<circle cx="86" cy="152" r="14"/><circle cx="196" cy="152" r="14"/>' +
               '<circle cx="238" cy="152" r="14"/>';
      case 'dozer':
        return '<path d="M78 148 h116 q10 0 10 -10 v-20 q0 -10 -10 -10 h-116 q-10 0 -10 10 v20 q0 10 10 10 Z"/>' +
               '<path d="M104 108 h58 v-24 h-48 q-10 0 -10 10 Z"/>' +
               '<path d="M212 92 l0 66 l14 0 l0 -66 Z"/>' +
               '<path d="M74 156 h124"/>';
      case 'loader':
        return '<path d="M66 144 h130 q10 0 10 -10 v-18 q0 -10 -10 -10 h-130 q-10 0 -10 10 v18 q0 10 10 10 Z"/>' +
               '<path d="M96 106 h52 v-26 h-42 q-10 0 -10 10 Z"/>' +
               '<path d="M206 122 L262 106 M262 106 l0 34 l-34 0"/>' +
               '<circle cx="98" cy="150" r="16"/><circle cx="176" cy="150" r="16"/>';
      case 'dumper':
        return '<path d="M52 142 h92 v-34 h-70 q-10 0 -14 8 Z"/>' +
               '<path d="M150 142 h122 l-14 -56 h-108 Z"/>' +
               '<circle cx="90" cy="152" r="15"/><circle cx="216" cy="152" r="17"/>';
      case 'mixer':
        return '<path d="M46 142 h84 v-40 h-56 q-10 0 -14 8 Z"/>' +
               '<path d="M142 140 q-14 -46 30 -54 l56 -10 q34 -4 34 30 q0 34 -34 34 Z"/>' +
               '<circle cx="84" cy="150" r="14"/><circle cx="196" cy="150" r="14"/>' +
               '<circle cx="242" cy="150" r="14"/>';
      case 'forklift':
        return '<path d="M76 142 h94 q10 0 10 -10 v-24 q0 -10 -10 -10 h-94 q-10 0 -10 10 v24 q0 10 10 10 Z"/>' +
               '<path d="M100 98 h48 v-22 h-38 q-10 0 -10 10 Z"/>' +
               '<path d="M196 52 l0 106 M196 52 l16 0 M196 158 l44 0"/>' +
               '<circle cx="98" cy="150" r="14"/><circle cx="160" cy="150" r="14"/>';
      case 'roller':
        return '<path d="M84 122 h98 q10 0 10 -10 v-18 q0 -10 -10 -10 h-98 q-10 0 -10 10 v18 q0 10 10 10 Z"/>' +
               '<circle cx="100" cy="142" r="24"/><circle cx="188" cy="142" r="24"/>' +
               '<path d="M76 142 h8 M204 142 h8"/>';
      case 'drill':
        return '<path d="M62 150 h116 q10 0 10 -10 v-18 q0 -10 -10 -10 h-116 q-10 0 -10 10 v18 q0 10 10 10 Z"/>' +
               '<path d="M196 34 l0 116 M182 34 l28 0 M196 150 l0 8"/>' +
               '<path d="M188 60 l16 0 M188 88 l16 0 M188 116 l16 0"/>' +
               '<path d="M96 112 h52 v-26 h-42 q-10 0 -10 10 Z"/>';
      case 'mining':
        return '<path d="M44 140 h96 v-40 h-74 q-10 0 -14 8 Z"/>' +
               '<path d="M146 140 h134 l-18 -64 h-116 Z"/>' +
               '<circle cx="88" cy="152" r="19"/><circle cx="224" cy="152" r="22"/>';
      case 'industrial':
        return '<path d="M72 148 h140 q10 0 10 -10 v-52 q0 -10 -10 -10 h-140 q-10 0 -10 10 v52 q0 10 10 10 Z"/>' +
               '<path d="M96 108 h40 M96 126 h72 M182 100 l0 34"/>' +
               '<path d="M110 76 l0 -14 M170 76 l0 -14"/>';
      default: /* parts */
        return '<circle cx="142" cy="108" r="36"/><circle cx="142" cy="108" r="14"/>' +
               '<path d="M142 58 l0 -14 M142 172 l0 -14 M92 108 l-14 0 M206 108 l14 0"/>' +
               '<path d="M106 72 l-10 -10 M178 144 l10 10 M178 72 l10 -10 M106 144 l-10 10"/>';
    }
  }

  function plate(l, big) {
    if (l.img) {
      var cr = l.credit || {};
      return '<img src="' + esc(l.img) + '" alt="' +
        esc(l.year + ' ' + l.mfr + ' ' + l.model) + '" loading="lazy" ' +
        'style="width:100%;height:100%;object-fit:cover">' +
        (cr.auteur ? '<span class="credit">' + esc(cr.auteur) + ' · ' +
                     esc(cr.licence || '') + '</span>' : '');
    }
    /* Light plate, to sit on a light page. The aircraft preview draws these
       dark because that page is dark; here a dark rectangle would punch a hole
       in an ExportRev-toned layout. */
    var h = l.hue, h2 = (h + 14) % 360;
    var id = 'g' + l.ref.replace(/\W/g, '') + (big ? 'b' : '');
    return '' +
      '<svg viewBox="0 0 320 200" role="img" aria-label="' +
        esc(l.year + ' ' + l.mfr + ' ' + l.model) + ', illustration">' +
      '<defs><linearGradient id="' + id + '" x1="0" y1="0" x2="0.35" y2="1">' +
        '<stop offset="0" stop-color="hsl(' + h + ',34%,93%)"/>' +
        '<stop offset=".6" stop-color="hsl(' + h + ',26%,86%)"/>' +
        '<stop offset="1" stop-color="hsl(' + h2 + ',22%,79%)"/>' +
      '</linearGradient></defs>' +
      '<rect width="320" height="200" fill="url(#' + id + ')"/>' +
      '<circle cx="258" cy="46" r="26" fill="hsl(' + h + ',48%,64%)" opacity=".16"/>' +
      /* ground line — these machines stand on something */
      '<path d="M0 166 L320 166" stroke="hsl(' + h + ',30%,38%)" stroke-opacity=".20" stroke-width="1.4"/>' +
      '<g transform="translate(160,104) rotate(' + l.tilt + ') translate(-160,-104)" ' +
      'fill="none" stroke="hsl(' + h + ',36%,30%)" stroke-opacity=".72" stroke-width="2.6" ' +
      'stroke-linecap="round" stroke-linejoin="round">' +
      silhouette(l.shape) +
      '</g></svg>';
  }

  function etatClass(s) {
    if (s === 'Just listed') return 'etat neuf';
    if (s === 'Under offer') return 'etat offre';
    return 'etat';
  }

  function specs(l) {
    var out = [];
    if (l.hours) out.push(nf.format(l.hours) + ' h');
    if (l.weight) out.push(l.weight + ' t');
    if (l.power) out.push(l.power + ' hp');
    return out;
  }

  function filtre() {
    var q = f.q.trim().toLowerCase();
    return all.filter(function (l) {
      if (f.cat && l.cat !== f.cat) return false;
      if (f.mfr && l.mfr !== f.mfr) return false;
      if (l.price > f.maxPrice) return false;
      if (l.year < f.minYear) return false;
      if (q) {
        var hay = (l.mfr + ' ' + l.model + ' ' + l.cat + ' ' + l.city + ' ' +
                   l.country + ' ' + l.ref + ' ' + l.year).toLowerCase();
        if (hay.indexOf(q) === -1) return false;
      }
      return true;
    }).sort(function (a, b) {
      switch (f.sort) {
        case 'price-asc': return a.price - b.price;
        case 'year-desc': return b.year - a.year || a.price - b.price;
        case 'hours-asc': return a.hours - b.hours;
        default: return b.price - a.price;
      }
    });
  }

  function rendu() {
    var res = filtre();
    var g = $('#grille');
    $('#compte').innerHTML = '<b>' + res.length + '</b> machines' +
      (res.length === all.length ? '' : ' of ' + all.length);
    if (!res.length) { g.innerHTML = ''; $('#vide').hidden = false; return; }
    $('#vide').hidden = true;

    g.innerHTML = res.map(function (l) {
      var sp = specs(l).map(function (s, i) {
        return (i ? '<span class="dot"></span>' : '') + '<span>' + esc(s) + '</span>';
      }).join('');
      return '<button class="card" type="button" data-ref="' + esc(l.ref) + '">' +
        '<span class="plate" style="aspect-ratio:' + (l.ar || '16/10') + '">' + plate(l) +
          '<span class="' + etatClass(l.status) + '">' + esc(l.status) + '</span>' +
        '</span>' +
        '<span class="cbody">' +
          '<span class="ctype">' + esc(l.cat) + '</span>' +
          '<h3>' + esc(l.year + ' ' + l.mfr + ' ' + l.model) + '</h3>' +
          '<span class="prix">' + eur(l.price) + '</span>' +
          '<span class="meta">' + sp +
            (sp ? '<span class="dot"></span>' : '') +
            '<span>' + esc(l.city) + ', ' + esc(l.country) + '</span>' +
          '</span>' +
        '</span>' +
      '</button>';
    }).join('');
  }

  function ouvrir(ref) {
    var l = all.filter(function (x) { return x.ref === ref; })[0];
    if (!l) return;
    $('#dplate').innerHTML = plate(l, true);
    $('#dtitre').textContent = l.year + ' ' + l.mfr + ' ' + l.model;
    $('#dsous').textContent = l.cat + ' · ' + l.city + ', ' + l.country;
    $('#dprix').textContent = eur(l.price);
    $('#dheures').textContent = l.hours ? nf.format(l.hours) + ' h' : '—';
    $('#dpoids').textContent = l.weight ? l.weight + ' t' : '—';
    $('#dpuiss').textContent = l.power ? l.power + ' hp' : '—';
    $('#dannee').textContent = l.year;
    $('#dref').textContent = l.ref;
    $('#detat').textContent = l.status;
    var cr = l.credit;
    $('#dcredit').innerHTML = cr
      ? 'Photograph: ' + esc(cr.auteur) + ' — ' + esc(cr.licence) +
        ' — <a href="' + esc(cr.source) + '" target="_blank" rel="noopener">source</a>'
      : 'Illustration drawn in the page. No photograph is reproduced for this machine.';
    var d = $('#detail');
    if (d.showModal) { d.showModal(); } else { d.setAttribute('open', ''); }
  }

  document.addEventListener('click', function (e) {
    var c = e.target.closest ? e.target.closest('.card') : null;
    if (c) { ouvrir(c.getAttribute('data-ref')); }
  });

  function bind() {
    var cats = window.JX_CATS || [], mfrs = window.JX_MFRS || [];
    $('#fcat').innerHTML = '<option value="">All categories</option>' +
      cats.map(function (c) { return '<option>' + esc(c) + '</option>'; }).join('');
    $('#fmfr').innerHTML = '<option value="">All makes</option>' +
      mfrs.map(function (m) { return '<option>' + esc(m) + '</option>'; }).join('');

    var max = Math.max.apply(null, all.map(function (l) { return l.price; }));
    var pr = $('#fprix');
    /* Align the ceiling to the slider's own step grid, rounding UP.
       With min=900 and step=500 the browser clamps a max of 1 700 000 down to
       1 699 900 — so dragging the slider fully right would still hide the most
       expensive machine on the site. */
    var pas = +pr.step || 1, bas = +pr.min || 0;
    var plafond = bas + Math.ceil((max - bas) / pas) * pas;
    pr.max = plafond; pr.value = plafond; f.maxPrice = plafond;
    $('#oprix').textContent = eur(plafond);

    $('#fq').addEventListener('input', function () { f.q = this.value; rendu(); });
    $('#fcat').addEventListener('change', function () { f.cat = this.value; rendu(); });
    $('#fmfr').addEventListener('change', function () { f.mfr = this.value; rendu(); });
    $('#ftri').addEventListener('change', function () { f.sort = this.value; rendu(); });
    pr.addEventListener('input', function () {
      f.maxPrice = +this.value;
      $('#oprix').textContent = eur(+this.value);
      rendu();
    });
    $('#fannee').addEventListener('input', function () {
      f.minYear = +this.value;
      $('#oannee').textContent = this.value === '0' ? 'any' : this.value + '+';
      rendu();
    });

    Array.prototype.forEach.call(document.querySelectorAll('.puce'), function (b) {
      b.addEventListener('click', function () {
        var on = b.getAttribute('aria-pressed') === 'true';
        Array.prototype.forEach.call(document.querySelectorAll('.puce'), function (o) {
          o.setAttribute('aria-pressed', 'false');
        });
        b.setAttribute('aria-pressed', on ? 'false' : 'true');
        f.cat = on ? '' : (b.getAttribute('data-cat') || '');
        $('#fcat').value = f.cat;
        rendu();
      });
    });

    $('#dfermer').addEventListener('click', function () {
      var d = $('#detail');
      if (d.close) { d.close(); } else { d.removeAttribute('open'); }
    });

    var note = 0;
    Array.prototype.forEach.call(document.querySelectorAll('.stars button'), function (b, i) {
      b.addEventListener('click', function () {
        note = i + 1;
        Array.prototype.forEach.call(document.querySelectorAll('.stars button'), function (o, j) {
          o.setAttribute('aria-pressed', j < note ? 'true' : 'false');
        });
      });
    });
    $('#fbform').addEventListener('submit', function (e) {
      e.preventDefault();
      $('#fbok').textContent =
        'Thank you. In the live site this would be queued for moderation' +
        (note ? ' (' + note + '/5)' : '') + '. Nothing was sent from this preview.';
    });
  }

  bind();
  rendu();
})();
