/* Preferences and saved stories stay on this device. No analytics requests. */
(() => {
  const en = document.documentElement.lang === 'en';
  const read = key => {try{const value=JSON.parse(localStorage.getItem(key) || '[]');return Array.isArray(value)?value:[];}catch{return [];}};
  const write = (key, value) => {try{localStorage.setItem(key, JSON.stringify(value));}catch{}};
  const saved = new Set(read('signal-saved-v1'));
  const seen = new Set(read('signal-read-v1'));
  const prefs = read('signal-display-v2');
  document.body.classList.toggle('dark', prefs.includes('dark'));
  document.body.classList.toggle('large', prefs.includes('large'));
  for (const kind of ['dark', 'large']) {
    const button = document.querySelector(`[data-display="${kind}"]`);
    if (!button) continue;
    button.setAttribute('aria-pressed', document.body.classList.contains(kind));
    button.addEventListener('click', () => {
      document.body.classList.toggle(kind);
      button.setAttribute('aria-pressed', document.body.classList.contains(kind));
      write('signal-display-v2', ['dark','large'].filter(k => document.body.classList.contains(k)));
    });
  }
  const cards = [...document.querySelectorAll('.news-card')];
  let category = 'all';
  const search = document.getElementById('news-search');
  const mode = document.getElementById('news-mode');
  const sort = document.getElementById('news-sort');
  function filter() {
    const query = (search?.value || '').trim().toLocaleLowerCase();
    let count = 0;
    for (const card of cards) {
      const show = (category === 'all' || card.dataset.category === category)
        && (!query || card.textContent.toLocaleLowerCase().includes(query))
        && (mode?.value !== 'saved' || saved.has(card.dataset.id))
        && (mode?.value !== 'unread' || !seen.has(card.dataset.id));
      card.hidden = !show;
      if (show) count++;
    }
    const countEl = document.getElementById('result-count');
    if (countEl) countEl.textContent = en ? `${count} stories` : `${count}件の記事`;
    const empty = document.getElementById('empty');
    if (empty) empty.hidden = count > 0;
  }
  cards.forEach(card => {
    const id = card.dataset.id;
    const button = card.querySelector('.save');
    const update = () => {
      button.setAttribute('aria-pressed', saved.has(id));
      button.textContent = saved.has(id) ? (en ? 'Saved' : '保存済み') : (en ? 'Save' : 'あとで読む');
      card.classList.toggle('is-read', seen.has(id));
    };
    button.addEventListener('click', () => {saved.has(id) ? saved.delete(id) : saved.add(id);write('signal-saved-v1', [...saved]);update();filter();});
    card.querySelectorAll('a[data-original]').forEach(link => link.addEventListener('click', () => {seen.add(id);write('signal-read-v1', [...seen]);update();}));
    update();
  });
  document.querySelectorAll('[data-filter]').forEach(button => button.addEventListener('click', () => {
    category = button.dataset.filter;
    document.querySelectorAll('[data-filter]').forEach(b => b.setAttribute('aria-pressed', b === button));
    filter();
  }));
  search?.addEventListener('input', filter);
  mode?.addEventListener('change', filter);
  sort?.addEventListener('change', () => {
    [...cards].sort((a,b) => sort.value === 'latest' ? b.dataset.date.localeCompare(a.dataset.date) : Number(b.dataset.score)-Number(a.dataset.score) || b.dataset.date.localeCompare(a.dataset.date)).forEach(c => c.parentNode.append(c));
  });
  const age = document.querySelector('[data-updated]');
  if (age && Date.now()-Date.parse(age.dataset.updated) > 86400000) age.hidden = false;
  filter();
  const calculator = document.getElementById('margin-calculator');
  if (calculator) {
    const calculate = () => {
      const output = document.getElementById('margin-result');
      if (!calculator.checkValidity()) {output.textContent = en ? 'Check the input ranges.' : '入力範囲を確認してください。';return;}
      const price = Number(calculator.elements.price.value), cost = Number(calculator.elements.cost.value), hours = Number(calculator.elements.hours.value);
      const value = ((price-cost)/hours).toLocaleString(en?'en-US':'ja-JP',{maximumFractionDigits:0});
      output.textContent = en ? `¥${value} / hour before tax and overhead` : `経費差引後・税引前の時間単価：${value}円`;
    };
    calculator.addEventListener('input', calculate);
    calculator.addEventListener('submit', e => e.preventDefault());
    calculate();
  }
})();
