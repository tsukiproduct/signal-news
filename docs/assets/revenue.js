/* No cookies, network requests or personal data. Integrators can subscribe to
   signal:conversion after configuring their analytics and disclosure. */
(() => {
  'use strict';
  document.addEventListener('click', event => {
    const link = event.target.closest('[data-signal-event]');
    if (!link) return;
    window.dispatchEvent(new CustomEvent('signal:conversion', {detail: {
      event: link.dataset.signalEvent,
      offer: link.dataset.offer || '',
      page: location.pathname
    }}));
  });
  const form = document.getElementById('budget-form');
  if (!form) return;
  const en = document.documentElement.lang === 'en';
  function calculate() {
    const out = document.getElementById('budget-result');
    const detail = document.getElementById('budget-detail');
    if (!form.checkValidity()) {
      out.textContent = en ? 'Check the input ranges.' : '入力範囲を確認してください。'; detail.textContent = ''; return;
    }
    const cost = Number(form.elements.cost.value);
    const runs = Number(form.elements.runs.value);
    const ratio = Number(form.elements.yield.value) / 100;
    const cuts = Number(form.elements.cuts.value);
    const usable = runs * ratio;
    const perCut = cost / usable;
    const yen = n => n.toLocaleString('ja-JP', {maximumFractionDigits: 0});
    if (en) {
      out.textContent = `About ¥${yen(perCut)} per usable shot`;
      detail.textContent = `Estimated usable shots: ${usable.toLocaleString('en-US', {maximumFractionDigits:1})}. Generation cost allocated to a ${cuts}-shot video: about ¥${yen(perCut*cuts)}.` + (cuts > usable ? ' More shots are needed than estimated; check actual top-up prices.' : '');
      return;
    }
    out.textContent = `採用カット1本あたり 約${yen(perCut)}円`;
    detail.textContent = `採用見込み ${usable.toLocaleString('ja-JP', {maximumFractionDigits: 1})}カット。${cuts}カットの完成動画1本に配分される生成費は約${yen(perCut * cuts)}円。` +
      (cuts > usable ? ' 必要カット数が見込みを上回るため、追加生成が必要です。追加購入の実際の料金は別途確認してください。' : '');
  }
  form.addEventListener('submit', event => event.preventDefault());
  form.addEventListener('input', calculate);
  calculate();
})();
