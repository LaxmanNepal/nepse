const stocks = [
  {
    name: "NABIL",
    ltp: 435,
    change: 2.5,
    volume: 12400,
    history: [420, 425, 430, 432, 435] // last 5 days
  },
  {
    name: "RHPC",
    ltp: 210,
    change: 3.1,
    volume: 20000,
    history: [198, 202, 205, 208, 210]
  },
  {
    name: "NLIC",
    ltp: 702,
    change: -0.4,
    volume: 5300,
    history: [710, 708, 705, 703, 702]
  }
];

function renderStocks(data) {
  const grid = document.getElementById('stockGrid');
  grid.innerHTML = '';
  data.forEach(stock => {
    const card = document.createElement('div');
    card.className = 'stock-card';
    card.innerHTML = `
      <div class="stock-title">${stock.name}</div>
      <div>LTP: Rs. ${stock.ltp}</div>
      <div>Change: <span class="${stock.change >= 0 ? 'green' : 'red'}">${stock.change}%</span></div>
      <div>Volume: ${stock.volume}</div>
      <button onclick="drawChart('${stock.name}')">📈 Show Trend</button>
      <button onclick="askGPT('Give technical and fundamental analysis of ${stock.name} in NEPSE')">🤖 AI Analyze</button>
    `;
    grid.appendChild(card);
  });
}

function filterStocks() {
  const query = document.getElementById('search').value.toUpperCase();
  const filtered = stocks.filter(s => s.name.includes(query));
  renderStocks(filtered);
}

function drawChart(stockName) {
  const stock = stocks.find(s => s.name === stockName);
  if (!stock) return;

  document.getElementById('chartSection').style.display = 'block';

  const ctx = document.getElementById('priceChart').getContext('2d');
  if (window.priceChart) window.priceChart.destroy(); // reset if exists

  window.priceChart = new Chart(ctx, {
    type: 'line',
    data: {
      labels: ['Day 1', 'Day 2', 'Day 3', 'Day 4', 'Today'],
      datasets: [{
        label: `${stock.name} LTP`,
        data: stock.history,
        borderColor: 'rgb(75, 192, 192)',
        tension: 0.3,
        fill: false
      }]
    },
    options: {
      responsive: true,
      scales: { y: { beginAtZero: false } }
    }
  });
}

async function askGPT(prompt) {
  document.getElementById("response").innerText = "🧠 Analyzing...";
  const res = await fetch("http://localhost:3000/analyze", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ prompt })
  });
  const data = await res.json();
  document.getElementById("response").innerText = data.answer;
}

function startVoice() {
  const recognition = new (window.SpeechRecognition || window.webkitSpeechRecognition)();
  recognition.lang = 'ne-NP'; // Try Nepali, fallback to en-US if not supported
  recognition.start();

  recognition.onresult = function(event) {
    const text = event.results[0][0].transcript;
    document.getElementById("search").value = text;
    filterStocks();
    askGPT(text);
  };
}

renderStocks(stocks);
