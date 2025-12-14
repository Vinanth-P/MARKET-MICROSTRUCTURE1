// Main JavaScript file for Market Microstructure Platform

document.addEventListener('DOMContentLoaded', function() {
    // Initialize real-time updates
    initRealTimeUpdates();
    
    // Initialize form handlers
    initFormHandlers();
    
    // Initialize chart updates
    initChartUpdates();
    
    // Apply usage bar widths set from server-rendered data attributes
    applyUsageWidths();
});

// Real-time data updates
function initRealTimeUpdates() {
    // Update market overview every 5 seconds
    if (document.querySelector('.market-cards')) {
        setInterval(updateMarketOverview, 5000);
    }
    
    // Update signals every 10 seconds
    if (document.querySelector('.signal-list')) {
        setInterval(updateSignals, 10000);
    }
    
    // Update sentiment every 30 seconds
    if (document.querySelector('.sentiment-gauge')) {
        setInterval(updateSentiment, 30000);
    }
}

// Update market overview data
async function updateMarketOverview() {
    try {
        const response = await fetch('/api/dashboard/market-overview/');
        const data = await response.json();
        
        // Update indicator cards
        if (data.sp500) {
            updateIndicatorCard('sp500', data.sp500);
        }
        if (data.btc) {
            updateIndicatorCard('btc', data.btc);
        }
        if (data.eth) {
            updateIndicatorCard('eth', data.eth);
        }
    } catch (error) {
        console.error('Error updating market overview:', error);
    }
}

// Update individual indicator card
function updateIndicatorCard(type, data) {
    const card = document.querySelector(`[data-indicator="${type}"]`);
    if (!card) return;
    
    const valueEl = card.querySelector('.card-value');
    const changeEl = card.querySelector('.card-change');
    
    if (valueEl) {
        valueEl.textContent = formatPrice(data.value, type);
    }
    
    if (changeEl) {
        const sign = data.change_percent >= 0 ? '+' : '';
        changeEl.textContent = `${sign}${data.change_percent.toFixed(1)}%`;
        changeEl.className = `card-change ${data.change_percent >= 0 ? 'positive' : 'negative'}`;
    }
}

// Format price based on type
function formatPrice(value, type) {
    if (type === 'sp500') {
        return value.toLocaleString('en-US', { minimumFractionDigits: 2, maximumFractionDigits: 2 });
    } else {
        return '$' + value.toLocaleString('en-US', { minimumFractionDigits: 2, maximumFractionDigits: 2 });
    }
}

// Update signals
async function updateSignals() {
    try {
        const response = await fetch('/api/dashboard/signals/?limit=5');
        const signals = await response.json();
        
        const signalList = document.querySelector('.signal-list');
        if (!signalList) return;
        
        // Update signal list (simplified - in production, use a template engine)
        signalList.innerHTML = signals.map(signal => `
            <div class="signal-item">
                <div class="signal-header">
                    <span class="signal-asset">${signal.asset}</span>
                    <span class="signal-type ${signal.signal_type.toLowerCase()}">${signal.signal_type}</span>
                    <span class="signal-time">${formatTimeAgo(signal.created_at)}</span>
                </div>
                ${signal.entry_price ? `
                    <div class="signal-details">
                        <span>Entry: ${signal.entry_price}</span>
                        <span>Target: ${signal.target_price}</span>
                    </div>
                    <div class="signal-confidence">Confidence: ${signal.confidence}%</div>
                ` : `
                    <div class="signal-notes">${signal.notes}</div>
                `}
            </div>
        `).join('');
    } catch (error) {
        console.error('Error updating signals:', error);
    }
}

// Update sentiment
async function updateSentiment() {
    try {
        const response = await fetch('/api/dashboard/sentiment/');
        const data = await response.json();
        
        const gaugeScore = document.querySelector('.gauge-score');
        const gaugeLabel = document.querySelector('.gauge-label');
        
        if (gaugeScore) {
            gaugeScore.textContent = data.score;
        }
        
        if (gaugeLabel) {
            gaugeLabel.textContent = data.level.toUpperCase().replace('_', ' ');
        }
        
        // Update gauge visualization if Chart.js is available
        updateSentimentGauge(data.score);
    } catch (error) {
        console.error('Error updating sentiment:', error);
    }
}

