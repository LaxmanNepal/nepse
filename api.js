/* NEPSE Pulse data layer — local-first, cached, source-agnostic. */
const NEPSE_LOCAL = './data/';
const NEPSE_EXTERNAL = window.NEPSE_API_BASE || 'https://shubhamnpk.github.io/yonepse/data/';
const NEPSE_CACHE_TTL = 60_000;

function npNormalizeStock(s = {}) {
  const ltp = Number(s.ltp ?? s.lastTradedPrice ?? s.lastPrice ?? s.price ?? 0);
  const change = Number(s.change ?? s.pointChange ?? s.changeAmount ?? 0);
  const previous = Number(s.previous_close ?? s.previousClose ?? (ltp - change));
  const percent = Number(s.percent_change ?? s.percentChange ?? s.percentageChange ?? (previous ? change / previous * 100 : 0));
  return {
    ...s,
    symbol: String(s.symbol ?? s.ticker ?? s.securitySymbol ?? '').trim().toUpperCase(),
    name: String(s.name ?? s.companyName ?? s.company ?? s.securityName ?? '').trim(),
    ltp, previous, change, percentChange: Number.isFinite(percent) ? percent : 0,
    open: Number(s.open ?? s.openPrice ?? 0),
    high: Number(s.high ?? s.highPrice ?? 0), low: Number(s.low ?? s.lowPrice ?? 0),
    volume: Number(s.volume ?? s.totalTradedQuantity ?? 0),
    turnover: Number(s.turnover ?? s.totalTradedValue ?? 0),
    trades: Number(s.trades ?? s.totalTrades ?? 0)
  };
}

function unwrapStocks(raw) {
  const list = Array.isArray(raw) ? raw : (raw?.data || raw?.stocks || raw?.items || []);
  return list.map(npNormalizeStock).filter(x => x.symbol);
}

async function readJson(url) {
  const response = await fetch(url, {cache: 'no-store'});
  if (!response.ok) throw new Error(`${response.status} ${url}`);
  return response.json();
}

async function nepseFetch(path, {ttl = NEPSE_CACHE_TTL, localFirst = true} = {}) {
  const key = `nepse:${path}`;
  try {
    const cached = JSON.parse(sessionStorage.getItem(key) || 'null');
    if (cached && Date.now() - cached.time < ttl) return cached.value;
  } catch (_) {}

  const candidates = localFirst
    ? [`${NEPSE_LOCAL}${path}`, `${NEPSE_EXTERNAL}${path}`]
    : [`${NEPSE_EXTERNAL}${path}`, `${NEPSE_LOCAL}${path}`];
  let lastError;
  for (const url of candidates) {
    try {
      const value = await readJson(url);
      try { sessionStorage.setItem(key, JSON.stringify({time: Date.now(), value})); } catch (_) {}
      return value;
    } catch (error) { lastError = error; }
  }
  throw lastError || new Error(`Unable to load ${path}`);
}

async function loadStocks() {
  return unwrapStocks(await nepseFetch('live.json'));
}

async function loadStock(symbol) {
  const s = String(symbol || '').trim().toLowerCase();
  if (!s) throw new Error('Missing stock symbol');
  const raw = await nepseFetch(`../stock/${encodeURIComponent(s)}/data.json`, {ttl: 60_000});
  return { ...raw, stock: npNormalizeStock(raw.stock || raw) };
}

async function loadIndexHistory() {
  return nepseFetch('index-history.json', {ttl: 60_000});
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

window.NEPSEData = {fetch: nepseFetch, loadStocks, loadStock, loadIndexHistory, normalizeStock: npNormalizeStock, nepaliNow, isNepseMarketWindow};
