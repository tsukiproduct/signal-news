const fs = require('node:fs');
const vm = require('node:vm');
const assert = require('node:assert/strict');
const source = fs.readFileSync('docs/assets/edition.js', 'utf8');

for (const lang of ['ja','en']) {
  let valid = true;
  const events = {};
  const result = {textContent:''};
  const calculator = {
    elements: {price:{value:5000},cost:{value:500},hours:{value:3}},
    checkValidity: () => valid,
    addEventListener: (type, cb) => {events[type] = cb;}
  };
  const classes = new Set();
  const document = {
    documentElement:{lang},
    body:{classList:{toggle:(k,on)=>on?classes.add(k):classes.delete(k),contains:k=>classes.has(k)}},
    querySelector:()=>null,
    querySelectorAll:()=>[],
    getElementById:id=>id==='margin-calculator'?calculator:id==='margin-result'?result:null
  };
  // Privacy modes may block storage: the reader and calculator must still work.
  const localStorage = {getItem(){throw Error('blocked');},setItem(){throw Error('blocked');}};
  vm.runInNewContext(source,{document,localStorage,Date,Set,Number});
  assert.match(result.textContent,/1,500/);
  calculator.elements.price.value=0;
  events.input();
  assert.match(result.textContent,/-167/);
  valid=false;
  events.input();
  assert.match(result.textContent,lang==='en'?/Check the input/:/入力範囲/);
}
console.log('Calculator JA/EN, negative margin, validation, blocked storage: passed.');
