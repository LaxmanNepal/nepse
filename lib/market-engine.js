/**
 * NEPSE Pulse canonical market intelligence engine.
 * Pure functions: safe to run in browser, Node, or GitHub Actions.
 */

const finite = (value) => Number.isFinite(Number(value)) ? Number(value) : null;

function normalizeStock(row = {}) {
  return {
    symbol: String(row.symbol || row.ticker || '').trim().toUpperCase(),
    name: row.name ?? row.companyName ?? null,
    sector: row.sector ?? row.sectorName ?? 'Other',
    ltp: finite(row.ltp ?? row.price ?? row.lastPrice),
    previousClose: finite(row.previousClose ?? row.previous_close ?? row.prevClose),
    change: finite(row.change ?? row.changeValue),
    changePercent: finite(row.changePercent ?? row.percent_change ?? row.perChange),
    open: finite(row.open ?? row.openPrice),
    high: finite(row.high ?? row.dayHigh),
    low: finite(row.low ?? row.dayLow),
    volume: finite(row.volume ?? row.quantity ?? row.totalTradedQuantity),
    turnover: finite(row.turnover ?? row.totalTurnover),
    trades: finite(row.trades ?? row.totalTrades),
    marketCap: finite(row.marketCap ?? row.market_cap),
    lastUpdated: row.lastUpdated ?? row.last_updated ?? null,
  };
}

function normalizeSnapshot(snapshot = {}) {
  const stocks = Array.isArray(snapshot.stocks) ? snapshot.stocks.map(normalizeStock).filter(s => s.symbol) : [];
  return {
    updatedAt: snapshot.updatedAt ?? null,
    source: snapshot.source ?? null,
    sourceUpdatedAt: snapshot.sourceUpdatedAt ?? null,
    market: snapshot.market ?? null,
    index: snapshot.index ?? null,
    summary: snapshot.summary ?? null,
    stocks,
  };
}

function summarize(stocks) {
  const rows = stocks.map(normalizeStock);
  const classified = rows.filter(s => s.changePercent !== null || s.change !== null);
  const advancing = classified.filter(s => (s.changePercent ?? s.change ?? 0) > 0).length;
  const declining = classified.filter(s => (s.changePercent ?? s.change ?? 0) < 0).length;
  const unchanged = classified.length - advancing - declining;
  const turnover = rows.reduce((sum, s) => sum + (s.turnover ?? 0), 0);
  const volume = rows.reduce((sum, s) => sum + (s.volume ?? 0), 0);
  const trades = rows.reduce((sum, s) => sum + (s.trades ?? 0), 0);
  return {
    listed: rows.length,
    classified: classified.length,
    advancing,
    unchanged,
    declining,
    turnover,
    volume,
    trades,
    breadthRatio: declining ? advancing / declining : advancing > 0 ? Infinity : null,
  };
}

function movers(stocks, limit = 10) {
  const rows = stocks.map(normalizeStock).filter(s => s.symbol);
  const valid = rows.filter(s => s.changePercent !== null);
  return {
    gainers: [...valid].sort((a, b) => b.changePercent - a.changePercent).slice(0, limit),
    losers: [...valid].sort((a, b) => a.changePercent - b.changePercent).slice(0, limit),
    turnover: [...rows].filter(s => s.turnover !== null).sort((a, b) => b.turnover - a.turnover).slice(0, limit),
    volume: [...rows].filter(s => s.volume !== null).sort((a, b) => b.volume - a.volume).slice(0, limit),
  };
}

function sectorPerformance(stocks) {
  const groups = new Map();
  for (const stock of stocks.map(normalizeStock)) {
    const key = stock.sector || 'Other';
    if (!groups.has(key)) groups.set(key, []);
    groups.get(key).push(stock);
  }
  return [...groups.entries()].map(([sector, rows]) => {
    const valid = rows.filter(s => s.changePercent !== null);
    const avgChangePercent = valid.length ? valid.reduce((sum, s) => sum + s.changePercent, 0) / valid.length : null;
    const turnover = rows.reduce((sum, s) => sum + (s.turnover ?? 0), 0);
    return { sector, stocks: rows.length, advancing: valid.filter(s => s.changePercent > 0).length, declining: valid.filter(s => s.changePercent < 0).length, unchanged: valid.filter(s => s.changePercent === 0).length, avgChangePercent, turnover };
  }).sort((a, b) => (b.avgChangePercent ?? -Infinity) - (a.avgChangePercent ?? -Infinity));
}

function screen(stocks, rules = {}) {
  return stocks.map(normalizeStock).filter(s => {
    if (rules.minPrice != null && (s.ltp == null || s.ltp < rules.minPrice)) return false;
    if (rules.maxPrice != null && (s.ltp == null || s.ltp > rules.maxPrice)) return false;
    if (rules.minChangePercent != null && (s.changePercent == null || s.changePercent < rules.minChangePercent)) return false;
    if (rules.maxChangePercent != null && (s.changePercent == null || s.changePercent > rules.maxChangePercent)) return false;
    if (rules.minTurnover != null && (s.turnover == null || s.turnover < rules.minTurnover)) return false;
    if (rules.sector && s.sector !== rules.sector) return false;
    return true;
  });
}

function snapshotHealth(snapshot, now = Date.now()) {
  const s = normalizeSnapshot(snapshot);
  const ageSeconds = s.sourceUpdatedAt ? Math.max(0, (now - Date.parse(s.sourceUpdatedAt)) / 1000) : null;
  const freshness = ageSeconds == null || !Number.isFinite(ageSeconds) ? 'unknown' : ageSeconds <= 300 ? 'fresh' : ageSeconds <= 900 ? 'aging' : 'stale';
  return { freshness, ageSeconds, stocks: s.stocks.length, hasIndex: Boolean(s.index), hasSource: Boolean(s.source), valid: s.stocks.length > 0 && Boolean(s.updatedAt) };
}

module.exports = { normalizeStock, normalizeSnapshot, summarize, movers, sectorPerformance, screen, snapshotHealth };
