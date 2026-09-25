/* Offline-only controls for the parent dashboard. All data is bundled locally. */
(() => {
  const $ = (selector, root = document) => root.querySelector(selector);
  const $$ = (selector, root = document) => [...root.querySelectorAll(selector)];
  const toast = (message) => {
    const el = $('#toast');
    if (!el) return;
    el.textContent = message;
    el.classList.add('show');
    clearTimeout(toast.timer);
    toast.timer = setTimeout(() => el.classList.remove('show'), 2400);
  };
  const titles = { overview: 'Lake Malawi at a glance', signal: 'Water signal, unpacked', network: 'Network alert propagation', health: 'Water signal to human action' };

  function wireNavigation() {
    $$('.nav').forEach(button => button.addEventListener('click', () => {
      const view = button.dataset.view;
      $$('.nav').forEach(item => item.classList.toggle('active', item === button));
      $$('[data-panel]').forEach(panel => {
        const active = panel.dataset.panel === view;
        panel.classList.toggle('visible', active);
        panel.hidden = !active;
      });
      const heading = $('#title');
      if (heading) heading.textContent = titles[view] || titles.overview;
    }));
  }

  function wireSatelliteToggle() {
    const image = $('img[src*="satellite-demo"], .satellite img, .map img');
    if (!image) return;
    const frame = image.closest('.satellite, .card') || image.parentElement;
    const controls = document.createElement('div');
    controls.className = 'local-scene-toggle';
    controls.setAttribute('role', 'group');
    controls.setAttribute('aria-label', 'Local satellite image mode');
    controls.style.cssText = 'display:flex;gap:8px;margin:10px 0;flex-wrap:wrap';
    const modes = [
      ['natural', 'Natural color', 'assets/satellite-natural.png', 'assets/satellite-natural.svg'],
      ['ir', 'Infrared / false color', 'assets/satellite-ir.png', 'assets/satellite-ir.svg']
    ];
    const select = (mode, button) => {
      const [, label, png, fallback] = mode;
      image.onerror = () => { image.onerror = null; image.src = fallback; };
      image.src = png;
      image.alt = `${label} local illustration of Lake Malawi near Salima`;
      controls.querySelectorAll('button').forEach(item => {
        const active = item === button;
        item.setAttribute('aria-pressed', String(active));
        item.style.cssText = `border:1px solid #b7e7e2;border-radius:4px;padding:8px 10px;cursor:pointer;font-weight:700;background:${active ? '#081a2b' : '#edf3f3'};color:${active ? '#fff' : '#426176'}`;
      });
    };
    modes.forEach(mode => {
      const button = document.createElement('button');
      button.type = 'button';
      button.textContent = mode[1];
      button.addEventListener('click', () => select(mode, button));
      controls.append(button);
    });
    frame.insertAdjacentElement('afterend', controls);
    const caption = document.createElement('p');
    caption.className = 'local-place-label';
    caption.textContent = 'Lake Malawi · Salima District, Malawi — illustrative, offline scene';
    caption.style.cssText = 'margin:6px 0;color:#426176;font-size:12px';
    controls.insertAdjacentElement('afterend', caption);
    select(modes[0], controls.querySelector('button'));
  }

  function labelRealPlaces() {
    const replacements = [['Demo Lake', 'Lake Malawi (Salima District)'], ['Khaoleya', 'Salima'], ['Chisomo', 'Nkhotakota'], ['Matope', 'Mangochi']];
    const walk = () => {
      const walker = document.createTreeWalker(document.body, NodeFilter.SHOW_TEXT);
      let node;
      while ((node = walker.nextNode())) {
        if (!node.parentElement || /^(SCRIPT|STYLE)$/.test(node.parentElement.tagName)) continue;
        let text = node.nodeValue;
        replacements.forEach(([from, to]) => { text = text.replaceAll(from, to); });
        if (text !== node.nodeValue) node.nodeValue = text;
      }
    };
    walk();
    new MutationObserver(walk).observe(document.body, { childList: true, subtree: true, characterData: true });
  }

  function addNetworkRiskMarkers() {
    const svg = $('.network .map svg, [data-panel="network"] .map svg');
    if (!svg || svg.querySelector('.offline-risk-markers')) return;
    const ns = 'http://www.w3.org/2000/svg';
    const group = document.createElementNS(ns, 'g');
    group.setAttribute('class', 'offline-risk-markers');
    group.setAttribute('aria-label', 'Red screening risk markers: Salima source and downstream locations');
    [[360, 78, 'Salima · flagged source'], [120, 174, 'Nkhotakota · exposed'], [360, 174, 'Salima · exposed'], [600, 174, 'Mangochi · exposed']].forEach(([x, y, label]) => {
      const marker = document.createElementNS(ns, 'circle');
      marker.setAttribute('cx', x); marker.setAttribute('cy', y); marker.setAttribute('r', 8);
      marker.setAttribute('fill', '#dc2626'); marker.setAttribute('stroke', '#fff'); marker.setAttribute('stroke-width', 3);
      marker.setAttribute('aria-label', `Red risk marker: ${label}`);
      group.append(marker);
    });
    svg.append(group);
  }

  function wireLocalControls() {
    $('#refresh')?.addEventListener('click', () => toast('Offline demo is already current.'));
    $('#help')?.addEventListener('click', () => toast('Choose a dashboard view, switch the local satellite image, or run the offline network preview.'));
    $('#language')?.addEventListener('click', event => {
      const button = event.currentTarget;
      button.textContent = button.textContent.includes('SW') ? 'EN / SW' : 'SW / EN';
      toast('Language control updated locally; no message was sent.');
    });
    $('#alert-action')?.addEventListener('click', () => toast('Use a verified-safe source and contact local authorities.'));
    $('#share')?.addEventListener('click', () => toast('Local field note ready to share; nothing was sent.'));
    $$('.task input[type="checkbox"]').forEach(box => box.addEventListener('change', () => {
      const row = box.closest('.task');
      row?.classList.toggle('done', box.checked);
      const state = $('.task-state', row);
      if (state) state.textContent = box.checked ? 'DONE' : 'PENDING';
    }));
    $('#network-demo')?.addEventListener('click', () => {
      addNetworkRiskMarkers();
      toast('Offline network preview: red screening markers shown; field sample still required.');
    });
    $('#demo-run')?.addEventListener('click', () => toast('Offline presenter controls are ready.'));
    $('#next-beat')?.addEventListener('click', () => toast('Explore the next dashboard view from the sidebar.'));
  }

  function init() {
    wireNavigation();
    wireLocalControls();
    labelRealPlaces();
    wireSatelliteToggle();
    addNetworkRiskMarkers();
  }
  if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded', init, { once: true });
  else init();
})();
