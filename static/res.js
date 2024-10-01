document.addEventListener('DOMContentLoaded', () => {
    const top10VideosData = JSON.parse(document.getElementById('top10_videos_data').textContent);
    const monthlyVideosData = JSON.parse(document.getElementById('monthly_videos_data').textContent);

    // Check if top 10 videos data is available
    if (top10VideosData && top10VideosData.labels && top10VideosData.data) {
        const ctxTop10Videos = document.getElementById('top10VideosChart').getContext('2d');
        new Chart(ctxTop10Videos, {
            type: 'bar',
            data: {
                labels: top10VideosData.labels,
                datasets: [{
                    label: 'Views',
                    data: top10VideosData.data,
                    backgroundColor: 'rgba(75, 192, 192, 0.2)',
                    borderColor: 'rgba(75, 192, 192, 1)',
                    borderWidth: 1
                }]
            },
            options: {
                responsive: true,
                plugins: {
                    legend: {
                        position: 'top',
                        align: 'end'
                    },
                    tooltip: {
                        callbacks: {
                            label: function(tooltipItem) {
                                return tooltipItem.label + ': ' + tooltipItem.raw;
                            }
                        }
                    }
                },
                scales: {
                    x: { beginAtZero: true },
                    y: { beginAtZero: true }
                }
            }
        });
    } else {
        console.error('Top 10 Videos data is missing or malformed.');
    }

    // Check if monthly videos data is available
    if (monthlyVideosData && monthlyVideosData.labels && monthlyVideosData.data) {
        const ctxMonthlyVideos = document.getElementById('monthlyVideosChart').getContext('2d');
        new Chart(ctxMonthlyVideos, {
            type: 'bar',
            data: {
                labels: monthlyVideosData.labels,
                datasets: [{
                    label: 'Number of Videos',
                    data: monthlyVideosData.data,
                    backgroundColor: 'rgba(153, 102, 255, 0.2)',
                    borderColor: 'rgba(153, 102, 255, 1)',
                    borderWidth: 1
                }]
            },
            options: {
                responsive: true,
                plugins: {
                    legend: {
                        position: 'top',
                        align: 'end'
                    },
                    tooltip: {
                        callbacks: {
                            label: function(tooltipItem) {
                                return tooltipItem.label + ': ' + tooltipItem.raw;
                            }
                        }
                    }
                },
                scales: {
                    x: { beginAtZero: true },
                    y: { beginAtZero: true }
                }
            }
        });
    } else {
        console.error('Monthly Videos data is missing or malformed.');
    }
});
