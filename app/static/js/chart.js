function revenueChart(label, data) {
    const chart = document.getElementById('chart');
    new Chart(chart, {
        type: 'pie',
        data: {
          labels: label,
          datasets: [{
            label: 'Doanh thu',
            data: data,
            borderWidth: 1
          }]
        },
        options: {
          scales: {
            y: {
              beginAtZero: true
            }
          }
        }
    });
}
function frequencyChart(label, data) {
    const chart = document.getElementById('chart2');
    new Chart(chart, {
        type: 'bar',
        data: {
          labels: label,
          datasets: [{
            label: 'Số ngày thuê',
            data: data,
            borderWidth: 1
          }]
        },
        options: {
          scales: {
            y: {
              beginAtZero: true
            }
          }
        }
    });
}