// Update sentiment gauge visualization
function updateSentimentGauge(score) {
    const canvas = document.getElementById('sentimentGauge');
    if (!canvas) return;
    
    const ctx = canvas.getContext('2d');
    const centerX = canvas.width / 2;
    const centerY = canvas.height / 2;
    const radius = Math.min(centerX, centerY) - 10;
    
    // Clear canvas
    ctx.clearRect(0, 0, canvas.width, canvas.height);
    
    // Draw gauge arc
    ctx.beginPath();
    ctx.arc(centerX, centerY, radius, Math.PI, 0);
    ctx.lineWidth = 20;
    ctx.strokeStyle = '#1a1f2e';
    ctx.stroke();
    
    // Draw filled arc based on score
    const angle = Math.PI - (score / 100) * Math.PI;
    ctx.beginPath();
    ctx.arc(centerX, centerY, radius, Math.PI, angle);
    ctx.lineWidth = 20;
    ctx.strokeStyle = score >= 50 ? '#10b981' : '#ef4444';
    ctx.stroke();
}

// Apply widths for elements with `.usage-fill` using their `data-usage` attribute
function applyUsageWidths() {
    document.querySelectorAll('.usage-fill').forEach(el => {
        const usage = el.dataset.usage;
        let val = parseFloat(usage);
        if (isNaN(val)) val = 0;
        val = Math.max(0, Math.min(100, val));
        el.style.width = val + '%';
    });
}

// Format time ago
function formatTimeAgo(timestamp) {
    const now = new Date();
    const time = new Date(timestamp);
    const diff = Math.floor((now - time) / 1000);
    
    if (diff < 60) return `${diff}s ago`;
    if (diff < 3600) return `${Math.floor(diff / 60)}m ago`;
    if (diff < 86400) return `${Math.floor(diff / 3600)}h ago`;
    return `${Math.floor(diff / 86400)}d ago`;
}

// Initialize form handlers
function initFormHandlers() {
    // Forecast form slider handlers
    const horizonSlider = document.getElementById('horizon-slider');
    if (horizonSlider) {
        horizonSlider.addEventListener('input', function(e) {
            const valueEl = document.getElementById('horizon-value');
            if (valueEl) {
                valueEl.textContent = e.target.value + ' Days';
            }
        });
    }
    
    const riskSlider = document.getElementById('risk-slider');
    if (riskSlider) {
        const riskLabels = ['Low', 'Medium', 'High'];
        riskSlider.addEventListener('input', function(e) {
            const valueEl = document.getElementById('risk-value');
            if (valueEl) {
                valueEl.textContent = riskLabels[e.target.value] || 'Medium';
            }
        });
    }
    
    // Asset button handlers
    document.querySelectorAll('.asset-btn').forEach(btn => {
        btn.addEventListener('click', function() {
            const select = document.querySelector('select[name="asset"]');
            if (select) {
                select.value = this.dataset.symbol;
            }
        });
    });
}

// Initialize chart updates
function initChartUpdates() {
    // Update price charts periodically
    const priceCharts = document.querySelectorAll('#priceChart, #btcChart');
    priceCharts.forEach(canvas => {
        if (canvas) {
            setInterval(() => {
                updatePriceChart(canvas);
            }, 10000);
        }
    });
}

// Update price chart
async function updatePriceChart(canvas) {
    const chart = Chart.getChart(canvas);
    if (!chart) return;
    
    // Get asset symbol from context
    const symbol = canvas.dataset.symbol || 'BTC/USD';
    
    try {
        const response = await fetch(`/api/dashboard/price-data/${symbol}/?hours=24`);
        const data = await response.json();
        
        if (data.length > 0) {
            chart.data.datasets[0].data = data.map(point => ({
                x: new Date(point.timestamp).toLocaleTimeString(),
                y: point.price
            }));
            chart.update('none'); // Update without animation
        }
    } catch (error) {
        console.error('Error updating price chart:', error);
    }
}

// Utility: Debounce function
function debounce(func, wait) {
    let timeout;
    return function executedFunction(...args) {
        const later = () => {
            clearTimeout(timeout);
            func(...args);
        };
        clearTimeout(timeout);
        timeout = setTimeout(later, wait);
    };
}

// Export functions for use in templates
window.MarketMicrostructure = {
    updateMarketOverview,
    updateSignals,
    updateSentiment,
    formatTimeAgo,
};


