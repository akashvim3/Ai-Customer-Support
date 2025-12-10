/**
 * Analytics Dashboard JavaScript
 * Handles data visualization and interactive charts
 */

(function($) {
    'use strict';

    // Analytics Dashboard Object
    const AnalyticsDashboard = {
        // Configuration
        config: {
            refreshInterval: 60000, // 1 minute
            apiEndpoint: '/api/analytics/',
            chartColors: {
                primary: '#87CEEB',
                success: '#27AE60',
                warning: '#F39C12',
                danger: '#E74C3C',
                info: '#3498DB',
                secondary: '#2C3E50'
            }
        },

        // Chart instances
        charts: {
            ticketTrend: null,
            sentimentPie: null,
            categoryBar: null,
            performanceRadar: null,
            timelineArea: null
        },

        // Initialize
        init: function() {
            console.log('Analytics Dashboard Initializing...');
            this.bindEvents();
            this.loadAnalyticsData();
            this.startAutoRefresh();
        },

        // Bind events
        bindEvents: function() {
            const self = this;

            // Date range selector
            $('#dateRange').on('change', function() {
                self.loadAnalyticsData();
            });

            // Period selector
            $('input[name="period"]').on('change', function() {
                self.loadAnalyticsData();
            });

            // Export buttons
            $('#exportPDF').on('click', function() {
                self.exportToPDF();
            });

            $('#exportCSV').on('click', function() {
                self.exportToCSV();
            });

            // Refresh button
            $('#refreshData').on('click', function() {
                self.loadAnalyticsData();
            });

            // Category filter
            $('#categoryFilter').on('change', function() {
                self.updateCharts();
            });
        },

        // Load analytics data
        loadAnalyticsData: function() {
            const self = this;
            const dateRange = $('#dateRange').val() || '30';

            $.ajax({
                url: self.config.apiEndpoint + 'overview/',
                method: 'GET',
                data: {
                    days: dateRange
                },
                success: function(data) {
                    self.updateMetrics(data);
                    self.loadChartData();
                },
                error: function(xhr, status, error) {
                    console.error('Error loading analytics:', error);
                    showNotification('Error loading analytics data', 'danger');
                }
            });
        },

        // Update metrics
        updateMetrics: function(data) {
            // Update stat cards with animation
            this.animateValue('#totalTickets', 0, data.tickets.total, 1000);
            this.animateValue('#resolvedTickets', 0, data.tickets.resolved, 1000);
            this.animateValue('#avgResponseTime', 0, Math.round(data.tickets.avg_resolution_hours * 60), 1000, 'm');
            this.animateValue('#csatScore', 0, data.chatbot.avg_sentiment, 1000, '', 1);

            // Update percentages
            const resolutionRate = data.tickets.resolution_rate || 0;
            $('#resolutionRate').text(resolutionRate.toFixed(1) + '%');

            // Update progress bars
            this.updateProgressBar('#resolutionProgress', resolutionRate);

            // Update trend indicators
            this.updateTrendIndicator('#ticketTrend', data.trend || 'up', data.change || 12);
        },

        // Animate number values
        animateValue: function(selector, start, end, duration, suffix = '', decimals = 0) {
            const element = $(selector);
            const range = end - start;
            const increment = range / (duration / 16);
            let current = start;

            const timer = setInterval(function() {
                current += increment;
                if ((increment > 0 && current >= end) || (increment < 0 && current <= end)) {
                    current = end;
                    clearInterval(timer);
                }
                element.text(current.toFixed(decimals) + suffix);
            }, 16);
        },

        // Update progress bar
        updateProgressBar: function(selector, value) {
            $(selector).css('width', value + '%').attr('aria-value-now', value);
        },

        // Update trend indicator
        updateTrendIndicator: function(selector, direction, percentage) {
            const icon = direction === 'up' ? 'fa-arrow-up' : 'fa-arrow-down';
            const colorClass = direction === 'up' ? 'text-success' : 'text-danger';

            $(selector).html(
                `<i class="fas ${icon} ${colorClass}"></i> ${percentage}%`
            );
        },

        // Load chart data
        loadChartData: function() {
            const self = this;

            // Load trend data
            $.ajax({
                url: self.config.apiEndpoint + 'trends/',
                method: 'GET',
                success: function(data) {
                    self.renderTicketTrendChart(data);
                    self.renderSentimentChart(data);
                }
            });

            // Load category performance
            $.ajax({
                url: self.config.apiEndpoint + 'category-performance/',
                method: 'GET',
                success: function(data) {
                    self.renderCategoryChart(data);
                }
            });

            // Load agent performance
            $.ajax({
                url: self.config.apiEndpoint + 'agent-performance/',
                method: 'GET',
                success: function(data) {
                    self.renderPerformanceChart(data);
                }
            });
        },

        // Render ticket trend chart
        renderTicketTrendChart: function(data) {
            const ctx = document.getElementById('ticketTrendChart');
            if (!ctx) return;

            // Destroy existing chart
            if (this.charts.ticketTrend) {
                this.charts.ticketTrend.destroy();
            }

            this.charts.ticketTrend = new Chart(ctx.getContext('2d'), {
                type: 'line',
                data: {
                    labels: data.tickets.dates.map(date => this.formatDate(date)),
                    datasets: [{
                        label: 'Total Tickets',
                        data: data.tickets.counts,
                        borderColor: this.config.chartColors.primary,
                        backgroundColor: this.hexToRgba(this.config.chartColors.primary, 0.1),
                        tension: 0.4,
                        fill: true,
                        pointRadius: 4,
                        pointHoverRadius: 6,
                        pointBackgroundColor: this.config.chartColors.primary
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
                            },
                            callbacks: {
                                label: function(context) {
                                    return 'Tickets: ' + context.parsed.y;
                                }
                            }
                        }
                    },
                    scales: {
                        y: {
                            beginAtZero: true,
                            ticks: {
                                precision: 0
                            },
                            grid: {
                                drawBorder: false
                            }
                        },
                        x: {
                            grid: {
                                display: false
                            }
                        }
                    },
                    interaction: {
                        intersect: false,
                        mode: 'index'
                    }
                }
            });
        },

        // Render sentiment chart
        renderSentimentChart: function(data) {
            const ctx = document.getElementById('sentimentChart');
            if (!ctx) return;

            if (this.charts.sentimentPie) {
                this.charts.sentimentPie.destroy();
            }

            const sentimentData = data.sentiment_distribution || {};

            this.charts.sentimentPie = new Chart(ctx.getContext('2d'), {
                type: 'doughnut',
                data: {
                    labels: ['Positive', 'Neutral', 'Negative'],
                    datasets: [{
                        data: [
                            sentimentData.positive || 0,
                            sentimentData.neutral || 0,
                            sentimentData.negative || 0
                        ],
                        backgroundColor: [
                            this.config.chartColors.success,
                            this.config.chartColors.warning,
                            this.config.chartColors.danger
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
                        },
                        tooltip: {
                            callbacks: {
                                label: function(context) {
                                    const label = context.label || '';
                                    const value = context.parsed;
                                    const total = context.dataset.data.reduce((a, b) => a + b, 0);
                                    const percentage = ((value / total) * 100).toFixed(1);
                                    return label + ': ' + value + ' (' + percentage + '%)';
                                }
                            }
                        }
                    }
                }
            });
        },

        // Render category performance chart
        renderCategoryChart: function(data) {
            const ctx = document.getElementById('categoryChart');
            if (!ctx) return;

            if (this.charts.categoryBar) {
                this.charts.categoryBar.destroy();
            }

            const categories = data.map(item => item.category);
            const counts = data.map(item => item.total_tickets);

            this.charts.categoryBar = new Chart(ctx.getContext('2d'), {
                type: 'bar',
                data: {
                    labels: categories,
                    datasets: [{
                        label: 'Tickets',
                        data: counts,
                        backgroundColor: this.config.chartColors.primary,
                        borderRadius: 8,
                        barThickness: 40
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
                            callbacks: {
                                label: function(context) {
                                    return 'Tickets: ' + context.parsed.y;
                                }
                            }
                        }
                    },
                    scales: {
                        y: {
                            beginAtZero: true,
                            ticks: {
                                precision: 0
                            }
                        }
                    }
                }
            });
        },

        // Render performance radar chart
        renderPerformanceChart: function(data) {
            const ctx = document.getElementById('performanceChart');
            if (!ctx) return;

            if (this.charts.performanceRadar) {
                this.charts.performanceRadar.destroy();
            }

            const topAgents = data.slice(0, 5);
            const agentNames = topAgents.map(agent =>
                agent.assigned_agent__first_name + ' ' + agent.assigned_agent__last_name
            );
            const tickets = topAgents.map(agent => agent.tickets_resolved);

            this.charts.performanceRadar = new Chart(ctx.getContext('2d'), {
                type: 'radar',
                data: {
                    labels: agentNames,
                    datasets: [{
                        label: 'Tickets Resolved',
                        data: tickets,
                        backgroundColor: this.hexToRgba(this.config.chartColors.primary, 0.2),
                        borderColor: this.config.chartColors.primary,
                        pointBackgroundColor: this.config.chartColors.primary,
                        pointBorderColor: '#fff',
                        pointHoverBackgroundColor: '#fff',
                        pointHoverBorderColor: this.config.chartColors.primary
                    }]
                },
                options: {
                    responsive: true,
                    maintainAspectRatio: false,
                    plugins: {
                        legend: {
                            display: false
                        }
                    },
                    scales: {
                        r: {
                            beginAtZero: true,
                            ticks: {
                                precision: 0
                            }
                        }
                    }
                }
            });
        },

        // Export to PDF
        exportToPDF: function() {
            showNotification('Generating PDF report...', 'info');

            $.ajax({
                url: this.config.apiEndpoint + 'export-pdf/',
                method: 'POST',
                data: {
                    date_range: $('#dateRange').val()
                },
                success: function(response) {
                    if (response.file_url) {
                        window.open(response.file_url, '_blank');
                        showNotification('PDF report generated successfully', 'success');
                    }
                },
                error: function() {
                    showNotification('Error generating PDF report', 'danger');
                }
            });
        },

        // Export to CSV
        exportToCSV: function() {
            const dateRange = $('#dateRange').val();
            window.location.href = this.config.apiEndpoint + 'export-csv/?days=' + dateRange;
            showNotification('CSV export started', 'success');
        },

        // Update charts
        updateCharts: function() {
            this.loadChartData();
        },

        // Start auto-refresh
        startAutoRefresh: function() {
            const self = this;
            setInterval(function() {
                self.loadAnalyticsData();
            }, self.config.refreshInterval);
        },

        // Helper: Format date
        formatDate: function(dateString) {
            const date = new Date(dateString);
            return date.toLocaleDateString('en-US', { month: 'short', day: 'numeric' });
        },

        // Helper: Hex to RGBA
        hexToRgba: function(hex, alpha) {
            const r = parseInt(hex.slice(1, 3), 16);
            const g = parseInt(hex.slice(3, 5), 16);
            const b = parseInt(hex.slice(5, 7), 16);
            return `rgba(${r}, ${g}, ${b}, ${alpha})`;
        }
    };

    // Initialize on document ready
    $(document).ready(function() {
        if ($('#analyticsContainer').length) {
            AnalyticsDashboard.init();
        }
    });

})(jQuery);
