// chart.js - Initializes the event registration chart
document.addEventListener('DOMContentLoaded', function() {
    // Get the chart data element
    const chartDataElement = document.getElementById('chart-data');
    
    if (!chartDataElement) {
        console.error('Chart data element not found');
        return;
    }
    
    try {
        // Parse the JSON data from data attributes
        const labels = JSON.parse(chartDataElement.getAttribute('data-labels'));
        const data = JSON.parse(chartDataElement.getAttribute('data-data'));
        
        // Get the canvas element
        const ctx = document.getElementById('eventChart');
        
        if (!ctx) {
            console.error('Chart canvas not found');
            return;
        }
        
        // Create the chart
        new Chart(ctx, {
            type: 'bar',
            data: {
                labels: labels,
                datasets: [{
                    label: 'Registration Count',
                    data: data,
                    backgroundColor: 'rgba(13, 110, 253, 0.6)', // Bootstrap primary color
                    borderColor: 'rgba(13, 110, 253, 1)',
                    borderWidth: 1
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: {
                        display: true,
                        position: 'top',
                    },
                    tooltip: {
                        callbacks: {
                            title: function(tooltipItems) {
                                return tooltipItems[0].label;
                            },
                            label: function(context) {
                                return 'Registrations: ' + context.raw;
                            }
                        }
                    }
                },
                scales: {
                    y: {
                        beginAtZero: true,
                        title: {
                            display: true,
                            text: 'Number of Registrations'
                        }
                    },
                    x: {
                        title: {
                            display: true,
                            text: 'Events'
                        },
                        ticks: {
                            autoSkip: false,
                            maxRotation: 45,
                            minRotation: 45
                        }
                    }
                }
            }
        });
        
        console.log('Chart initialized successfully');
    } catch (error) {
        console.error('Error initializing chart:', error);
        // Log the data that failed to parse for debugging
        console.error('data-labels:', chartDataElement.getAttribute('data-labels'));
        console.error('data-data:', chartDataElement.getAttribute('data-data'));
    }
});