/* Build guide (EPIC-17) — progressive enhancement for the /build/ tutorial pages.
   Loaded with `defer`, so the DOM is ready. Both features below ADD behaviour to
   markup that already works without JavaScript:
     - copy buttons are created here, so no dead button is ever rendered;
     - tab panels are plain stacked sections with their own headings until this
       script turns them into a .mode-toggle (nothing becomes unreachable). */
(function () {
  'use strict';

  /* ---------- Copy-to-clipboard on code blocks ---------- */
  document.querySelectorAll('.guide-code').forEach(function (block) {
    var code = block.querySelector('pre code');
    var head = block.querySelector('.guide-code-head');
    if (!code || !head || !navigator.clipboard) return;

    var btn = document.createElement('button');
    btn.type = 'button';
    btn.className = 'guide-code-copy';
    btn.innerHTML = '<i class="fas fa-copy" aria-hidden="true"></i><span>Copy</span>';
    btn.setAttribute('aria-label', 'Copy this snippet to the clipboard');

    btn.addEventListener('click', function () {
      navigator.clipboard.writeText(code.textContent).then(function () {
        btn.classList.add('is-done');
        btn.innerHTML = '<i class="fas fa-check" aria-hidden="true"></i><span>Copied</span>';
        setTimeout(function () {
          btn.classList.remove('is-done');
          btn.innerHTML = '<i class="fas fa-copy" aria-hidden="true"></i><span>Copy</span>';
        }, 1600);
      }).catch(function () {
        btn.innerHTML = '<i class="fas fa-circle-exclamation" aria-hidden="true"></i><span>Press Ctrl/Cmd+C</span>';
      });
    });

    head.appendChild(btn);
  });

  /* ---------- Stacked panels -> tabs ---------- */
  document.querySelectorAll('.guide-tabs').forEach(function (group, groupIndex) {
    var panels = Array.prototype.slice.call(group.querySelectorAll('.guide-tabpanel'));
    if (panels.length < 2) return;

    var toggle = document.createElement('div');
    toggle.className = 'mode-toggle';
    toggle.setAttribute('role', 'tablist');

    var tabs = panels.map(function (panel, i) {
      var id = 'guide-tab-' + groupIndex + '-' + i;
      var tab = document.createElement('button');
      tab.type = 'button';
      tab.className = 'mode-tab' + (i === 0 ? ' is-active' : '');
      tab.textContent = panel.dataset.tabLabel || 'Option ' + (i + 1);
      tab.id = id;
      tab.setAttribute('role', 'tab');
      tab.setAttribute('aria-selected', i === 0 ? 'true' : 'false');
      panel.setAttribute('role', 'tabpanel');
      panel.setAttribute('aria-labelledby', id);
      panel.hidden = i !== 0;
      toggle.appendChild(tab);
      return tab;
    });

    tabs.forEach(function (tab, i) {
      tab.addEventListener('click', function () {
        tabs.forEach(function (t, j) {
          t.classList.toggle('is-active', i === j);
          t.setAttribute('aria-selected', i === j ? 'true' : 'false');
          panels[j].hidden = i !== j;
        });
      });
    });

    group.insertBefore(toggle, panels[0]);
    group.classList.add('is-enhanced');
  });
})();
