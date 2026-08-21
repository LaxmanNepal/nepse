/* NEPSE Pulse data layer — browser-safe, cached, source-agnostic. */
const NEPSE_API = window.NEPSE_API_BASE || 'https://shubhamnpk.github.io/yonepse/data/';
const NEPSE_CACHE_TTL = 60_000;

function npNormalizeStock(s = {}) {
  const ltp = Number(s.ltp ?? s.lastTradedPrice ?? s.lastPrice ?? s.price ?? 0);
  const change = Number(s.change ?? s.pointChange ?? s.changeAmount ?? 0);
  return {
    ...s,
    symbol: String(s.symbol ?? s.ticker ?? s.securitySymbol ?? '').trim(),
    name: String(s.name ?? s.companyName ?? s.company ?? s.securityName ?? '').trim(),
    ltp,
    previous: Number(s.previous_close ?? s.previousClose ?? ltp - change),
    change,
    percentChange: Number(s.percent_change ?? s.percentChange ?? s.percentageChange ?? (ltp - change ? change / (ltp - change) * 100 : 0)),
    high: Number(s.high ?? 0), low: Number(s.low ?? 0),
    volume: Number(s.volume ?? s.totalTradedQuantity ?? 0),
    turnover: Number(s.turnover ?? s.totalTradedValue ?? 0),
    trades: Number(s.trades ?? s.totalTrades ?? 0)
  };
}

async function nepseFetch(path, {ttl = NEPSE_CACHE_TTL} = {}) {
  const key = `nepse:${NEPSE_API}:${path}`;
  try {
    const cached = JSON.parse(sessionStorage.getItem(key) || 'null');
    if (cached && Date.now() - cached.time < ttl) return cached.value;
  } catch (_) {}
  const response = await fetch(NEPSE_API + path, {cache: 'no-store'});
  if (!response.ok) throw new Error(`NEPSE source ${response.status}`);
  const value = await response.json();
  try { sessionStorage.setItem(key, JSON.stringify({time: Date.now(), value})); } catch (_) {}
  return value;
}

async function loadStocks() {
  const raw = await nepseFetch('nepse_data.json');
  const list = Array.isArray(raw) ? raw : (raw.data || raw.stocks || []);
  return list.map(npNormalizeStock).filter(x => x.symbol);
}

function nepaliNow() {
  const date = new Date();
  return {
    date,
    bs: new Intl.DateTimeFormat('ne-NP-u-ca-bikram-sambat', {year:'numeric', month:'long', day:'numeric', weekday:'long', timeZone:'Asia/Kathmandu'}).format(date),
    time: new Intl.DateTimeFormat('ne-NP', {hour:'2-digit', minute:'2-digit', second:'2-digit', hour12:true, timeZone:'Asia/Kathmandu'}).format(date)
  };
}

function isNepseMarketWindow(date = new Date()) {
  const weekday = new Intl.DateTimeFormat('en-US', {weekday:'short', timeZone:'Asia/Kathmandu'}).format(date);
  const parts = new Intl.DateTimeFormat('en-US', {hour:'2-digit', minute:'2-digit', hour12:false, timeZone:'Asia/Kathmandu'}).formatToParts(date);
  const h = Number(parts.find(x => x.type === 'hour').value);
  const m = Number(parts.find(x => x.type === 'minute').value);
  return ['Mon','Tue','Wed','Thu','Fri'].includes(weekday) && (h > 11 || (h === 11 && m >= 0)) && (h < 15 || (h === 15 && m === 0));
}

window.NEPSEData = {fetch: nepseFetch, loadStocks, normalizeStock: npNormalizeStock, nepaliNow, isNepseMarketWindow};
