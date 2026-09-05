(()=>{'use strict';
const input=document.querySelector('#globalSearch');
const box=document.querySelector('#glassSearch');
if(!input||!box)return;
const results=document.createElement('div');
results.className='global-search-results';
results.setAttribute('role','listbox');
results.hidden=true;
box.appendChild(results);
const style=document.createElement('style');
style.textContent=`.glass-search{position:relative}.global-search-results{position:absolute;top:calc(100% + 9px);left:0;right:0;max-height:390px;overflow:auto;padding:6px;border:1px solid rgba(255,255,255,.82);border-radius:16px;background:rgba(248,250,252,.94);backdrop-filter:blur(28px) saturate(170%);-webkit-backdrop-filter:blur(28px) saturate(170%);box-shadow:0 20px 50px rgba(24,39,75,.18);z-index:5000}.global-search-result{width:100%;display:grid;grid-template-columns:62px 1fr auto;gap:9px;align-items:center;text-align:left;border:0;background:transparent;padding:10px;border-radius:11px;cursor:pointer;color:#172033}.global-search-result:hover,.global-search-result.active{background:rgba(255,255,255,.82)}.global-search-result .gs-symbol{font-size:11px;font-weight:950}.global-search-result .gs-name{font-size:10px;font-weight:750;white-space:nowrap;overflow:hidden;text-overflow:ellipsis}.global-search-result .gs-sector{display:block;color:#8b95a5;font-size:9px;margin-top:2px}.global-search-result .gs-price{text-align:right;font-size:10px;font-weight:850}.global-search-result .gs-change{display:block;font-size:9px;margin-top:2px}.global-search-result .up{color:#17865d}.global-search-result .down{color:#c43f4d}.global-search-empty{padding:18px 12px;text-align:center;color:#7d8796;font-size:10px}.global-search-hint{padding:7px 10px;color:#8b95a5;font-size:9px;border-top:1px solid rgba(20,32,50,.06)}@media(max-width:520px){.glass-search.search-active input{display:block!important}.glass-search.search-active:after{display:none}.glass-search.search-active{position:relative}.global-search-results{position:fixed;top:73px;left:8px;right:8px;max-height:calc(100vh - 90px);border-radius:18px}.global-search-result{grid-template-columns:58px 1fr auto;padding:11px}.global-search-result .gs-name{font-size:10px}}`;
document.head.appendChild(style);
let index=-1,items=[];
const getStocks=()=>Array.isArray(window.NEPSE_STOCKS)?window.NEPSE_STOCKS:[];
const esc=v=>String(v??'').replace(/[&<>\"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','\"':'&quot;',"'":'&#39;'}[c]));
const pct=n=>`${Number(n||0)>=0?'+':''}${Number(n||0).toFixed(2)}%`;
const fmt=n=>Number(n||0).toLocaleString('en-IN');
function open(sym){const p=location.pathname.split('/').filter(Boolean),i=p.indexOf('nepse'),root=i>=0?`/${p.slice(0,i+1).join('/')}/`:'/';location.href=`${root}company.html?symbol=${encodeURIComponent(sym)}`}
function render(q){const term=q.trim().toLowerCase();if(!term){results.hidden=true;results.innerHTML='';items=[];index=-1;return}const a=getStocks().filter(s=>`${s.symbol} ${s.name} ${s.sector}`.toLowerCase().includes(term)).sort((x,y)=>{const ax=x.symbol.toLowerCase()===term?0:x.symbol.toLowerCase().startsWith(term)?1:x.name.toLowerCase().startsWith(term)?2:3;const ay=y.symbol.toLowerCase()===term?0:y.symbol.toLowerCase().startsWith(term)?1:y.name.toLowerCase().startsWith(term)?2:3;return ax-ay||x.symbol.localeCompare(y.symbol)}).slice(0,8);items=a;if(!a.length){results.innerHTML='<div class="global-search-empty">No matching stock found.</div><div class="global-search-hint">Try a symbol or company name.</div>';results.hidden=false;return}results.innerHTML=a.map((s,i)=>`<button class="global-search-result" role="option" aria-selected="false" data-search-index="${i}" data-symbol="${esc(s.symbol)}"><span class="gs-symbol">${esc(s.symbol)}</span><span><span class="gs-name">${esc(s.name||'Unnamed company')}</span><small class="gs-sector">${esc(s.sector||'Other')}</small></span><span class="gs-price">${Number(s.ltp||0).toFixed(2)}<span class="gs-change ${s.percentChange<0?'down':'up'}">${pct(s.percentChange)}</span></span></button>`).join('');results.hidden=false;index=-1}
function setActive(n){const els=[...results.querySelectorAll('.global-search-result')];els.forEach((e,i)=>{const active=i===n;e.classList.toggle('active',active);e.setAttribute('aria-selected',String(active))});index=n;if(els[n])els[n].scrollIntoView({block:'nearest'})}
input.addEventListener('input',()=>render(input.value));
input.addEventListener('keydown',e=>{if(results.hidden)return;if(e.key==='ArrowDown'){e.preventDefault();setActive(Math.min(index+1,items.length-1))}else if(e.key==='ArrowUp'){e.preventDefault();setActive(Math.max(index-1,0))}else if(e.key==='Enter'){e.preventDefault();const s=items[index>=0?index:0];if(s)open(s.symbol)}else if(e.key==='Escape'){e.preventDefault();results.hidden=true;input.blur()}});
results.addEventListener('click',e=>{const b=e.target.closest('[data-symbol]');if(b)open(b.dataset.symbol)});
document.addEventListener('click',e=>{if(!box.contains(e.target))results.hidden=true});
box.addEventListener('click',()=>{if(window.innerWidth<=520){input.style.display='block';box.classList.add('search-active');input.focus();if(input.value)render(input.value)}});
window.addEventListener('nepse-data-ready',()=>{if(input.value)render(input.value)});
setInterval(()=>{if(input.value&&document.activeElement===input&&!results.hidden)render(input.value)},1500);
})();
