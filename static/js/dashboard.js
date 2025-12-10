// Dashboard specific JavaScript
$(document).ready(function() {
    // Initialize charts if on dashboard page
    if ($('#ticketChart').length) {
        initializeDashboard();
    }
});

function initializeDashboard() {
    loadMetrics();
    loadCharts();

    // Auto-refresh every 60 seconds
    setInterval(loadMetrics, 60000);
}

function loadMetrics() {
    $.ajax({
        url: '/api/analytics/overview/',
        method: 'GET',
        success: function(data) {
            updateMetrics(data);
        },
        error: function(xhr) {
            console.error('Error loading metrics:', xhr);
        }
    });
}

function updateMetrics(data) {
    // Update stat cards
    $('#totalTickets').text(formatNumber(data.tickets.total));
    $('#resolvedTickets').text(formatNumber(data.tickets.resolved));
    $('#avgResponseTime').text(Math.round(data.tickets.avg_resolution_hours * 60) + 'm');
    $('#customerSatisfaction').text(data.chatbot.avg_sentiment.toFixed(1));

    // Update percentages
    const resolutionRate = data.tickets.resolution_rate;
    $('.resolution-rate').text(resolutionRate.toFixed(1) + '%');

    // Update progress bars
    $('.progress-bar').each(function() {
        const value = $(this).data('value');
        $(this).css('width', value + '%');
    });
}

function loadCharts() {
    // Load ticket trend chart
    $.ajax({
        url: '/api/analytics/trends/',
        method: 'GET',
        success: function(data) {
            renderTicketChart(data);
            renderSentimentChart(data);
        }
    });
}

function renderTicketChart(data) {
    const ctx = document.getElementById('ticketChart');
    if (!ctx) return;

    new Chart(ctx.getContext('2d'), {
        type: 'line',
        data: {
            labels: data.tickets.dates.map(date => formatDate(date)),
            datasets: [{
                label: 'Tickets Created',
                data: data.tickets.counts,
                borderColor: '#87CEEB',
                backgroundColor: 'rgba(135, 206, 235, 0.1)',
                tension: 0.4,
                fill: true,
                pointRadius: 4,
                pointHoverRadius: 6
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: {
                    display: false
                },
                tooltip: {
                    backgroundColor: 'rgba(0, 0, 0, 0.8)',
                    padding: 12,
                    titleFont: {
                        size: 14
                    },
                    bodyFont: {
                        size: 13
                    }
                }
            },
            scales: {
                y: {
                    beginAtZero: true,
                    ticks: {
                        precision: 0
                    }
                },
                x: {
                    grid: {
                        display: false
                    }
                }
            }
        }
    });
}

function renderSentimentChart(data) {
    const ctx = document.getElementById('sentimentChart');
    if (!ctx) return;

    new Chart(ctx.getContext('2d'), {
        type: 'doughnut',
        data: {
            labels: ['Positive', 'Neutral', 'Negative'],
            datasets: [{
                data: [
                    data.sentiment_distribution?.positive || 0,
                    data.sentiment_distribution?.neutral || 0,
                    data.sentiment_distribution?.negative || 0
                ],
                backgroundColor: [
                    '#27AE60',
                    '#F39C12',
                    '#E74C3C'
                ],
                borderWidth: 0
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: {
                    position: 'bottom',
                    labels: {
                        padding: 20,
                        font: {
                            size: 12
                        }
                    }
                }
            }
        }
    });
}

// Real-time updates
function subscribeToUpdates() {
    // WebSocket connection for real-time updates
    const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
    const ws = new WebSocket(`${protocol}//${window.location.host}/ws/dashboard/`);

    ws.message = function(event) {
        const data = JSON.parse(event.data);
        handleRealtimeUpdate(data);
    };

    ws.onerror = function(error) {
        console.error('WebSocket error:', error);
    };
}

function handleRealtimeUpdate(data) {
    if (data.type === 'new_ticket') {
        showNotification('New ticket created: ' + data.ticket_id, 'info');
        loadMetrics();
    } else if (data.type === 'ticket_resolved') {
        showNotification('Ticket resolved: ' + data.ticket_id, 'success');
        loadMetrics();
    }
}
