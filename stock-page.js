/* Shared generated stock-page application. Each generated /stock/<symbol>/ page uses this same UI. */
(() => {
  const symbol = (location.pathname.match(/\/stock\/([^/]+)/i)?.[1] || '').toUpperCase();
  const $ = id => document.getElementById(id);
  let rows = [], chart;
  const fmt = n => Number.isFinite(Number(n)) ? Number(n).toLocaleString('en-IN',{maximumFractionDigits:2}) : '—';
  const nepaliNow = () => new Intl.DateTimeFormat('en-GB',{timeZone:'Asia/Kathmandu',dateStyle:'medium',timeStyle:'medium'}).format(new Date());
  async function load(){
    const sources = [`./data.json`,`../../data/live.json`];
    let data=null;
    for(const src of sources){try{const r=await fetch(src,{cache:'no-store'});if(r.ok){data=await r.json();break;}}catch(e){}}
    if(!data) throw new Error('Stock data unavailable');
    const all = Array.isArray(data) ? data : (data.stocks || data.data || [data]);
    rows = all.filter(x => String(x.symbol||x.Symbol||'').toUpperCase()===symbol);
    if(!rows.length && !Array.isArray(data)) rows=[data];
    const d=rows.at(-1)||{};
    $('companyName').textContent=d.companyName||d.company||d.name||symbol;
    $('symbol').textContent=symbol;
    $('sector').textContent=d.sector||'NEPSE STOCK';
    const ltp=Number(d.ltp??d.LTP??d.close??d.price); const ch=Number(d.change??d.changePercent??0);
    $('ltp').textContent=Number.isFinite(ltp)?`Rs. ${fmt(ltp)}`:'—';
    $('change').textContent=Number.isFinite(ch)?`${ch>=0?'▲':'▼'} ${fmt(Math.abs(ch))}${Math.abs(ch)<2?'%':' '}`:'—';
    $('marketStatus').textContent='Market data · '+nepaliNow();
    $('lastUpdated').textContent='Updated '+nepaliNow();
    const metrics=[['Open',d.open],['High',d.high],['Low',d.low],['Previous Close',d.previousClose??d.prevClose],['Volume',d.volume],['Turnover',d.turnover],['Transactions',d.transactions??d.trades]];
    $('metrics').innerHTML=metrics.map(([k,v])=>`<div><span>${k}</span><strong>${fmt(v)}</strong></div>`).join('');
    renderChart(); renderTechnical(d);
  }
  function renderChart(){
    const points=rows.map((r,i)=>({x:i,y:Number(r.ltp??r.close??r.price)})).filter(p=>Number.isFinite(p.y));
    if(!window.Chart || !points.length) return;
    if(chart) chart.destroy();
    chart=new Chart($('priceChart'),{type:'line',data:{datasets:[{data:points,borderWidth:2,pointRadius:0,tension:.25}]},options:{responsive:true,maintainAspectRatio:false,parsing:false,plugins:{legend:{display:false}},scales:{x:{display:false},y:{ticks:{callback:v=>'Rs. '+v}}}}});
  }
  function renderTechnical(d){
    const t=window.NEPSETechnical?.analyze?.(rows.map(r=>Number(r.ltp??r.close??r.price)).filter(Number.isFinite))||{};
    const verdict=t.verdict||'HOLD'; $('verdict').textContent=verdict; $('score').textContent=`${fmt(t.score??50)} / 100`;
    $('reasons').innerHTML=(t.reasons||['Technical signal is calculated from available market history.']).map(x=>`<li>${x}</li>`).join('');
    const vals=[['RSI 14',t.rsi],['SMA 20',t.sma20],['SMA 50',t.sma50],['EMA 20',t.ema20],['MACD',t.macd],['ADX',t.adx],['ATR',t.atr],['Bollinger',t.bollinger]];
    $('indicators').innerHTML=vals.map(([k,v])=>`<div><span>${k}</span><strong>${typeof v==='number'?fmt(v):v??'—'}</strong></div>`).join('');
  }
  load().catch(e=>{ $('companyName').textContent=symbol||'Stock'; $('marketStatus').textContent='Unable to load current stock data'; console.error(e); });
})();
