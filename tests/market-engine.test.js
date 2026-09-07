const assert = require('node:assert/strict');
const test = require('node:test');
const engine = require('../lib/market-engine');

const stocks = [
  { symbol: 'AAA', name: 'Alpha', sector: 'Banking', ltp: 110, previousClose: 100, change: 10, changePercent: 10, turnover: 1000, volume: 10 },
  { symbol: 'BBB', name: 'Beta', sector: 'Hydro', ltp: 95, previousClose: 100, change: -5, changePercent: -5, turnover: 500, volume: 5 },
  { symbol: 'CCC', name: 'Gamma', sector: 'Banking', ltp: 100, previousClose: 100, change: 0, changePercent: 0, turnover: 200, volume: 2 },
];

test('normalizes stock fields', () => {
  const stock = engine.normalizeStock({ ticker: ' aaa ', price: '110', previous_close: '100', percent_change: '10' });
  assert.equal(stock.symbol, 'AAA');
  assert.equal(stock.ltp, 110);
  assert.equal(stock.previousClose, 100);
  assert.equal(stock.changePercent, 10);
});

test('summarizes market breadth', () => {
  const summary = engine.summarize(stocks);
  assert.deepEqual({ advancing: summary.advancing, unchanged: summary.unchanged, declining: summary.declining }, { advancing: 1, unchanged: 1, declining: 1 });
  assert.equal(summary.turnover, 1700);
});

test('returns ranked movers', () => {
  const result = engine.movers(stocks, 2);
  assert.deepEqual(result.gainers.map(s => s.symbol), ['AAA', 'CCC']);
  assert.deepEqual(result.losers.map(s => s.symbol), ['BBB', 'CCC']);
});

test('aggregates sectors', () => {
  const result = engine.sectorPerformance(stocks);
  assert.equal(result.find(s => s.sector === 'Banking').stocks, 2);
});

test('screens by rules', () => {
  const result = engine.screen(stocks, { minChangePercent: 1, minTurnover: 900 });
  assert.deepEqual(result.map(s => s.symbol), ['AAA']);
});

test('reports snapshot health', () => {
  const snapshot = { updatedAt: '2026-09-07T10:00:00Z', source: 'test', sourceUpdatedAt: '2026-09-07T09:59:00Z', index: { value: 3000 }, stocks };
  const health = engine.snapshotHealth(snapshot, Date.parse('2026-09-07T10:00:00Z'));
  assert.equal(health.freshness, 'fresh');
  assert.equal(health.valid, true);
});
