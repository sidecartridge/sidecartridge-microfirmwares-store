/* SidecarTridge Microfirmware Store: embeddable app carousel.
 *
 *   <div data-md-store-carousel data-platform="atari-st">
 *     <a href="https://md-store.sidecartridge.com/#atari-st">Browse all apps in the Store</a>
 *   </div>
 *   <script src="https://md-store.sidecartridge.com/widget/carousel.js" defer></script>
 *
 * Add data-theme="dark" when the container sits on a dark background, and data-creator="<name>"
 * to show one creator's apps instead of all of them.
 *
 * Reads <platform>/apps.json from the store that serves this script, so it shows what the store
 * shows. Everything renders inside a shadow root: the host page's CSS cannot restyle the cards and
 * the widget's CSS cannot leak onto the page. Whatever the container holds is the fallback. It
 * stays visible while the catalog loads, and for good if the catalog cannot load.
 */
(() => {
  'use strict';

  const VERSION = '1.0.0';
  const script = document.currentScript || document.querySelector('script[src*="/widget/carousel.js"]');
  if (!script) return;
  const WIDGET = new URL('.', script.src);   // .../widget/
  const STORE = new URL('..', WIDGET);       // the store root
  const reducedMotion = matchMedia('(prefers-reduced-motion: reduce)');

  // The same monogram the store's app cards use (index.html), so an app without an icon looks
  // the same in both places.
  const noLogo = (src) => !src || /placehold\.co/i.test(src) || !/^https:\/\//i.test(src);
  const initials = (name) => {
    const clean = String(name || '').replace(/\(TEST\)/i, '').trim();
    const parts = clean.split(/\s+/).filter(Boolean);
    const s = parts.length >= 2 ? parts[0][0] + parts[1][0] : clean.slice(0, 2);
    return (s || '?').toUpperCase();
  };
  const logoBg = (name) => {
    let h = 0;
    const s = String(name || '');
    for (let i = 0; i < s.length; i++) h = (h * 31 + s.charCodeAt(i)) % 360;
    return `linear-gradient(135deg, hsl(${h},42%,52%), hsl(${(h + 40) % 360},42%,38%))`;
  };

  // Descriptions are untrusted third-party HTML. The widget keeps only their text and never
  // inserts catalog markup, so there is nothing to sanitize. DOMParser documents are inert.
  //
  // Catalog descriptions often close on a link such as "Learn more". The whole card is already a
  // link, so that text would point nowhere: a final link whose text is a generic call to action
  // is dropped. Any other link keeps its text, because it is part of a sentence ("visit
  // neilrackett.com.").
  const CALL_TO_ACTION = /^\s*(learn|read|find out|see|more|details)\b/i;
  const plainText = (html) => {
    const body = new DOMParser().parseFromString(String(html || ''), 'text/html').body;
    const links = body.querySelectorAll('a');
    const last = links[links.length - 1];
    if (last && CALL_TO_ACTION.test(last.textContent)) {
      const after = body.ownerDocument.createRange();
      after.setStartAfter(last);
      after.setEnd(body, body.childNodes.length);
      if (/^[\s.!?]*$/.test(after.toString())) last.remove();
    }
    return body.textContent.replace(/\s+/g, ' ').trim();
  };

  const el = (tag, className, text) => {
    const node = document.createElement(tag);
    if (className) node.className = className;
    if (text != null) node.textContent = text;
    return node;
  };

  const CHEVRON = '<svg viewBox="0 0 16 16" aria-hidden="true" focusable="false"><path d="M10 3 5 8l5 5" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"/></svg>';

  function slide(app, creators, platform, index, total) {
    const li = el('li', 'slide');
    li.setAttribute('aria-roledescription', 'slide');
    li.setAttribute('aria-label', `${index + 1} of ${total}`);

    const a = el('a', 'card');
    a.href = new URL(`#${encodeURIComponent(platform)}/${encodeURIComponent(app.uuid)}`, STORE).href;
    a.target = '_blank';
    a.rel = 'noopener';
    a.draggable = false;

    const media = el('div', 'media');
    media.style.setProperty('--logo-bg', logoBg(app.name));
    media.append(el('span', 'monogram', initials(app.name)));
    if (!noLogo(app.image)) {
      const img = el('img', 'icon');
      img.src = app.image;
      img.alt = '';            // the app name is the card's text; the icon adds nothing to read out
      img.loading = 'lazy';
      img.decoding = 'async';
      img.draggable = false;
      img.addEventListener('error', () => img.remove());
      media.append(img);
    }

    const body = el('div', 'body');
    const meta = el('p', 'meta');
    if (app.version) meta.append(el('span', 'version', app.version));
    const creator = creators[app.creator];
    meta.append(el('span', 'creator', `by ${(creator && creator.name) || app.creator || 'unknown'}`));
    body.append(meta, el('h3', 'name', app.name || 'Untitled'));

    const desc = plainText(app.description);
    if (desc) body.append(el('p', 'desc', desc));

    const tags = (app.tags || []).filter((t) => typeof t === 'string').slice(0, 3);
    if (tags.length) {
      const ul = el('ul', 'tags');
      tags.forEach((t) => ul.append(el('li', null, t)));
      body.append(ul);
    }

    a.append(media, body);
    li.append(a);
    return li;
  }

  function build(root, data, platform, byName) {
    const apps = data.apps;
    const creators = data.creators || {};

    const section = el('section', 'carousel');
    section.setAttribute('aria-roledescription', 'carousel');
    section.setAttribute('aria-label', 'Microfirmware catalog');

    const bar = el('div', 'bar');
    const count = `${apps.length} microfirmware${apps.length === 1 ? '' : 's'}`;
    bar.append(el('p', 'count', byName ? `${count} by ${byName}` : count));
    const nav = el('div', 'nav');
    const prev = el('button', 'prev');
    const next = el('button', 'next');
    prev.type = next.type = 'button';
    prev.setAttribute('aria-label', 'Previous apps');
    next.setAttribute('aria-label', 'Next apps');
    prev.innerHTML = next.innerHTML = CHEVRON;
    nav.append(prev, next);
    bar.append(nav);

    const track = el('ul', 'track');
    track.tabIndex = 0;          // arrow keys scroll it without tabbing through every card
    track.setAttribute('aria-label', 'Apps');
    apps.forEach((app, i) => track.append(slide(app, creators, platform, i, apps.length)));

    const progress = el('div', 'progress');
    progress.setAttribute('aria-hidden', 'true');
    const thumb = el('span');
    progress.append(thumb);

    section.append(bar, track, progress);
    root.replaceChildren(root.querySelector('link'), section);

    // One press moves by as many whole cards as fit, so nothing is skipped or half-shown.
    const page = () => {
      const card = track.querySelector('.slide');
      const gap = parseFloat(getComputedStyle(track).columnGap) || 0;
      const unit = card ? card.getBoundingClientRect().width + gap : track.clientWidth;
      return Math.max(1, Math.floor((track.clientWidth + gap) / unit)) * unit;
    };
    const go = (dir) => track.scrollBy({ left: dir * page(), behavior: reducedMotion.matches ? 'auto' : 'smooth' });
    prev.addEventListener('click', () => go(-1));
    next.addEventListener('click', () => go(1));

    const update = () => {
      const max = track.scrollWidth - track.clientWidth;
      section.classList.toggle('static', max <= 1);
      prev.disabled = track.scrollLeft <= 1;
      next.disabled = track.scrollLeft >= max - 1;
      thumb.style.width = `${(track.clientWidth / track.scrollWidth) * 100}%`;
      thumb.style.left = `${(track.scrollLeft / track.scrollWidth) * 100}%`;
    };
    track.addEventListener('scroll', update, { passive: true });
    new ResizeObserver(update).observe(track);

    // Mouse drag. Touch and trackpads already scroll natively; a mouse can only click, so this
    // lets it grab the row too. A drag must not end in opening the card it started on.
    let drag = null;
    track.addEventListener('pointerdown', (e) => {
      if (e.pointerType !== 'mouse' || e.button !== 0) return;
      drag = { id: e.pointerId, x: e.clientX, left: track.scrollLeft, moved: false };
    });
    track.addEventListener('pointermove', (e) => {
      if (!drag || e.pointerId !== drag.id) return;
      const dx = e.clientX - drag.x;
      if (!drag.moved) {
        if (Math.abs(dx) < 6) return;
        drag.moved = true;
        track.setPointerCapture(e.pointerId);
        track.classList.add('dragging');   // snapping off while dragging, or the row fights back
      }
      track.scrollLeft = drag.left - dx;
    });
    const end = (e) => {
      if (!drag || e.pointerId !== drag.id) return;
      const moved = drag.moved;
      drag = null;
      track.classList.remove('dragging');  // snapping back on settles on the nearest card
      if (!moved) return;
      const block = (ev) => { ev.preventDefault(); ev.stopPropagation(); };
      track.addEventListener('click', block, true);
      setTimeout(() => track.removeEventListener('click', block, true), 0);
    };
    track.addEventListener('pointerup', end);
    track.addEventListener('pointercancel', end);
  }

  function mount(host) {
    if (host.shadowRoot) return;             // the script was included twice
    const platform = (host.dataset.platform || 'atari-st').trim();
    const creator = (host.dataset.creator || '').trim();
    if (!/^[a-z0-9-]+$/.test(platform)) return;

    // Until the carousel is ready the shadow root only holds a slot, which keeps showing the
    // container's own fallback content.
    const root = host.attachShadow({ mode: 'open' });
    const css = el('link');
    css.rel = 'stylesheet';
    css.href = new URL(`carousel.css?v=${VERSION}`, WIDGET).href;
    root.append(css, el('slot'));

    const styled = new Promise((resolve, reject) => {
      css.addEventListener('load', resolve);
      css.addEventListener('error', reject);
    });
    const catalog = fetch(new URL(`${platform}/apps.json`, STORE), { credentials: 'omit' })
      .then((r) => { if (!r.ok) throw new Error(`HTTP ${r.status}`); return r.json(); });

    Promise.all([catalog, styled])
      .then(([data]) => {
        if (!data || !Array.isArray(data.apps)) return;
        const creators = data.creators || {};
        // data-creator narrows the carousel to one creator. It matches the creator's id or display
        // name, ignoring case, so "neilrackett" and "Neil Rackett" both work. Empty shows every app.
        const wanted = creator.toLowerCase();
        const byCreator = (app) => [app.creator, creators[app.creator] && creators[app.creator].name]
          .some((v) => typeof v === 'string' && v.trim().toLowerCase() === wanted);
        const apps = wanted ? data.apps.filter(byCreator) : data.apps;
        if (!apps.length) {
          if (wanted) console.warn(`[md-store carousel] no apps by creator "${creator}" on ${platform}`);
          return;
        }
        const byName = wanted ? (creators[apps[0].creator] && creators[apps[0].creator].name) || apps[0].creator : '';
        build(root, { ...data, apps }, platform, byName);
      })
      .catch((err) => console.warn('[md-store carousel]', err));
  }

  const start = () => document.querySelectorAll('[data-md-store-carousel]').forEach(mount);
  if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded', start);
  else start();
})();
