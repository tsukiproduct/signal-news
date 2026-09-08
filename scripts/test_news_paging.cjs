const fs=require('node:fs'), vm=require('node:vm'), assert=require('node:assert/strict');
const element=(value='')=>({value,hidden:false,events:{},addEventListener(k,f){this.events[k]=f},setAttribute(){},scrollIntoView(){}});
for(const lang of ['ja','en']){
 const ids={};['news-search','news-mode','news-sort','result-count','empty','news-pagination','news-page','news-prev','news-next'].forEach(k=>ids[k]=element());ids['news-sort'].value='latest';
 const cards=Array.from({length:23},(_,i)=>{const save=element();return {dataset:{id:String(i),date:new Date(2026,8,i+1).toISOString(),score:i%5,category:'Tools'},textContent:`story ${i}`,classList:{toggle(){}},parentNode:{append(){}},querySelector:()=>save,querySelectorAll:()=>[]}});
 const document={documentElement:{lang},body:{classList:{toggle(){},contains(){return false}}},querySelector:()=>null,querySelectorAll:q=>q==='.news-card'?cards:[],getElementById:id=>ids[id]||null};
 vm.runInNewContext(fs.readFileSync('docs/assets/edition.js','utf8'),{document,localStorage:{getItem:()=>null,setItem(){}},Date,Set,Number});
 const visible=()=>cards.filter(c=>!c.hidden).map(c=>Number(c.dataset.id));
 assert.deepEqual(visible(),[13,14,15,16,17,18,19,20,21,22]);
 ids['news-next'].events.click();assert.equal(visible().length,10);
 ids['news-next'].events.click();assert.deepEqual(visible(),[0,1,2]);assert.equal(ids['news-next'].disabled,true);
 ids['news-sort'].value='oldest';ids['news-sort'].events.change();assert.deepEqual(visible(),[0,1,2,3,4,5,6,7,8,9]);
 ids['news-search'].value='story 22';ids['news-search'].events.input();assert.deepEqual(visible(),[22]);assert.equal(ids['news-pagination'].hidden,true);
 ids['news-search'].value='';ids['news-mode'].value='new';ids['news-mode'].events.change();assert.equal(visible().length,0);
 ids['news-mode'].value='all';
 ids['news-search'].value='missing';ids['news-search'].events.input();assert.equal(visible().length,0);assert.equal(ids.empty.hidden,false);
}
console.log('JA/EN paging, global date sort, filter reset, last page and empty state passed');
