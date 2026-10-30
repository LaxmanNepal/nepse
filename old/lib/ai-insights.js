const { normalizeSnapshot, summarize, movers, sectorPerformance, snapshotHealth } = require('./market-engine');

const pct = (v) => v == null || !Number.isFinite(v) ? 'n/a' : `${v.toFixed(2)}%`;

function buildMarketBrief(snapshot, now = Date.now()) {
  const data = normalizeSnapshot(snapshot);
  const metrics = summarize(data.stocks);
  const ranked = movers(data.stocks, 5);
  const sectors = sectorPerformance(data.stocks);
  const health = snapshotHealth(data, now);
  const observations = [];

  if (metrics.advancing > metrics.declining) observations.push(`Breadth is positive: ${metrics.advancing} advancing vs ${metrics.declining} declining.`);
  else if (metrics.declining > metrics.advancing) observations.push(`Breadth is negative: ${metrics.declining} declining vs ${metrics.advancing} advancing.`);
  else observations.push(`Breadth is balanced: ${metrics.advancing} advancing and ${metrics.declining} declining.`);

  const best = sectors[0];
  const worst = [...sectors].sort((a, b) => (a.avgChangePercent ?? Infinity) - (b.avgChangePercent ?? Infinity))[0];
  if (best?.avgChangePercent != null) observations.push(`Best sector: ${best.sector} (${pct(best.avgChangePercent)} average move).`);
  if (worst?.avgChangePercent != null && worst.sector !== best?.sector) observations.push(`Weakest sector: ${worst.sector} (${pct(worst.avgChangePercent)} average move).`);
  if (ranked.gainers[0]) observations.push(`Top gainer: ${ranked.gainers[0].symbol} (${pct(ranked.gainers[0].changePercent)}).`);
  if (ranked.losers[0]) observations.push(`Top loser: ${ranked.losers[0].symbol} (${pct(ranked.losers[0].changePercent)}).`);

  return { generatedAt: new Date(now).toISOString(), freshness: health.freshness, observations, metrics, leaders: ranked, sectors, disclaimer: 'Informational market summary only; not personalized investment advice.' };
}

module.exports = { buildMarketBrief };
