async function loadLiveStocks() {
  const res = await fetch("http://localhost:3000/stocks");
  const data = await res.json();
  populateTable(data);
}

function populateTable(stocks) {
  const tbody = document.querySelector("#stockTable tbody");
  tbody.innerHTML = "";
  stocks.forEach(stock => {
    const row = document.createElement("tr");
    row.innerHTML = `
      <td>${stock.name}</td>
      <td>${stock.ltp}</td>
      <td class="${stock.change >= 0 ? 'green' : 'red'}">${stock.change}</td>
      <td class="${stock.change >= 0 ? 'green' : 'red'}">${((stock.change / (stock.ltp - stock.change)) * 100).toFixed(2)}%</td>
      <td>${stock.volume}</td>
    `;
    tbody.appendChild(row);
  });
}

function filterTable() {
  const query = document.getElementById('search').value.toUpperCase();
  const rows = document.querySelectorAll("#stockTable tbody tr");
  rows.forEach(row => {
    const company = row.children[0].textContent.toUpperCase();
    row.style.display = company.includes(query) ? "" : "none";
  });
}

loadLiveStocks();
