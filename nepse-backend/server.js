const express = require("express");
const axios = require("axios");
const cheerio = require("cheerio");
const cors = require("cors");

const app = express();
app.use(cors());

app.get("/stocks", async (req, res) => {
  try {
    const { data } = await axios.get("https://merolagani.com/LatestMarket.aspx");
    const $ = cheerio.load(data);

    const rows = $("#ctl00_ContentPlaceHolder1_divLatestMarket table tr");
    const stocks = [];

    rows.each((i, row) => {
      const cols = $(row).find("td");
      if (cols.length > 1) {
        const name = $(cols[0]).text().trim();
        const ltp = parseFloat($(cols[2]).text().trim());
        const change = parseFloat($(cols[4]).text().trim());
        const volume = parseInt($(cols[10]).text().replace(/,/g, '').trim());

        if (!isNaN(ltp) && !isNaN(change)) {
          stocks.push({ name, ltp, change, volume });
        }
      }
    });

    res.json(stocks);
  } catch (err) {
    console.error("Error scraping:", err.message);
    res.status(500).json({ error: "Failed to fetch NEPSE data" });
  }
});

const PORT = process.env.PORT || 3000;
app.listen(PORT, () => console.log(`✅ Server running on http://localhost:${PORT}`));

