// forecast/static/forecast/js/forecast.js
// Calls /api/forecast/backtest/run/ and renders Plotly charts

function getCookie(name) {
    const cookies = document.cookie.split(';').map(c => c.trim());
    for (const c of cookies) {
        if (c.startsWith(name + '=')) return decodeURIComponent(c.split('=')[1]);
    }
    return null;
}

function movingAverage(values, window) {
    const res = [];
    for (let i = 0; i < values.length; i++) {
        if (i < window - 1) { res.push(null); continue; }
        let sum = 0;
        for (let j = i - window + 1; j <= i; j++) sum += values[j];
        res.push(sum / window);
    }
    return res;
}

async function runBacktest() {
    const symbol = document.getElementById('bt_symbol').value || 'BTCUSDT';
    const interval = document.getElementById('bt_interval').value || '1d';
    const short_window = parseInt(document.getElementById('bt_short').value || '10');
    const long_window = parseInt(document.getElementById('bt_long').value || '50');
    const forecast_days = parseInt(document.getElementById('bt_forecast_days').value || '5');
    const initial_capital = parseFloat(document.getElementById('bt_capital').value || '10000');
    const save = document.getElementById('bt_save').checked;

    const payload = {
        symbol: symbol,
        interval: interval,
        short_window: short_window,
        long_window: long_window,
        forecast_days: forecast_days,
        initial_capital: initial_capital,
        save: save
    };

    const csrftoken = getCookie('csrftoken');

    const resp = await fetch('/api/forecast/backtest/run/', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'X-CSRFToken': csrftoken
        },
        credentials: 'same-origin',
        body: JSON.stringify(payload)
    });

    if (!resp.ok) {
        const txt = await resp.text();
        console.error('Backtest API error', resp.status, txt);
        alert('Backtest failed: ' + resp.status);
        return;
    }

    const data = await resp.json();
    if (!data || !data.candles || data.candles.length === 0) {
        alert('No candle data returned from server. Please check symbol or try again.');
        console.warn('Backtest result missing candles:', data);
        return;
    }
    renderPlots(data, short_window, long_window);
}

function renderPlots(result, short_window, long_window) {
    // Candles
    const candles = result.candles || [];
    const times = candles.map(c => c.timestamp);
    const opens = candles.map(c => c.open);
    const highs = candles.map(c => c.high);
    const lows = candles.map(c => c.low);
    const closes = candles.map(c => c.close);

    const priceTraces = [];
    priceTraces.push({
        x: times,
        open: opens,
        high: highs,
        low: lows,
        close: closes,
        type: 'candlestick',
        name: 'Price',
        increasing: { line: { color: '#10b981' } },
        decreasing: { line: { color: '#ef4444' } }
    });

    // SMAs
    const smaShort = movingAverage(closes.map(Number), short_window);
    const smaLong = movingAverage(closes.map(Number), long_window);
    priceTraces.push({ x: times, y: smaShort, type: 'scatter', mode: 'lines', name: `SMA ${short_window}`, line: {color: 'orange', width:1} });
    priceTraces.push({ x: times, y: smaLong, type: 'scatter', mode: 'lines', name: `SMA ${long_window}`, line: {color: 'blue', width:1} });

    // Prediction overlay
    if (result.forecast_points && result.forecast_points.length) {
        const fts = result.forecast_points.map(p => p.date);
        const fprices = result.forecast_points.map(p => p.price);
        const fupper = result.forecast_points.map(p => p.confidence_upper);
        const flower = result.forecast_points.map(p => p.confidence_lower);

        priceTraces.push({ x: fts, y: fprices, type: 'scatter', mode: 'lines+markers', name: 'Prediction', line: {color: 'yellow', dash: 'dot'} });

        // Confidence band (upper then lower - fill)
        priceTraces.push({ x: fts, y: fupper, type: 'scatter', mode: 'lines', line: {width:0}, showlegend:false });
        priceTraces.push({ x: fts, y: flower, type: 'scatter', mode: 'lines', fill: 'tonexty', fillcolor: 'rgba(255,255,0,0.12)', line: {width:0}, showlegend:false });
    }

    // Trade markers
    const buys = (result.trades || []).filter(t => (t.type || '').toLowerCase() === 'buy');
    const sells = (result.trades || []).filter(t => (t.type || '').toLowerCase() === 'sell');
    if (buys.length) {
        priceTraces.push({ x: buys.map(b => b.timestamp), y: buys.map(b => b.price), mode: 'markers', type: 'scatter', name: 'Buys', marker: {color: 'green', size:10, symbol:'triangle-up'} });
    }
    if (sells.length) {
        priceTraces.push({ x: sells.map(s => s.timestamp), y: sells.map(s => s.price), mode: 'markers', type: 'scatter', name: 'Sells', marker: {color: 'red', size:10, symbol:'triangle-down'} });
    }

    const priceLayout = {
        title: `${document.getElementById('bt_symbol').value} Price & Prediction`,
        xaxis: { type: 'date', gridcolor: 'rgba(255,255,255,0.06)', tickcolor: '#9ca3af' },
        yaxis: { title: 'Price (USD)', gridcolor: 'rgba(255,255,255,0.06)', tickcolor: '#9ca3af' },
        showlegend: true,
        template: 'plotly_dark',
        paper_bgcolor: '#071026',
        plot_bgcolor: '#071026',
        font: { color: '#cbd5e1' }
    };
    Plotly.newPlot('pricePlot', priceTraces, priceLayout, { responsive: true });

    // Equity plot
    const equity = result.equity || [];
    if (equity.length) {
        const eq_x = equity.map(e => e.timestamp);
        const eq_y = equity.map(e => e.equity);
        const eqTrace = [{ x: eq_x, y: eq_y, type: 'scatter', mode: 'lines', name: 'Equity', line: {color: '#10b981'} }];
        const eqLayout = {
            title: 'Equity Curve',
            xaxis: { type: 'date', gridcolor: 'rgba(255,255,255,0.06)', tickcolor: '#9ca3af' },
            yaxis: { title: 'Equity (USD)', gridcolor: 'rgba(255,255,255,0.06)', tickcolor: '#9ca3af' },
            template: 'plotly_dark',
            paper_bgcolor: '#071026',
            plot_bgcolor: '#071026',
            font: { color: '#cbd5e1' }
        };
        Plotly.newPlot('equityPlot', eqTrace, eqLayout, { responsive: true });
    }
}

document.addEventListener('DOMContentLoaded', function() {
    const runBtn = document.getElementById('bt_run');
    if (runBtn) runBtn.addEventListener('click', function() { runBacktest(); });
});
