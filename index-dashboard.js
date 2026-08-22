(() => {
  const BASE = (window.NEPSE_API_BASE || 'https://shubhamnpk.github.io/yonepse/data').replace(/\/$/, '');
  const $ = id => document.getElementById(id);
  let indexRows = [];
  let currentRange = '1d';
  let canvas, ctx;

  const fmt = n => Number(n || 0).toLocaleString('en-IN', {maximumFractionDigits: 2});
  const signed = n => `${Number(n || 0) >= 0 ? '+' : ''}${Number(n || 0).toFixed(2)}`;
  const signedPct = n => `${Number(n || 0) >= 0 ? '+' : ''}${Number(n || 0).toFixed(2)}%`;

  async function get(url) {
    const r = await fetch(url, {cache:'no-store'});
    if (!r.ok) throw new Error(`${r.status} ${url}`);
    return r.json();
  }

  function findNepse(raw) {
    const rows = Array.isArray(raw) ? raw : (raw.items || raw.data || raw.indices || []);
    return rows.find(x => String(x.index || x.name || '').toLowerCase().includes('nepse')) || rows[0] || null;
  }

  function normalizeCurrent(x) {
    if (!x) return null;
    const value = Number(x.currentValue ?? x.close ?? x.indexValue ?? 0);
    const prev = Number(x.previousClose ?? x.previous_close ?? 0);
    const change = Number(x.change ?? (value - prev));
    const per = Number(x.perChange ?? x.percentChange ?? (prev ? change / prev * 100 : 0));
    return {value, prev, change, per, high:Number(x.high ?? 0), low:Number(x.low ?? 0), fiftyHigh:Number(x.fiftyTwoWeekHigh ?? 0), fiftyLow:Number(x.fiftyTwoWeekLow ?? 0), time:x.generatedTime || x.lastUpdated || ''};
  }

  function normalizeHistory(raw) {
    const rows = Array.isArray(raw) ? raw : (raw.history || raw.data || raw.rows || []);
    return rows.map(x => ({
      date: String(x.date || x.businessDate || x.tradingDate || '').slice(0,10),
      value: Number(x.value ?? x.close ?? x.closingIndex ?? x.indexValue ?? x.currentValue ?? 0)
    })).filter(x => x.date && Number.isFinite(x.value) && x.value > 0).sort((a,b) => a.date.localeCompare(b.date));
  }

  function rangeStart(range) {
    const d = new Date();
    if (range === '1d') return new Date(d.getTime() - 24*3600*1000);
    if (range === '7d') return new Date(d.getTime() - 7*24*3600*1000);
    if (range === '1m') { d.setMonth(d.getMonth()-1); return d; }
    if (range === '3m') { d.setMonth(d.getMonth()-3); return d; }
    if (range === '6m') { d.setMonth(d.getMonth()-6); return d; }
    d.setFullYear(d.getFullYear()-5); return d;
  }

  function draw(rows) {
    if (!canvas) canvas = $('nepseIndexChart');
    if (!canvas) return;
    const wrap = canvas.parentElement;
    const w = Math.max(320, wrap.clientWidth || 800), h = 310, ratio = window.devicePixelRatio || 1;
    canvas.width = w * ratio; canvas.height = h * ratio; canvas.style.width = `${w}px`; canvas.style.height = `${h}px`;
    ctx = canvas.getContext('2d'); ctx.setTransform(ratio,0,0,ratio,0,0); ctx.clearRect(0,0,w,h);
    if (!rows.length) { $('chartEmpty').hidden = false; return; }
    $('chartEmpty').hidden = true;
    const pad = {l:12,r:12,t:18,b:28};
    const vals = rows.map(r=>r.value), min=Math.min(...vals), max=Math.max(...vals), span=Math.max(max-min, 1);
    const x=i=>pad.l+i*Math.max(1,(w-pad.l-pad.r)/(Math.max(rows.length-1,1)));
    const y=v=>pad.t+(max-v)/span*(h-pad.t-pad.b);
    ctx.strokeStyle='rgba(120,135,155,.18)'; ctx.lineWidth=1;
    for(let i=0;i<4;i++){const gy=pad.t+i*(h-pad.t-pad.b)/3;ctx.beginPath();ctx.moveTo(pad.l,gy);ctx.lineTo(w-pad.r,gy);ctx.stroke();}
    const gradient=ctx.createLinearGradient(0,pad.t,0,h); gradient.addColorStop(0,'rgba(20,184,166,.25)'); gradient.addColorStop(1,'rgba(20,184,166,0)');
    ctx.beginPath(); rows.forEach((r,i)=>{const px=x(i),py=y(r.value);i?ctx.lineTo(px,py):ctx.moveTo(px,py)}); ctx.lineTo(x(rows.length-1),h-pad.b);ctx.lineTo(x(0),h-pad.b);ctx.closePath();ctx.fillStyle=gradient;ctx.fill();
    ctx.beginPath(); rows.forEach((r,i)=>{const px=x(i),py=y(r.value);i?ctx.lineTo(px,py):ctx.moveTo(px,py)});ctx.strokeStyle='#14b8a6';ctx.lineWidth=2.5;ctx.stroke();
    ctx.fillStyle='#64748b';ctx.font='12px system-ui';
    [0,Math.floor((rows.length-1)/2),rows.length-1].forEach(i=>{if(i<0)return;const d=rows[i].date;ctx.fillText(d,Math.max(0,x(i)-28),h-8)});
    ctx.fillStyle='#334155';ctx.font='600 12px system-ui';ctx.fillText(fmt(max),pad.l,h-pad.b-8);ctx.fillText(fmt(min),pad.l, h-pad.b);
  }

  function renderCurrent(c) {
    if (!c) return;
    $('nepseValue').textContent=fmt(c.value);
    $('nepseChange').textContent=`${signed(c.change)} points · ${signedPct(c.per)}`;
    $('nepseChange').className=`nepse-change ${c.change>=0?'up':'down'}`;
    $('nepseHigh').textContent=fmt(c.high); $('nepseLow').textContent=fmt(c.low); $('nepsePrev').textContent=fmt(c.prev);
    $('nepse52High').textContent=c.fiftyHigh?fmt(c.fiftyHigh):'—'; $('nepse52Low').textContent=c.fiftyLow?fmt(c.fiftyLow):'—';
    $('nepseOpen').textContent='—';
    $('nepseIndexMeta').textContent=c.time ? `Latest index source update · ${new Date(c.time).toLocaleString('en-IN',{timeZone:'Asia/Kathmandu'})} NPT` : 'Latest available NEPSE Index';
  }

  function renderRange() {
    const start=rangeStart(currentRange), filtered=indexRows.filter(r=>new Date(`${r.date}T23:59:59+05:45`)>=start);
    draw(filtered);
    const labels={ '1d':'1 day','7d':'7 days','1m':'1 month','3m':'3 months','6m':'6 months','5y':'5 years' };
    $('chartRangeLabel').textContent=labels[currentRange];
    $('chartDataStatus').textContent=filtered.length ? `${filtered.length} trading-day points` : 'No historical points available for this range yet';
  }

  async function load() {
    try {
      const [current, localHistory] = await Promise.allSettled([
        get(`${BASE}/market/indices.json`),
        get('./data/index-history.json')
      ]);
      if (current.status === 'fulfilled') renderCurrent(normalizeCurrent(findNepse(current.value)));
      indexRows = localHistory.status === 'fulfilled' ? normalizeHistory(localHistory.value) : [];
      renderRange();
    } catch (e) { console.error('NEPSE index dashboard', e); }
  }

  document.addEventListener('click', e => {
    const b=e.target.closest('.chart-range'); if(!b)return;
    document.querySelectorAll('.chart-range').forEach(x=>x.classList.remove('active')); b.classList.add('active'); currentRange=b.dataset.range; renderRange();
  });
  window.addEventListener('resize',()=>renderRange());
  load();
  setInterval(load,60000);
})();
