# Use this repository as a Claude Skill

Copy the instruction below into Claude after making this repository available to Claude:

> Use `LaxmanNepal/nepse` as my NEPSE short-term trading skill and data source. Read `CLAUDE.md` and `skills/claude-nepse-trader/SKILL.md` first. Then read the latest `data/live.json` and `data/ai-signals.json`. Do not use stale data. During Nepal market hours, reject data older than 15 minutes as live trading data. When I ask `LIVE MARKET`, show the current NEPSE state and data timestamp. When I ask `TOP 5`, rank the best short-term BUY/BUY ON BREAKOUT setups from the current signal file. When I ask about a symbol, cross-check its raw record and return BUY, SELL, HOLD, WAIT or AVOID with current LTP, entry, stop, targets, risk/reward, confidence and the exact data timestamp. Never guarantee profit and never invent missing indicators. If the repository data is stale or conflicting, say `WAIT — DATA NOT FRESH`.

## Useful direct files

- Live market: `https://raw.githubusercontent.com/LaxmanNepal/nepse/main/data/live.json`
- AI signals: `https://raw.githubusercontent.com/LaxmanNepal/nepse/main/data/ai-signals.json`
- Skill: `https://raw.githubusercontent.com/LaxmanNepal/nepse/main/skills/claude-nepse-trader/SKILL.md`
- Rules: `https://raw.githubusercontent.com/LaxmanNepal/nepse/main/CLAUDE.md`

## Example requests

- `LIVE MARKET`
- `TOP 5`
- `Analyze TPKHL`
- `BUY SETUP with NPR 170000 capital and 1% max risk`
- `SELL CHECK`
- `Calculate position size for TPKHL`

The repository is a near-live research system, not an official exchange trading terminal. GitHub Actions refreshes the normalized dataset on a schedule and may be delayed. The data source is a community YONEPSE dataset.
