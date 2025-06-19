const dummyStocks = [
  { name: "NABIL", ltp: 435, change: +2.5, volume: 12400 },
  { name: "RHPC", ltp: 210, change: +3.1, volume: 20000 },
  { name: "NLIC", ltp: 702, change: -0.4, volume: 5300 },
];

function renderStocks(data) {
  const grid = document.getElementById("stockGrid");
  grid.innerHTML = "";
  data.forEach(stock => {
    const card = document.createElement("div");
    card.className = "stock-card";
    card.innerHTML = `
      <h3>${stock.name}</h3>
      <p>LTP: Rs. ${stock.ltp}</p>
      <p>Change: <span class="${stock.change >= 0 ? 'green' : 'red'}">${stock.change}%</span></p>
      <p>Volume: ${stock.volume}</p>
      <button onclick="askGPT('Give short analysis of ${stock.name} in NEPSE')">🤖 AI Analyze</button>
    `;
    grid.appendChild(card);
  });
}

function filterStocks() {
  const query = document.getElementById("search").value.toUpperCase();
  const filtered = dummyStocks.filter(s => s.name.includes(query));
  renderStocks(filtered);
}

// 🔗 AI Integration (calls your backend)
async function askGPT(prompt) {
  document.getElementById("response").innerText = "Analyzing...";
  const res = await fetch("http://localhost:3000/analyze", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ prompt })
  });
  const data = await res.json();
  document.getElementById("response").innerText = data.answer;
}

// 🎙️ Voice Support
function startVoice() {
  const recognition = new (window.SpeechRecognition || window.webkitSpeechRecognition)();
  recognition.lang = 'en-US';
  recognition.start();
  recognition.onresult = function(event) {
    const text = event.results[0][0].transcript;
    document.getElementById("search").value = text;
    filterStocks();
    askGPT(text); // Also trigger AI if question-like
  };
}

renderStocks(dummyStocks);
