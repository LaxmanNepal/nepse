(()=>{
"use strict";
const $=id=>document.getElementById(id),FRESH=15,SIZE=20;
const S={stocks:[],page:1,filtered:[],live:null};
const n=v=>v!==null&&v!==undefined&&v!==""&&Number.isFinite(Number(v))?Number(v):null;
const fmt=(v,d=2)=>v==null?"—":Number(v).toLocaleString("en-IN",{maximumFractionDigits:d});
const esc=s=>String(s??"").replace(/[&<>"']/g,c=>({"&":"&amp;","<":"&lt;",">":"&gt;",'"':"&quot;","'":"&#39;"}[c]));
function siteNavigate(path){if(window.top!==window.self)window.top.location.href='https://laxmannepal.com.np'+path;else location.href=path}
function dateText(d){return Number.isNaN(d.getTime())?"Unknown":d.toLocaleString("en-GB",{dateStyle:"medium",timeStyle:"short",timeZone:"Asia/Kathmandu"})+" NPT"}
function stamp(x){return new Date(x?.sourceUpdatedAt||x?.updatedAt||x?.timestamp||0)}
function freshness(l){
 const d=stamp(l),age=(Date.now()-d.getTime())/60000;
 const verified=(l.sourceVerification||{}).status==="verified"&&l.tradeSignalsEnabled===true;
 const fresh=Number.isFinite(age)&&age<=FRESH&&age>=-5;
 const stale=!fresh||!verified;
 $("feed-label").textContent=!verified?"UNVERIFIED SOURCE":stale?"OLD SNAPSHOT":"VERIFIED FEED";
 $("feed-time").textContent="Source timestamp "+dateText(d);
 $("market-state").textContent=!verified?"SIGNALS LOCKED":stale?"NOT LIVE":"VERIFIED";
 $("market-state").style.color=stale?"#b7791f":"#16865b";
 if(stale){$("stale-banner").classList.remove("hidden");$("stale-message").textContent=!verified?"Source is not independently verified. Market values are for reference only; BUY/SELL signals are disabled. Source timestamp: "+dateText(d):"Source timestamp: "+dateText(d)+" ("+(Number.isFinite(age)?Math.max(0,age).toFixed(0)+" minutes old":"timestamp unavailable")+"). Active trade calls are disabled.";$("signal-status").innerHTML='<div class="empty-icon">⚠</div><b>Trading signals locked — source not verified</b><p>Quotes are reference snapshots only. No BUY, SELL or WATCH recommendations are permitted until a licensed source passes independent comparison and freshness checks.</p>'}
 else $("stale-banner").classList.add("hidden");
 return !stale;
}
function market(l){
 S.live=l;
 S.stocks=(Array.isArray(l.stocks)?l.stocks:[]).filter(x=>x&&x.symbol);
 const quoted=S.stocks.filter(x=>n(x.ltp)!=null),pct=x=>n(x.changePercent??x.percent_change??x.changePercent);
 const up=quoted.filter(x=>(pct(x)??0)>0).length,down=quoted.filter(x=>(pct(x)??0)<0).length,flat=quoted.filter(x=>pct(x)===0).length,total=quoted.length||1;
 $("advancers").textContent=fmt(up,0);$("decliners").textContent=fmt(down,0);
 $("breadth-up").textContent=fmt(up,0);$("breadth-down").textContent=fmt(down,0);$("breadth-flat").textContent=fmt(flat,0);$("breadth-total").textContent=fmt(quoted.length,0);
 const a=up/total*100,b=(up+down)/total*100;
 $("breadth-donut").style.background="conic-gradient(#31d6a0 0 "+a+"%,#ff6b78 "+a+"% "+b+"%,#526176 "+b+"% 100%)";
 const turnover=S.stocks.reduce((v,x)=>v+(n(x.turnover)||0),0);
 $("turnover").textContent=turnover>=1e7?(turnover/1e7).toFixed(2)+" Cr":fmt(turnover,0);
 const idx=l.index||{},iv=n(idx.close??idx.currentValue??idx.value),ip=n(idx.perChange??idx.percent_change);
 $("index-value").textContent=iv==null?"—":fmt(iv,2);
 $("index-change").textContent=ip==null?"Index change unavailable":(ip>0?"+":"")+fmt(ip,2)+"% today";
 $("stock-count").textContent=fmt(S.stocks.length,0);
 $("breadth-note").textContent="Breadth from "+quoted.length+" stocks with quotes; "+(S.stocks.length-quoted.length)+" active listings have no quote in this snapshot." ;
 $("table-status").textContent="Snapshot loaded · "+dateText(stamp(l));S.page=1;filter();
}
function filter(){
 const q=$("search").value.trim().toLowerCase(),m=$("movement").value,sort=$("sort").value;
 let a=S.stocks.filter(x=>(!q||String(x.symbol).toLowerCase().includes(q)||String(x.name).toLowerCase().includes(q))).filter(x=>{const p=n(x.changePercent??x.percent_change);return m==="all"||(m==="up"&&p!=null&&p>0)||(m==="down"&&p!=null&&p<0)||(m==="flat"&&p===0)});
 const key={turnover:"turnover",change:"changePercent",volume:"volume",price:"ltp"}[sort];
 a.sort((x,y)=>sort==="symbol"?String(x.symbol).localeCompare(String(y.symbol)):(n(y[key])||0)-(n(x[key])||0));
 S.filtered=a;rows();
}
function rows(){
 const total=S.filtered.length,pages=Math.max(1,Math.ceil(total/SIZE));S.page=Math.min(S.page,pages);
 const a=S.filtered.slice((S.page-1)*SIZE,S.page*SIZE);
 $("stock-rows").innerHTML=a.length?a.map(x=>{
  const p=n(x.changePercent??x.percent_change),lo=n(x.low),hi=n(x.high),ltp=n(x.ltp),pos=lo!=null&&hi!=null&&hi>lo?Math.max(0,Math.min(100,(ltp-lo)/(hi-lo)*100)):0;
  return '<tr class="stock-row" data-symbol="'+esc(x.symbol)+'" tabindex="0" role="button" aria-label="Open '+esc(x.symbol)+' research"><td class="stock-name"><b>'+esc(x.symbol)+'</b><small>'+esc(x.name||"")+'</small></td><td class="num">'+fmt(ltp)+'</td><td class="num '+(p>0?"positive":p<0?"negative":"")+'">'+(p!=null&&p>0?"+":"")+(p==null?"—":fmt(p)+"%")+'</td><td class="num">'+fmt(n(x.volume),0)+'</td><td class="num">'+fmt(n(x.turnover),0)+'</td><td class="num"><span class="range"><i style="width:'+pos+'%"></i></span> <small>'+fmt(lo,1)+'–'+fmt(hi,1)+'</small></td></tr>';
 }).join(""):'<tr><td colspan="6" class="table-empty">No stocks match this filter.</td></tr>';
 $("table-status").textContent="Showing "+(total?(S.page-1)*SIZE+1:0)+"–"+Math.min(S.page*SIZE,total)+" of "+total+" matches";
 $("page-label").textContent=S.page+" / "+pages;$("prev").disabled=S.page<=1;$("next").disabled=S.page>=pages;
}
function bar(label,value,display,ratio,klass=""){
 const w=Math.max(0,Math.min(100,Number(ratio)||0));
 return '<div class="data-bar"><div><span>'+esc(label)+'</span><b class="'+klass+'">'+esc(display)+'</b></div><i><em style="width:'+w+'%"></em></i></div>';
}
function miniChart(points){
 const vals=points.map(p=>n(p.close)).filter(v=>v>0);if(vals.length<2)return '<div class="chart-empty">Not enough daily history to draw a price chart.</div>';
 const W=760,H=190,P=12,min=Math.min(...vals),max=Math.max(...vals),span=max-min||1;
 const coords=vals.map((v,i)=>[P+i*(W-2*P)/(vals.length-1),H-P-(v-min)/span*(H-2*P)]);
 const path=coords.map((p,i)=>(i?"L":"M")+p[0].toFixed(1)+","+p[1].toFixed(1)).join(" ");
 return '<div class="history-chart"><div class="chart-meta"><span>'+esc(points[0].date||"Start")+'</span><b>'+vals.length+' daily observations</b><span>'+esc(points[points.length-1].date||"Latest")+'</span></div><svg viewBox="0 0 '+W+' '+H+'" role="img" aria-label="Daily closing price chart"><defs><linearGradient id="priceFill" x1="0" x2="0" y1="0" y2="1"><stop offset="0" stop-color="#268bdf" stop-opacity=".22"/><stop offset="1" stop-color="#268bdf" stop-opacity="0"/></linearGradient></defs><path d="'+path+' L'+coords[coords.length-1][0]+' '+(H-P)+' L'+P+' '+(H-P)+' Z" fill="url(#priceFill)"/><path d="'+path+'" fill="none" stroke="#268bdf" stroke-width="2.6" stroke-linecap="round" stroke-linejoin="round"/></svg><div class="chart-scale"><span>NPR '+fmt(min)+'</span><span>NPR '+fmt(max)+'</span></div></div>';
}
function calculateStockIndicators(history, stock){
 const closes=history.map(x=>n(x.close??x.ltp)).filter(x=>x!=null&&x>0);
 const mean=a=>a.length?a.reduce((v,x)=>v+x,0)/a.length:null;
 const sma=p=>closes.length>=p?mean(closes.slice(-p)):null;
 const emaSeries=(values,p)=>{if(values.length<p)return[];const k=2/(p+1),out=[mean(values.slice(0,p))];for(let i=p;i<values.length;i++)out.push(values[i]*k+out[out.length-1]*(1-k));return out};
 const e12=emaSeries(closes,12),e26=emaSeries(closes,26);
 const changes=closes.slice(1).map((v,i)=>v-closes[i]),recent=changes.slice(-14);
 const gains=recent.map(v=>Math.max(v,0)),losses=recent.map(v=>Math.max(-v,0)),ag=mean(gains),al=mean(losses);
 const rsi14=recent.length<14?null:al===0?(ag>0?100:50):100-(100/(1+ag/al));
 let macd=null;
 if(e12.length&&e26.length){const offset=26-12,lines=e26.map((v,i)=>e12[i+offset]-v),sig=emaSeries(lines,9),line=lines[lines.length-1],signal=sig.length?sig[sig.length-1]:null;macd={line,signal,histogram:signal==null?null:line-signal}}
 const vols=history.map(x=>n(x.volume??x.quantity??x.totalTradedQuantity)).filter(v=>v!=null&&v>=0),avgVolume20=vols.length>=21?mean(vols.slice(-21,-1)):null;
 return {history_points:closes.length,rsi14:rsi14==null?null:Number(rsi14.toFixed(2)),sma20:sma(20),sma50:sma(50),ema12:e12.length?e12[e12.length-1]:null,ema26:e26.length?e26[e26.length-1]:null,macd,avg_volume20:avgVolume20,relative_volume:avgVolume20&&n(stock.volume)!=null?n(stock.volume)/avgVolume20:null};
}
async function openStock(symbol){
 const stock=S.stocks.find(x=>String(x.symbol).toUpperCase()===String(symbol).toUpperCase());if(!stock)return;document.title=stock.symbol+" — "+(stock.name||"NEPSE Stock Research")+" | NEPSE Terminal";
 const panel=$("stock-detail");panel.classList.remove("hidden");$("detail-title").textContent=stock.name||stock.symbol;$("detail-subtitle").textContent=stock.symbol+" · "+(stock.sector&&stock.sector!=="Other"?stock.sector:"Sector not supplied")+" · source snapshot";
 $("detail-content").innerHTML='<p class="table-empty">Loading '+esc(stock.symbol)+' historical research…</p>';
 panel.scrollIntoView({behavior:"smooth",block:"start"});
 let history=[],ind={},signal=null;
 try{const [hr,sr]=await Promise.all([fetch("/nepse/data/history/"+encodeURIComponent(stock.symbol)+".json?v="+Date.now()),fetch("/nepse/data/ai-signals.json?v="+Date.now())]);if(hr.ok)history=await hr.json();if(sr.ok){const sd=await sr.json();signal=(sd.signals||[]).find(x=>x.symbol===stock.symbol)||null;ind=signal?.indicators||{}}}catch(e){}
 if(!Array.isArray(history))history=[];
 if(!ind||!Object.keys(ind).length)ind=calculateStockIndicators(history,stock);
 const ltp=n(stock.ltp),p=n(stock.changePercent??stock.percent_change)||0,lo=n(stock.low),hi=n(stock.high),vol=n(stock.volume)||0,to=n(stock.turnover)||0,range=lo!=null&&hi!=null&&hi>lo?(ltp-lo)/(hi-lo)*100:0;
 const sourceVerified=S.live?.sourceVerification?.status==="verified"&&S.live?.tradeSignalsEnabled===true;
 const tradeStatus=!sourceVerified?"AVOID / NO TRADE":signal?.action||"WAIT / INSUFFICIENT SETUP";
 const statusWhy=!sourceVerified?"Market feed has not passed independent licensed-source verification. This is a data-safety lock, not a fundamental judgement on this company.":signal?.method||"No eligible signal was generated from the available history.";
 const closes=history.map(x=>n(x.close)).filter(x=>x>0),last20=history.slice(-20),support=last20.length?Math.min(...last20.map(x=>n(x.close)).filter(x=>x>0)):null,resistance=last20.length?Math.max(...last20.map(x=>n(x.close)).filter(x=>x>0)):null;
 const indicators=[["RSI (14)",ind.rsi14==null?"Unavailable":fmt(ind.rsi14),ind.rsi14==null?0:ind.rsi14,""],["SMA (20)",fmt(ind.sma20),ind.sma20&&ltp?ind.sma20/ltp*100:0,""],["SMA (50)",fmt(ind.sma50),ind.sma50&&ltp?ind.sma50/ltp*100:0,""],["EMA (12)",fmt(ind.ema12),ind.ema12&&ltp?ind.ema12/ltp*100:0,""],["EMA (26)",fmt(ind.ema26),ind.ema26&&ltp?ind.ema26/ltp*100:0,""],["Relative volume",ind.relative_volume==null?"Unavailable":fmt(ind.relative_volume,2)+"×",ind.relative_volume==null?0:Math.min(100,ind.relative_volume*40),""],["MACD histogram",ind.macd?.histogram==null?"Unavailable":fmt(ind.macd.histogram),ind.macd?.histogram==null?0:Math.min(100,50+ind.macd.histogram*5),""]];
 $("detail-content").innerHTML='<div class="company-status '+(sourceVerified?'verified':'locked')+'"><div><small>RESEARCH STATUS · NOT AN ORDER</small><strong>'+esc(tradeStatus)+'</strong><p>'+esc(statusWhy)+'</p></div><span>'+(sourceVerified?'SOURCE VERIFIED':'SOURCE UNVERIFIED')+'</span></div><div class="detail-hero"><div><small>LAST TRADED PRICE</small><strong>NPR '+fmt(ltp)+'</strong><span class="'+(p>=0?"positive":"negative")+'">'+(p>0?"+":"")+fmt(p)+'% session change</span></div><div class="detail-tags"><span>'+esc(stock.symbol)+'</span><span>'+history.length+' history rows</span></div></div>'+miniChart(history)+'<div class="detail-grid"><div class="detail-card"><h3>Market snapshot</h3>'+bar("Previous close",null,"NPR "+fmt(stock.previousClose),stock.previousClose&&ltp?stock.previousClose/ltp*100:50)+bar("Open",null,"NPR "+fmt(stock.open),stock.open&&ltp?stock.open/ltp*100:50)+bar("Absolute change",null,(n(stock.change)>0?"+":"")+"NPR "+fmt(stock.change),Math.min(100,50+(n(stock.change)||0)))+bar("Day high",null,"NPR "+fmt(hi),hi&&ltp?ltp/hi*100:0)+bar("Day low",null,"NPR "+fmt(lo),lo&&ltp?lo/ltp*100:0)+bar("Day range position",null,fmt(range,0)+"%",range,p>=0?"positive":"negative")+bar("Traded volume",null,fmt(vol,0),Math.min(100,Math.log10(vol+1)*20))+bar("Turnover",null,"NPR "+fmt(to,0),Math.min(100,Math.log10(to+1)*10))+'</div><div class="detail-card"><h3>Technical indicators</h3>'+indicators.map(x=>bar(x[0],null,x[1],x[2])).join("")+'<p class="detail-note">Indicators are shown only when historical data is available. Missing values are not estimated.</p></div><div class="detail-card"><h3>Historical levels · last 20 observations</h3>'+bar("Observed support proxy",null,support==null?"Unavailable":"NPR "+fmt(support),support&&ltp?support/ltp*100:0)+bar("Observed resistance proxy",null,resistance==null?"Unavailable":"NPR "+fmt(resistance),resistance&&ltp?resistance/ltp*100:0)+'<p class="detail-note">These are simple recent-window extrema, not validated support/resistance zones.</p></div><div class="detail-card"><h3>Available company fields</h3>'+bar("Company",null,stock.name||"Not supplied",100)+bar("Sector",null,stock.sector&&stock.sector!=="Other"?stock.sector:"Not supplied",stock.sector&&stock.sector!=="Other"?100:0)+bar("Trades",null,fmt(stock.trades,0),Math.min(100,(n(stock.trades)||0)))+bar("Market capitalization",null,stock.marketCap==null?"Not supplied":"NPR "+fmt(stock.marketCap,0),stock.marketCap==null?0:100)+bar("Last quote timestamp",null,stock.lastUpdated||"Not supplied",stock.lastUpdated?100:0)+'<p class="detail-note">Fundamentals such as EPS, P/E, book value, dividends, financial statements and ownership are not present in this feed. They are not fabricated.</p></div><div class="detail-card"><h3>Fundamentals & corporate actions</h3>'+bar("EPS",null,"Not supplied",0)+bar("P/E ratio",null,"Not supplied",0)+bar("P/B ratio",null,"Not supplied",0)+bar("Book value per share",null,"Not supplied",0)+bar("Dividend / bonus history",null,"Not supplied",0)+bar("Paid-up capital / shares",null,"Not supplied",0)+bar("Promoter / public holding",null,"Not supplied",0)+bar("Quarterly financials",null,"Not supplied",0)+'<p class="detail-note">A licensed or official company-fundamentals source is required to populate these fields.</p></div></div>';
}
function risk(){
 const c=n($("capital").value),p=n($("risk-pct").value),e=n($("entry").value),s=n($("stop").value);
 if(!c||!p||!e||!s||e<=s||s<=0){$("shares").textContent="—";$("risk-amount").textContent="NPR —";$("position-value").textContent="NPR —";return}
 const qty=Math.floor(c*p/100/(e-s));$("shares").textContent=fmt(qty,0);$("risk-amount").textContent="NPR "+fmt(qty*(e-s),0);$("position-value").textContent="NPR "+fmt(qty*e,0);
}
function renderSignals(data){
 if(data.status==="LOCKED_UNVERIFIED_SOURCE"){ $("signal-status").innerHTML='<div class="empty-icon">⚠</div><b>Trade engine locked</b><p>Independent source verification has not passed. No actionable trade calls are published.</p>'; return; }
 const list=Array.isArray(data.signals)?data.signals:[];
 const buy=list.filter(x=>x.action==="BUY ON CONFIRMATION"),watch=list.filter(x=>x.action==="WATCH BREAKOUT"),sell=list.filter(x=>String(x.action||"").startsWith("SELL")),avoid=list.filter(x=>x.action==="AVOID"),wait=list.filter(x=>x.action==="WAIT");
 const top=[...buy,...watch,...sell,...avoid,...wait].slice(0,10);
 const cards=top.map(x=>{
  const cls=x.action==="BUY ON CONFIRMATION"?"positive":x.action==="AVOID"||String(x.action).startsWith("SELL")?"negative":"muted";
  return '<div class="signal-row"><div><b><a href="/nepse/'+encodeURIComponent(x.symbol.toLowerCase())+'"> '+esc(x.symbol)+'</a></b><small>'+esc(x.name||"")+'</small></div><span class="'+cls+'">'+esc(x.action)+'</span><div class="signal-levels"><small>Score '+fmt(x.score,1)+' · LTP NPR '+fmt(x.ltp)+'</small><small>Entry '+fmt(x.entry)+' / Stop '+fmt(x.stop)+' / T1 '+fmt(x.target1)+' / T2 '+fmt(x.target2)+'</small></div></div>';
 }).join("");
 $("signal-status").innerHTML='<div class="signal-summary"><span>BUY '+buy.length+'</span><span>WATCH '+watch.length+'</span><span>SELL REVIEW '+sell.length+'</span><span>AVOID '+avoid.length+'</span></div><div class="signal-list">'+(cards||'<p>No eligible stock passed the liquidity and data-quality filters.</p>')+'</div><p class="signal-disclaimer">Generated '+esc(dateText(new Date(data.generatedAt)))+'. '+esc(data.warning||"Heuristic screening only; not a profit guarantee.")+'</p>';
}
async function load(){
 $("refresh").disabled=true;$("refresh").textContent="↻ Loading";
 try{
  const r=await fetch("./data/live.json?v="+Date.now(),{cache:"no-store"});if(!r.ok)throw Error("Market data request failed ("+r.status+")");
  const l=await r.json(),fresh=freshness(l);market(l);
  const route=decodeURIComponent(location.pathname.split("/").filter(Boolean).pop()||"").trim().toUpperCase();
  if(route&&route!=="NEPSE"&&route!=="INDEX.HTML"&&S.stocks.some(x=>x.symbol===route)){openStock(route);return;}
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
 $("stock-rows").addEventListener("click",e=>{const tr=e.target.closest("tr[data-symbol]");if(tr)siteNavigate('/nepse/'+encodeURIComponent(tr.dataset.symbol.toLowerCase()))});$("stock-rows").addEventListener("keydown",e=>{if((e.key==="Enter"||e.key===" ")&&e.target.matches("tr[data-symbol]")){e.preventDefault();siteNavigate('/nepse/'+encodeURIComponent(e.target.dataset.symbol.toLowerCase()))}});$("detail-close").addEventListener("click",()=>{const path=location.pathname.split("/").filter(Boolean);if(path.length>1&&path[path.length-1].toUpperCase()!=="INDEX.HTML")siteNavigate("/nepse/");else $("stock-detail").classList.add("hidden")});$("prev").addEventListener("click",()=>{S.page--;rows()});$("next").addEventListener("click",()=>{S.page++;rows()});$("refresh").addEventListener("click",load);
 ["capital","risk-pct","entry","stop"].forEach(id=>$(id).addEventListener("input",risk));load();
}
document.addEventListener("DOMContentLoaded",init);
})();