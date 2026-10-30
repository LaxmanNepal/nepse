(()=>{
"use strict";
const $=id=>document.getElementById(id),FRESH=15,SIZE=20;
const S={stocks:[],page:1,filtered:[]};
const n=v=>v!==null&&v!==undefined&&v!==""&&Number.isFinite(Number(v))?Number(v):null;
const fmt=(v,d=2)=>v==null?"—":Number(v).toLocaleString("en-IN",{maximumFractionDigits:d});
const esc=s=>String(s??"").replace(/[&<>"']/g,c=>({"&":"&amp;","<":"&lt;",">":"&gt;",'"':"&quot;","'":"&#39;"}[c]));
function dateText(d){return Number.isNaN(d.getTime())?"Unknown":d.toLocaleString("en-GB",{dateStyle:"medium",timeStyle:"short",timeZone:"Asia/Kathmandu"})+" NPT"}
function stamp(x){return new Date(x?.sourceUpdatedAt||x?.updatedAt||x?.timestamp||0)}
function freshness(l){
 const d=stamp(l),age=(Date.now()-d.getTime())/60000,stale=!Number.isFinite(age)||age>FRESH||age< -5;
 $("feed-label").textContent=stale?"STALE SNAPSHOT":"DATA FRESH";
 $("feed-time").textContent="Updated "+dateText(d);
 $("market-state").textContent=stale?"STALE DATA":"FEED FRESH";
 $("market-state").style.color=stale?"#f5c56b":"#31d6a0";
 if(stale){$("stale-banner").classList.remove("hidden");$("stale-message").textContent="Last source check: "+dateText(d)+" ("+(Number.isFinite(age)?Math.max(0,age).toFixed(0)+" minutes old":"timestamp unavailable") +"). Active trade calls are disabled.";$("signal-status").innerHTML='<div class="empty-icon">⚠</div><b>Trading signals locked — stale feed</b><p>Historical prices are not live quotes. Do not place orders from this snapshot.</p>'}
 else $("stale-banner").classList.add("hidden");
 return !stale;
}
function market(l){
 S.stocks=(Array.isArray(l.stocks)?l.stocks:[]).filter(x=>x&&x.symbol&&n(x.ltp)!=null);
 const pct=x=>n(x.changePercent??x.percent_change??x.changePercent);
 const up=S.stocks.filter(x=>(pct(x)||0)>0).length,down=S.stocks.filter(x=>(pct(x)||0)<0).length,flat=S.stocks.length-up-down,total=S.stocks.length||1;
 $("advancers").textContent=fmt(up,0);$("decliners").textContent=fmt(down,0);
 $("breadth-up").textContent=fmt(up,0);$("breadth-down").textContent=fmt(down,0);$("breadth-flat").textContent=fmt(flat,0);$("breadth-total").textContent=fmt(S.stocks.length,0);
 const a=up/total*100,b=(up+down)/total*100;
 $("breadth-donut").style.background="conic-gradient(#31d6a0 0 "+a+"%,#ff6b78 "+a+"% "+b+"%,#526176 "+b+"% 100%)";
 const turnover=S.stocks.reduce((v,x)=>v+(n(x.turnover)||0),0);
 $("turnover").textContent=turnover>=1e7?(turnover/1e7).toFixed(2)+" Cr":fmt(turnover,0);
 const idx=l.index||{},iv=n(idx.close??idx.currentValue??idx.value),ip=n(idx.perChange??idx.percent_change);
 $("index-value").textContent=iv==null?"—":fmt(iv,2);
 $("index-change").textContent=ip==null?"Index change unavailable":(ip>0?"+":"")+fmt(ip,2)+"% today";
 $("stock-count").textContent=fmt(S.stocks.length,0);
 $("breadth-note").textContent="Calculated from "+S.stocks.length+" stock records. Check feed freshness before using.";
 $("table-status").textContent="Snapshot loaded · "+dateText(stamp(l));S.page=1;filter();
}
function filter(){
 const q=$("search").value.trim().toLowerCase(),m=$("movement").value,sort=$("sort").value;
 let a=S.stocks.filter(x=>(!q||String(x.symbol).toLowerCase().includes(q)||String(x.name).toLowerCase().includes(q))).filter(x=>{const p=n(x.changePercent??x.percent_change)||0;return m==="all"||(m==="up"&&p>0)||(m==="down"&&p<0)||(m==="flat"&&p===0)});
 const key={turnover:"turnover",change:"changePercent",volume:"volume",price:"ltp"}[sort];
 a.sort((x,y)=>sort==="symbol"?String(x.symbol).localeCompare(String(y.symbol)):(n(y[key])||0)-(n(x[key])||0));
 S.filtered=a;rows();
}
function rows(){
 const total=S.filtered.length,pages=Math.max(1,Math.ceil(total/SIZE));S.page=Math.min(S.page,pages);
 const a=S.filtered.slice((S.page-1)*SIZE,S.page*SIZE);
 $("stock-rows").innerHTML=a.length?a.map(x=>{
  const p=n(x.changePercent??x.percent_change)||0,lo=n(x.low),hi=n(x.high),ltp=n(x.ltp),pos=lo!=null&&hi!=null&&hi>lo?Math.max(0,Math.min(100,(ltp-lo)/(hi-lo)*100)):0;
  return '<tr><td class="stock-name"><b>'+esc(x.symbol)+'</b><small>'+esc(x.name||"")+'</small></td><td class="num">'+fmt(ltp)+'</td><td class="num '+(p>0?"positive":p<0?"negative":"")+'">'+(p>0?"+":"")+fmt(p)+'%</td><td class="num">'+fmt(n(x.volume),0)+'</td><td class="num">'+fmt(n(x.turnover),0)+'</td><td class="num"><span class="range"><i style="width:'+pos+'%"></i></span> <small>'+fmt(lo,1)+'–'+fmt(hi,1)+'</small></td></tr>';
 }).join(""):'<tr><td colspan="6" class="table-empty">No stocks match this filter.</td></tr>';
 $("table-status").textContent="Showing "+(total?(S.page-1)*SIZE+1:0)+"–"+Math.min(S.page*SIZE,total)+" of "+total+" matches";
 $("page-label").textContent=S.page+" / "+pages;$("prev").disabled=S.page<=1;$("next").disabled=S.page>=pages;
}
function risk(){
 const c=n($("capital").value),p=n($("risk-pct").value),e=n($("entry").value),s=n($("stop").value);
 if(!c||!p||!e||!s||e<=s||s<=0){$("shares").textContent="—";$("risk-amount").textContent="NPR —";$("position-value").textContent="NPR —";return}
 const qty=Math.floor(c*p/100/(e-s));$("shares").textContent=fmt(qty,0);$("risk-amount").textContent="NPR "+fmt(qty*(e-s),0);$("position-value").textContent="NPR "+fmt(qty*e,0);
}
function renderSignals(data){
 const list=Array.isArray(data.signals)?data.signals:[];
 const buy=list.filter(x=>x.action==="BUY ON CONFIRMATION"),watch=list.filter(x=>x.action==="WATCH BREAKOUT"),sell=list.filter(x=>String(x.action||"").startsWith("SELL")),avoid=list.filter(x=>x.action==="AVOID"),wait=list.filter(x=>x.action==="WAIT");
 const top=[...buy,...watch,...sell,...avoid,...wait].slice(0,10);
 const cards=top.map(x=>{
  const cls=x.action==="BUY ON CONFIRMATION"?"positive":x.action==="AVOID"||String(x.action).startsWith("SELL")?"negative":"muted";
  return '<div class="signal-row"><div><b>'+esc(x.symbol)+'</b><small>'+esc(x.name||"")+'</small></div><span class="'+cls+'">'+esc(x.action)+'</span><div class="signal-levels"><small>Score '+fmt(x.score,1)+' · LTP NPR '+fmt(x.ltp)+'</small><small>Entry '+fmt(x.entry)+' / Stop '+fmt(x.stop)+' / T1 '+fmt(x.target1)+' / T2 '+fmt(x.target2)+'</small></div></div>';
 }).join("");
 $("signal-status").innerHTML='<div class="signal-summary"><span>BUY '+buy.length+'</span><span>WATCH '+watch.length+'</span><span>SELL REVIEW '+sell.length+'</span><span>AVOID '+avoid.length+'</span></div><div class="signal-list">'+(cards||'<p>No eligible stock passed the liquidity and data-quality filters.</p>')+'</div><p class="signal-disclaimer">Generated '+esc(dateText(new Date(data.generatedAt)))+'. '+esc(data.warning||"Heuristic screening only; not a profit guarantee.")+'</p>';
}
async function load(){
 $("refresh").disabled=true;$("refresh").textContent="↻ Loading";
 try{
  const r=await fetch("./data/live.json?v="+Date.now(),{cache:"no-store"});if(!r.ok)throw Error("Market data request failed ("+r.status+")");
  const l=await r.json(),fresh=freshness(l);market(l);
  if(fresh){
   try{const s=await fetch("./data/ai-signals.json?v="+Date.now(),{cache:"no-store"});if(!s.ok)throw Error("No signal file");renderSignals(await s.json())}
   catch{$("signal-status").innerHTML='<div class="empty-icon">⌁</div><b>No validated signal file</b><p>Market data loaded, but the signal engine has not published a result.</p>'}
  }
 }catch(e){
  $("feed-label").textContent="FEED UNAVAILABLE";$("feed-time").textContent=e.message;$("stale-banner").classList.remove("hidden");$("stale-message").textContent="Unable to retrieve stored market snapshot. No trade calls available.";
  $("stock-rows").innerHTML='<tr><td colspan="6" class="table-empty">Market data unavailable. Check the repository pipeline.</td></tr>';$("signal-status").innerHTML='<div class="empty-icon">!</div><b>Data connection failed</b><p>'+esc(e.message)+'</p>';
 }finally{$("refresh").disabled=false;$("refresh").textContent="↻ Refresh"}
}
function init(){
 $("clock").textContent=new Date().toLocaleDateString("en-GB",{weekday:"short",day:"2-digit",month:"short",year:"numeric",timeZone:"Asia/Kathmandu"})+" · NPT";
 ["search","movement","sort"].forEach(id=>$(id).addEventListener(id==="search"?"input":"change",()=>{S.page=1;filter()}));
 $("prev").addEventListener("click",()=>{S.page--;rows()});$("next").addEventListener("click",()=>{S.page++;rows()});$("refresh").addEventListener("click",load);
 ["capital","risk-pct","entry","stop"].forEach(id=>$(id).addEventListener("input",risk));load();
}
document.addEventListener("DOMContentLoaded",init);
})();