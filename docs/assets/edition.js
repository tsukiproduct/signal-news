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
  const visit = read('signal-last-visit-v1');
  const lastVisit = typeof visit[0]==='number' && visit[0]<=Date.now() ? visit[0] : null;
  write('signal-last-visit-v1',[Date.now()]);
  const note=document.getElementById('return-note');
  if(note){note.hidden=false;note.textContent=lastVisit ? (en?'Welcome back. Use “Since your last visit” to catch up.':'おかえりなさい。「前回以降の新着」で続きを確認できます。') : (en?'On your next visit, new stories can be filtered on this device.':'次回から、この端末で前回以降の新着を絞り込めます。');}
  const cards = [...document.querySelectorAll('.news-card')];
  let category = 'all';
  const search = document.getElementById('news-search');
  const mode = document.getElementById('news-mode');
  const sort = document.getElementById('news-sort');
  let page = 1;
  const pageSize = 10;
  function filter(reset = true) {
    if (reset !== false) page = 1;
    const query = (search?.value || '').trim().toLocaleLowerCase();
    const matching = cards.filter(card =>
      (category === 'all' || card.dataset.category === category)
      && (!query || card.textContent.toLocaleLowerCase().includes(query))
      && (mode?.value !== 'new' || (lastVisit !== null && Date.parse(card.dataset.date)>lastVisit))
      && (mode?.value !== 'saved' || saved.has(card.dataset.id))
      && (mode?.value !== 'unread' || !seen.has(card.dataset.id)));
    matching.sort((a,b) => {
      const date = (Date.parse(b.dataset.date)||0)-(Date.parse(a.dataset.date)||0);
      return sort?.value === 'oldest' ? -date : sort?.value === 'useful' ? Number(b.dataset.score)-Number(a.dataset.score)||date : date;
    });
    const pages = Math.max(1, Math.ceil(matching.length/pageSize));
    page = Math.min(page,pages);
    cards.forEach(card => {card.hidden=true;});
    matching.forEach((card,index) => {card.parentNode.append(card);card.hidden=index<(page-1)*pageSize||index>=page*pageSize;});
    const countEl = document.getElementById('result-count');
    if (countEl) countEl.textContent = en ? `${matching.length} stories · 10 per page` : `${matching.length}件の記事・1ページ10件`;
    const empty = document.getElementById('empty');
    if (empty) empty.hidden = matching.length > 0;
    const pager = document.getElementById('news-pagination');
    if (pager) {
      pager.hidden=pages<=1;
      document.getElementById('news-page').textContent=`${page} / ${pages}`;
      document.getElementById('news-prev').disabled=page===1;
      document.getElementById('news-next').disabled=page===pages;
    }
  }
  ['prev','next'].forEach(direction => document.getElementById('news-'+direction)?.addEventListener('click',()=>{
    page += direction==='next'?1:-1;filter(false);
    document.getElementById('result-count')?.scrollIntoView({block:'start'});
  }));
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
  sort?.addEventListener('change', filter);
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
