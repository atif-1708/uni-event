/**
 * Advanced Reports Dashboard JavaScript
 * This script handles interactive features for the event reports dashboard
 */

document.addEventListener('DOMContentLoaded', function() {
    // Initialize variables
    let charts = {};
    const colorPalette = {
        primary: 'rgba(0, 123, 255, 0.8)',
        primaryLight: 'rgba(0, 123, 255, 0.2)',
        success: 'rgba(40, 167, 69, 0.8)',
        successLight: 'rgba(40, 167, 69, 0.2)',
        danger: 'rgba(220, 53, 69, 0.8)',
        dangerLight: 'rgba(220, 53, 69, 0.2)',
        warning: 'rgba(255, 193, 7, 0.8)',
        warningLight: 'rgba(255, 193, 7, 0.2)',
        info: 'rgba(23, 162, 184, 0.8)',
        infoLight: 'rgba(23, 162, 184, 0.2)',
    };
    
    // Handle date range filter functionality
    initializeDateFilters();
    
    // Initialize charts
    if (document.getElementById('registrationTrends')) {
        initializeRegistrationTrendsChart();
    }
    
    if (document.getElementById('attendanceChart')) {
        initializeAttendanceChart();
    }
    
    // Table functionality
    if (document.getElementById('eventsTable')) {
        initializeDataTable();
    }
    
    // Initialize column toggles
    initializeColumnToggles();
    
    // Add animation to stat cards
    animateStatCards();
    
    /**
     * Initializes the date range filter functionality
     */
    function initializeDateFilters() {
        const dateRangeSelect = document.getElementById('dateRange');
        const customDateFields = document.querySelectorAll('.custom-date');
        const startDateInput = document.getElementById('startDate');
        const endDateInput = document.getElementById('endDate');
        
        if (!dateRangeSelect) return;
        
        // Handle date range selection change
        dateRangeSelect.addEventListener('change', function() {
            if (this.value === 'custom') {
                customDateFields.forEach(field => field.classList.remove('d-none'));
            } else {
                customDateFields.forEach(field => field.classList.add('d-none'));
                
                // Auto-submit the form if not custom date range
                document.getElementById('reportFilters').submit();
            }
        });
        
        // Validate date range
        if (startDateInput && endDateInput) {
            [startDateInput, endDateInput].forEach(input => {
                input.addEventListener('change', validateDateRange);
            });
        }
    }
    
    /**
     * Validates that the start date is before the end date
     */
    function validateDateRange() {
        const startDate = new Date(document.getElementById('startDate').value);
        const endDate = new Date(document.getElementById('endDate').value);
        const submitButton = document.querySelector('#reportFilters button[type="submit"]');
        
        if (startDate > endDate) {
            alert('Start date cannot be after end date');
            submitButton.disabled = true;
        } else {
            submitButton.disabled = false;
        }
    }
    
    /**
     * Initializes the registration trends chart
     */
    function initializeRegistrationTrendsChart() {
        const ctx = document.getElementById('registrationTrends').getContext('2d');
        const chartLabels = window.trendDates || [];
        const chartData = window.registrationTrends || [];
        
        // Create gradient background
        const gradientFill = ctx.createLinearGradient(0, 0, 0, 400);
        gradientFill.addColorStop(0, colorPalette.successLight);
        gradientFill.addColorStop(1, 'rgba(255, 255, 255, 0)');
        
        charts.trendChart = new Chart(ctx, {
            type: 'line',
            data: {
                labels: chartLabels,
                datasets: [{
                    label: 'Registrations',
                    data: chartData,
                    backgroundColor: gradientFill,
                    borderColor: colorPalette.success,
                    borderWidth: 2,
                    pointBackgroundColor: colorPalette.success,
                    pointBorderColor: '#fff',
                    pointBorderWidth: 2,
                    pointRadius: 4,
                    pointHoverRadius: 6,
                    tension: 0.3,
                    fill: true
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                scales: {
                    y: {
                        beginAtZero: true,
                        grid: {
                            color: 'rgba(0, 0, 0, 0.05)'
                        },
                        ticks: {
                            precision: 0
                        }
                    },
                    x: {
                        grid: {
                            display: false
                        }
                    }
                },
                plugins: {
                    legend: {
                        display: false
                    },
                    tooltip: {
                        mode: 'index',
                        intersect: false,
                        backgroundColor: 'rgba(0, 0, 0, 0.7)',
                        titleFont: {
                            weight: 'bold'
                        },
                        callbacks: {
                            label: function(context) {
                                return `Registrations: ${context.raw}`;
                            }
                        }
                    }
                },
                interaction: {
                    mode: 'nearest',
                    axis: 'x',
                    intersect: false
                },
                animation: {
                    duration: 1000,
                    easing: 'easeOutQuart'
                }
            }
        });
    }
    
    /**
     * Initializes the attendance doughnut chart
     */
    function initializeAttendanceChart() {
        const ctx = document.getElementById('attendanceChart').getContext('2d');
        const attended = window.totalAttended || 0;
        const notAttended = (window.totalRegistrations || 0) - attended;
        
        charts.attendanceChart = new Chart(ctx, {
            type: 'doughnut',
            data: {
                labels: ['Attended', 'Not Attended'],
                datasets: [{
                    data: [attended, notAttended],
                    backgroundColor: [colorPalette.success, colorPalette.danger],
                    borderColor: ['#fff', '#fff'],
                    borderWidth: 2,
                    hoverOffset: 8
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                cutout: '70%',
                plugins: {
                    legend: {
                        position: 'bottom',
                        labels: {
                            padding: 20,
                            usePointStyle: true,
                            pointStyle: 'circle'
                        }
                    },
                    tooltip: {
                        callbacks: {
                            label: function(context) {
                                const label = context.label || '';
                                const value = context.raw || 0;
                                const total = context.dataset.data.reduce((a, b) => a + b, 0);
                                const percentage = Math.round((value / total) * 100);
                                return `${label}: ${value} (${percentage}%)`;
                            }
                        }
                    }
                },
                animation: {
                    animateRotate: true,
                    animateScale: true,
                    duration: 1000,
                    easing: 'easeOutQuart'
                }
            }
        });
    }
    
    /**
     * Initializes the data table functionality
     */
    function initializeDataTable() {
        const table = document.getElementById('eventsTable');
        
        // Enable search functionality
        const searchInput = document.createElement('input');
        searchInput.type = 'text';
        searchInput.placeholder = 'Search events...';
        searchInput.classList.add('form-control', 'mb-3');
        table.parentNode.insertBefore(searchInput, table);
        
        searchInput.addEventListener('keyup', function() {
            const searchText = this.value.toLowerCase();
            const rows = table.querySelectorAll('tbody tr');
            
            rows.forEach(row => {
                const text = row.textContent.toLowerCase();
                row.style.display = text.includes(searchText) ? '' : 'none';
            });
        });
        
        // Enable sorting
        const headers = table.querySelectorAll('thead th');
        headers.forEach((header, index) => {
            if (index > 0) { // Skip the # column
                header.classList.add('sortable');
                header.style.cursor = 'pointer';
                header.addEventListener('click', function() {
                    sortTable(table, index);
                });
            }
        });
    }
    
    /**
     * Sorts a table by the specified column index
     */
    function sortTable(table, columnIndex) {
        const headers = table.querySelectorAll('thead th');
        const header = headers[columnIndex];
        const direction = header.getAttribute('data-sort') === 'asc' ? 'desc' : 'asc';
        
        // Update sort direction indicators
        headers.forEach(h => h.removeAttribute('data-sort'));
        header.setAttribute('data-sort', direction);
        
        // Sort the table
        const rows = Array.from(table.querySelectorAll('tbody tr'));
        rows.sort((a, b) => {
            const aValue = a.cells[columnIndex].textContent.trim();
            const bValue = b.cells[columnIndex].textContent.trim();
            
            // Check if the values contain numbers
            const aNum = parseFloat(aValue.replace(/[^0-9.-]+/g, ''));
            const bNum = parseFloat(bValue.replace(/[^0-9.-]+/g, ''));
            
            if (!isNaN(aNum) && !isNaN(bNum)) {
                return direction === 'asc' ? aNum - bNum : bNum - aNum;
            }
            
            // String comparison
            return direction === 'asc' 
                ? aValue.localeCompare(bValue) 
                : bValue.localeCompare(aValue);
        });
        
        // Update the table
        const tbody = table.querySelector('tbody');
        rows.forEach(row => tbody.appendChild(row));
    }
    
    /**
     * Initializes the column toggle functionality
     */
    function initializeColumnToggles() {
        const toggleButton = document.getElementById('toggleTableColumns');
        const optionalColumns = document.querySelectorAll('.optional-column');
        
        if (!toggleButton) return;
        
        toggleButton.addEventListener('click', function() {
            optionalColumns.forEach(column => {
                column.classList.toggle('d-none');
            });
            
            // Update button text
            const isHidden = optionalColumns[0].classList.contains('d-none');
            this.innerHTML = isHidden
                ? '<i class="fas fa-columns me-1"></i> Show All Columns'
                : '<i class="fas fa-columns me-1"></i> Hide Optional Columns';
        });
    }
    
    /**
     * Adds animations to the stat cards
     */
    function animateStatCards() {
        const statValues = document.querySelectorAll('.display-6');
        
        statValues.forEach(element => {
            const finalValue = parseInt(element.textContent);
            let startValue = 0;
            const duration = 1000; // ms
            const startTime = performance.now();
            
            function updateValue(timestamp) {
                const elapsed = timestamp - startTime;
                const progress = Math.min(elapsed / duration, 1);
                const easedProgress = 1 - Math.pow(1 - progress, 3); // Cubic ease-out
                
                const currentValue = Math.floor(startValue + (finalValue - startValue) * easedProgress);
                element.textContent = currentValue;
                
                if (progress < 1) {
                    requestAnimationFrame(updateValue);
                } else {
                    element.textContent = finalValue;
                }
            }
            
            requestAnimationFrame(updateValue);
        });
    }
    
    // Add print functionality
    document.getElementById('printReport')?.addEventListener('click', function() {
        window.print();
    });
    
    // Add API refresh functionality for real-time updates
    document.getElementById('refreshData')?.addEventListener('click', function() {
        this.disabled = true;
        this.innerHTML = '<span class="spinner-border spinner-border-sm" role="status" aria-hidden="true"></span> Refreshing...';
        
        const dateRange = document.getElementById('dateRange').value;
        let params = new URLSearchParams();
        params.append('date_range', dateRange);
        
        if (dateRange === 'custom') {
            params.append('start_date', document.getElementById('startDate').value);
            params.append('end_date', document.getElementById('endDate').value);
        }
        
        fetch(`/admin/api/event-stats?${params.toString()}`)
            .then(response => response.json())
            .then(data => {
                if (charts.trendChart) {
                    charts.trendChart.data.labels = data.dates;
                    charts.trendChart.data.datasets[0].data = data.counts;
                    charts.trendChart.update();
                }
                this.disabled = false;
                this.innerHTML = '<i class="fas fa-sync-alt me-1"></i> Refresh Data';
            })
            .catch(error => {
                console.error('Error refreshing data:', error);
                this.disabled = false;
                this.innerHTML = '<i class="fas fa-sync-alt me-1"></i> Refresh Data';
                alert('Error refreshing data. Please try again.');
            });
    });
});