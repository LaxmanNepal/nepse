<canvas id="priceChart"></canvas>
<script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
<script>
  const ctx = document.getElementById('priceChart').getContext('2d');
  const chart = new Chart(ctx, {
    type: 'line',
    data: {
      labels: ['Mon', 'Tue', 'Wed', 'Thu', 'Fri'],
      datasets: [{
        label: 'NABIL Price',
        data: [430, 435, 432, 438, 440],
        borderColor: 'rgb(75, 192, 192)',
        tension: 0.3
      }]
    },
    options: { responsive: true }
  });
</script>
