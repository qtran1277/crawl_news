document.addEventListener('DOMContentLoaded', function() {
    // Sidebar toggle functionality
    const sidebar = document.getElementById('historySidebar');
    const mainContent = document.getElementById('mainContent');
    const toggleButton = document.getElementById('historyToggle');
    
    toggleButton.addEventListener('click', function() {
        sidebar.classList.toggle('collapsed');
        mainContent.classList.toggle('expanded');
        toggleButton.classList.toggle('collapsed');
        
        // Update toggle button icon
        const icon = toggleButton.querySelector('i');
        if (sidebar.classList.contains('collapsed')) {
            icon.classList.remove('fa-chevron-left');
            icon.classList.add('fa-chevron-right');
        } else {
            icon.classList.remove('fa-chevron-right');
            icon.classList.add('fa-chevron-left');
        }
    });

    // Create sentiment chart
    try {
        // Get results from data attribute
        const resultsElement = document.getElementById('results-data');
        const articleResults = JSON.parse(resultsElement.dataset.results);
        console.log('Raw results:', articleResults);
        
        if (!articleResults || !Array.isArray(articleResults)) {
            console.error('Invalid results data:', articleResults);
            return;
        }
        
        // Create sentiment distribution chart
        const ctx = document.getElementById('sentimentChart');
        if (!ctx) {
            console.error('Canvas element not found');
            return;
        }
        
        const chartContext = ctx.getContext('2d');
        console.log('Canvas context:', chartContext);
        
        // Prepare data for chart
        const dates = articleResults.map(r => r.date ? r.date.toString() : '');
        const scores = articleResults.map(r => parseFloat(r.sentiment_score) || 0);
        const colors = articleResults.map(r => {
            if (r.sentiment === 'positive') return 'rgba(40, 167, 69, 0.7)';
            if (r.sentiment === 'negative') return 'rgba(220, 53, 69, 0.7)';
            return 'rgba(108, 117, 125, 0.7)';
        });
        
        console.log('Chart data:', { dates, scores, colors, results: articleResults });
        
        if (dates.length > 0 && scores.length > 0) {
            new Chart(chartContext, {
                type: 'bar',
                data: {
                    labels: dates,
                    datasets: [{
                        label: 'Điểm sentiment',
                        data: scores,
                        backgroundColor: colors,
                        borderColor: colors.map(color => color.replace('0.7', '1')),
                        borderWidth: 1
                    }]
                },
                options: {
                    responsive: true,
                    maintainAspectRatio: false,
                    scales: {
                        y: {
                            beginAtZero: true,
                            title: {
                                display: true,
                                text: 'Điểm sentiment'
                            }
                        },
                        x: {
                            title: {
                                display: true,
                                text: 'Ngày tháng'
                            }
                        }
                    },
                    plugins: {
                        legend: {
                            display: false
                        },
                        tooltip: {
                            callbacks: {
                                label: function(context) {
                                    const result = articleResults[context.dataIndex];
                                    return [
                                        `Tiêu đề: ${result.title}`,
                                        `Điểm: ${result.sentiment_score}`,
                                        `Cảm xúc: ${result.sentiment}`
                                    ];
                                }
                            }
                        }
                    }
                }
            });
        } else {
            console.error('No valid data for chart');
        }
    } catch (error) {
        console.error('Error creating chart:', error);
    }
}); 