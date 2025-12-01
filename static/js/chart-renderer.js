/**
 * MCIDIA Chart Renderer
 * Renders AI-generated charts using Chart.js and Plotly
 */

// Prevent double declaration
if (typeof MCIDIAChartRenderer === 'undefined') {
class MCIDIAChartRenderer {
    constructor() {
        this.chartInstances = new Map();
        this.defaultColors = [
            '#0A2756', '#2767B1', '#2C8C56', '#E8B93B', 
            '#E74C3C', '#8B5CF6', '#3498db', '#1abc9c'
        ];
    }

    /**
     * Renders a chart in the specified container
     * @param {string} containerId - The ID of the container element
     * @param {Object} chartConfig - The chart configuration
     * @param {string} library - 'chartjs' or 'plotly' (default: 'chartjs')
     */
    render(containerId, chartConfig, library = 'chartjs') {
        const container = document.getElementById(containerId);
        if (!container) {
            console.error(`Container ${containerId} not found`);
            return;
        }

        // Destroy existing chart if any
        this.destroy(containerId);

        if (library === 'plotly') {
            this.renderPlotly(container, chartConfig);
        } else {
            this.renderChartJS(container, chartConfig);
        }
    }

    /**
     * Renders a chart using Chart.js
     */
    renderChartJS(container, config) {
        // Create canvas element
        const canvas = document.createElement('canvas');
        canvas.id = `${container.id}-canvas`;
        container.innerHTML = '';
        container.appendChild(canvas);

        const ctx = canvas.getContext('2d');
        
        // Handle special chart types
        let chartType = config.type;
        let chartData = this.prepareChartJSData(config);
        let chartOptions = this.prepareChartJSOptions(config);

        // Special handling for gauge type
        if (chartType === 'gauge') {
            this.renderGaugeChart(container, config);
            return;
        }

        // Map area to line with fill
        if (chartType === 'area') {
            chartType = 'line';
            chartData.datasets.forEach(ds => ds.fill = true);
        }

        // Map polarArea type
        if (chartType === 'polar' || chartType === 'polarArea') {
            chartType = 'polarArea';
        }

        const chart = new Chart(ctx, {
            type: chartType,
            data: chartData,
            options: chartOptions
        });

        this.chartInstances.set(container.id, chart);
    }

    /**
     * Prepares data for Chart.js
     */
    prepareChartJSData(config) {
        const datasets = (config.datasets || []).map((ds, idx) => {
            const dataset = { ...ds };
            
            // Add default colors if not specified
            if (!dataset.backgroundColor) {
                if (['pie', 'doughnut', 'polarArea'].includes(config.type)) {
                    dataset.backgroundColor = this.defaultColors.slice(0, (ds.data || []).length);
                } else {
                    dataset.backgroundColor = this.defaultColors[idx % this.defaultColors.length];
                }
            }
            
            if (!dataset.borderColor && !['pie', 'doughnut', 'polarArea'].includes(config.type)) {
                dataset.borderColor = dataset.backgroundColor;
            }

            return dataset;
        });

        return {
            labels: config.labels || [],
            datasets: datasets
        };
    }

    /**
     * Prepares options for Chart.js
     */
    prepareChartJSOptions(config) {
        const options = {
            responsive: true,
            maintainAspectRatio: true,
            plugins: {
                title: {
                    display: !!config.title,
                    text: config.title || '',
                    font: {
                        size: 16,
                        weight: 'bold',
                        family: "'Cairo', 'Inter', sans-serif"
                    },
                    color: '#0A2756'
                },
                subtitle: {
                    display: !!(config.options && config.options.subtitle),
                    text: config.options?.subtitle || '',
                    font: {
                        size: 12,
                        family: "'Cairo', 'Inter', sans-serif"
                    },
                    color: '#666'
                },
                legend: {
                    position: 'bottom',
                    labels: {
                        font: {
                            family: "'Cairo', 'Inter', sans-serif"
                        }
                    }
                },
                tooltip: {
                    backgroundColor: 'rgba(10, 39, 86, 0.9)',
                    titleFont: {
                        family: "'Cairo', 'Inter', sans-serif"
                    },
                    bodyFont: {
                        family: "'Cairo', 'Inter', sans-serif"
                    }
                }
            },
            animation: {
                duration: 1000,
                easing: 'easeOutQuart'
            },
            ...(config.options || {})
        };

        // Add scales for bar/line charts
        if (['bar', 'line', 'area'].includes(config.type)) {
            options.scales = {
                y: {
                    beginAtZero: true,
                    ticks: {
                        font: {
                            family: "'Cairo', 'Inter', sans-serif"
                        }
                    }
                },
                x: {
                    ticks: {
                        font: {
                            family: "'Cairo', 'Inter', sans-serif"
                        }
                    }
                },
                ...(config.options?.scales || {})
            };
        }

        return options;
    }

    /**
     * Renders a gauge chart
     */
    renderGaugeChart(container, config) {
        const value = config.value || 0;
        const target = config.target || 100;
        const color = config.color || '#2767B1';
        const title = config.title || '';
        const subtitle = config.options?.subtitle || '';

        container.innerHTML = `
            <div class="gauge-chart" style="text-align: center; padding: 20px;">
                <h5 style="color: #0A2756; margin-bottom: 15px; font-family: 'Cairo', 'Inter', sans-serif;">${title}</h5>
                <div class="gauge-container" style="position: relative; width: 200px; height: 100px; margin: 0 auto;">
                    <svg viewBox="0 0 200 100" style="width: 100%; height: 100%;">
                        <!-- Background arc -->
                        <path d="M 20 100 A 80 80 0 0 1 180 100" 
                              fill="none" 
                              stroke="#e0e0e0" 
                              stroke-width="20"
                              stroke-linecap="round"/>
                        <!-- Value arc -->
                        <path d="M 20 100 A 80 80 0 0 1 ${this.getGaugeArcX(value)} ${this.getGaugeArcY(value)}" 
                              fill="none" 
                              stroke="${color}" 
                              stroke-width="20"
                              stroke-linecap="round"
                              class="gauge-value"/>
                    </svg>
                    <div style="position: absolute; bottom: 0; left: 50%; transform: translateX(-50%); font-size: 24px; font-weight: bold; color: ${color}; font-family: 'Cairo', 'Inter', sans-serif;">
                        ${value}%
                    </div>
                </div>
                ${subtitle ? `<p style="color: #666; font-size: 12px; margin-top: 10px; font-family: 'Cairo', 'Inter', sans-serif;">${subtitle}</p>` : ''}
            </div>
        `;
    }

    /**
     * Calculate X coordinate for gauge arc endpoint
     */
    getGaugeArcX(percentage) {
        const angle = (percentage / 100) * Math.PI;
        return 100 + 80 * Math.cos(Math.PI - angle);
    }

    /**
     * Calculate Y coordinate for gauge arc endpoint
     */
    getGaugeArcY(percentage) {
        const angle = (percentage / 100) * Math.PI;
        return 100 - 80 * Math.sin(angle);
    }

    /**
     * Renders a chart using Plotly
     */
    renderPlotly(container, config) {
        container.innerHTML = '';
        
        const plotlyData = this.prepareplotlyData(config);
        const plotlyLayout = this.preparePlotlyLayout(config);
        const plotlyConfig = {
            responsive: true,
            displayModeBar: true,
            modeBarButtonsToRemove: ['lasso2d', 'select2d']
        };

        Plotly.newPlot(container.id, plotlyData, plotlyLayout, plotlyConfig);
    }

    /**
     * Prepares data for Plotly
     */
    prepareplotlyData(config) {
        const traces = [];
        const chartType = config.type;

        // Map chart types to Plotly types
        const plotlyTypeMap = {
            'bar': 'bar',
            'line': 'scatter',
            'area': 'scatter',
            'pie': 'pie',
            'doughnut': 'pie',
            'scatter': 'scatter',
            'radar': 'scatterpolar',
            'funnel': 'funnel',
            'heatmap': 'heatmap',
            'treemap': 'treemap',
            'sankey': 'sankey',
            'waterfall': 'waterfall'
        };

        const plotlyType = plotlyTypeMap[chartType] || 'bar';

        (config.datasets || []).forEach((ds, idx) => {
            const trace = {
                name: ds.label || `Series ${idx + 1}`
            };

            if (plotlyType === 'pie') {
                trace.type = 'pie';
                trace.labels = config.labels;
                trace.values = ds.data;
                trace.hole = chartType === 'doughnut' ? 0.4 : 0;
                trace.marker = {
                    colors: ds.backgroundColor || this.defaultColors
                };
            } else if (plotlyType === 'scatter') {
                trace.type = 'scatter';
                trace.mode = chartType === 'scatter' ? 'markers' : 'lines+markers';
                trace.x = config.labels;
                trace.y = ds.data;
                trace.fill = chartType === 'area' ? 'tozeroy' : 'none';
                trace.marker = {
                    color: ds.backgroundColor || this.defaultColors[idx]
                };
                trace.line = {
                    color: ds.borderColor || ds.backgroundColor || this.defaultColors[idx],
                    shape: 'spline'
                };
            } else if (plotlyType === 'scatterpolar') {
                trace.type = 'scatterpolar';
                trace.r = ds.data;
                trace.theta = config.labels;
                trace.fill = 'toself';
                trace.fillcolor = ds.backgroundColor || 'rgba(39, 103, 177, 0.2)';
                trace.line = {
                    color: ds.borderColor || '#2767B1'
                };
            } else if (plotlyType === 'funnel') {
                trace.type = 'funnel';
                trace.y = config.labels;
                trace.x = ds.data;
                trace.marker = {
                    color: ds.backgroundColor || this.defaultColors
                };
            } else {
                trace.type = 'bar';
                trace.x = config.labels;
                trace.y = ds.data;
                trace.marker = {
                    color: ds.backgroundColor || this.defaultColors[idx]
                };
                
                // Horizontal bar chart
                if (config.options?.indexAxis === 'y') {
                    trace.orientation = 'h';
                    [trace.x, trace.y] = [trace.y, trace.x];
                }
            }

            traces.push(trace);
        });

        return traces;
    }

    /**
     * Prepares layout for Plotly
     */
    preparePlotlyLayout(config) {
        return {
            title: {
                text: config.title || '',
                font: {
                    family: "'Cairo', 'Inter', sans-serif",
                    size: 16,
                    color: '#0A2756'
                }
            },
            font: {
                family: "'Cairo', 'Inter', sans-serif"
            },
            showlegend: true,
            legend: {
                orientation: 'h',
                y: -0.15
            },
            margin: {
                t: 60,
                r: 30,
                b: 60,
                l: 60
            },
            paper_bgcolor: 'rgba(0,0,0,0)',
            plot_bgcolor: 'rgba(0,0,0,0)',
            ...(config.options?.layout || {})
        };
    }

    /**
     * Destroys a chart instance
     */
    destroy(containerId) {
        if (this.chartInstances.has(containerId)) {
            const chart = this.chartInstances.get(containerId);
            if (chart && typeof chart.destroy === 'function') {
                chart.destroy();
            }
            this.chartInstances.delete(containerId);
        }
        
        // Also try to purge Plotly
        try {
            if (typeof Plotly !== 'undefined') {
                Plotly.purge(containerId);
            }
        } catch (e) {
            // Ignore
        }
    }

    /**
     * Renders multiple charts from AI response
     * @param {string} containerClass - Class name for chart containers
     * @param {Array} charts - Array of chart configurations
     */
    renderMultiple(containerClass, charts) {
        const containers = document.querySelectorAll(`.${containerClass}`);
        
        charts.forEach((chart, idx) => {
            if (containers[idx]) {
                this.render(containers[idx].id, chart);
            }
        });
    }

    /**
     * Creates a chart container element
     * @param {string} id - Container ID
     * @param {Object} config - Chart configuration
     * @returns {HTMLElement} - The chart container element
     */
    createChartElement(id, config) {
        const wrapper = document.createElement('div');
        wrapper.className = 'mcidia-chart-wrapper';
        wrapper.style.cssText = `
            background: white;
            border-radius: 12px;
            padding: 20px;
            margin: 15px 0;
            box-shadow: 0 2px 12px rgba(10, 39, 86, 0.08);
            border: 1px solid #e8ecf0;
        `;

        const container = document.createElement('div');
        container.id = id;
        container.className = 'mcidia-chart-container';
        container.style.cssText = `
            width: 100%;
            height: 300px;
            position: relative;
        `;

        wrapper.appendChild(container);
        return wrapper;
    }

    /**
     * Parses AI response and renders any embedded charts
     * @param {HTMLElement} messageElement - The message element containing the response
     * @param {Array} charts - Array of chart configurations extracted from response
     */
    renderChartsInMessage(messageElement, charts) {
        if (!charts || charts.length === 0) return;

        const chartsContainer = document.createElement('div');
        chartsContainer.className = 'message-charts';
        chartsContainer.style.marginTop = '15px';

        charts.forEach((chart, idx) => {
            const chartId = `msg-chart-${Date.now()}-${idx}`;
            const chartElement = this.createChartElement(chartId, chart);
            chartsContainer.appendChild(chartElement);
            
            // Render after DOM update
            setTimeout(() => {
                this.render(chartId, chart);
            }, 100);
        });

        messageElement.appendChild(chartsContainer);
    }
}
}

// Global instance - only create if not already created
if (typeof window.mcidiaChartRenderer === 'undefined') {
    window.mcidiaChartRenderer = new MCIDIAChartRenderer();
}

// Helper function to render charts
function renderMCIDIAChart(containerId, config, library = 'chartjs') {
    window.mcidiaChartRenderer.render(containerId, config, library);
}

// Helper function to render charts in AI message
function renderChartsInAIResponse(messageElement, charts) {
    window.mcidiaChartRenderer.renderChartsInMessage(messageElement, charts);
}
