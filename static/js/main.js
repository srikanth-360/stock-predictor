// ============================================================================
// STOCK PREDICTOR - FRONTEND JAVASCRIPT
// ============================================================================

document.addEventListener('DOMContentLoaded', function() {
    // DOM Elements
    const tickerInput = document.getElementById('tickerInput');
    const predictBtn = document.getElementById('predictBtn');
    const resultsSection = document.getElementById('resultsSection');
    const errorMessage = document.getElementById('errorMessage');
    const stockChips = document.querySelectorAll('.stock-chip');

    // Event Listeners
    predictBtn.addEventListener('click', handlePredict);
    tickerInput.addEventListener('keypress', function(e) {
        if (e.key === 'Enter') {
            handlePredict();
        }
    });

    stockChips.forEach(chip => {
        chip.addEventListener('click', function() {
            tickerInput.value = this.dataset.ticker;
            handlePredict();
        });
    });

    // Main Prediction Handler
    async function handlePredict() {
        const ticker = tickerInput.value.trim().toUpperCase();
        
        if (!ticker) {
            showError('Please enter a ticker symbol');
            return;
        }

        // Show loading state
        setLoadingState(true);
        hideError();
        resultsSection.style.display = 'none';

        try {
            const response = await fetch('/predict', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({ ticker })
            });

            const data = await response.json();

            if (!response.ok) {
                throw new Error(data.error || 'Failed to fetch prediction');
            }

            displayResults(data);
            resultsSection.style.display = 'block';
            
            // Smooth scroll to results
            setTimeout(() => {
                resultsSection.scrollIntoView({ behavior: 'smooth', block: 'start' });
            }, 100);

        } catch (error) {
            showError(error.message);
        } finally {
            setLoadingState(false);
        }
    }

    // Display Results
    function displayResults(data) {
        // Company Info
        document.getElementById('companyName').textContent = data.company_name;
        document.getElementById('tickerSymbol').textContent = data.ticker;
        document.getElementById('currentPrice').textContent = formatCurrency(data.current_price);
        
        // Display price timestamp with indicator (only if element exists)
        const timestampEl = document.getElementById('priceTimestamp');
        if (timestampEl && data.price_timestamp) {
            let timestampText = '';
            if (data.is_today_price) {
                timestampText = `📊 Current (Today) - ${data.price_timestamp}`;
            } else {
                timestampText = `⚠️ Previous Close - ${data.price_timestamp}`;
            }
            timestampEl.textContent = timestampText;
            timestampEl.style.color = data.is_today_price ? '#10b981' : '#f59e0b';
        }

        // Prediction Info
        document.getElementById('predictionDate').textContent = new Date(data.prediction_date).toLocaleDateString('en-US', {
            weekday: 'long',
            year: 'numeric',
            month: 'long',
            day: 'numeric'
        });
        document.getElementById('predictedPrice').textContent = formatCurrency(data.predicted_price);
        
        // Price Change
        const priceChangeEl = document.getElementById('priceChange');
        const changeText = `${data.price_change >= 0 ? '+' : ''}${formatCurrency(data.price_change)} (${data.price_change_percent >= 0 ? '+' : ''}${data.price_change_percent.toFixed(2)}%)`;
        priceChangeEl.textContent = changeText;

        // Signal Badge
        const signalBadge = document.getElementById('signalBadge');
        const signalText = document.getElementById('signalText');
        signalBadge.className = 'signal-badge';
        signalBadge.classList.add(data.signal.toLowerCase());
        signalText.textContent = data.signal;

        // Model Performance
        document.getElementById('accuracy').textContent = `${data.accuracy.toFixed(2)}%`;
        document.getElementById('mape').textContent = `${data.mape.toFixed(2)}%`;
        document.getElementById('rmse').textContent = formatCurrency(data.rmse);
        document.getElementById('mae').textContent = formatCurrency(data.mae);

        // Reasoning
        displayReasoning(data.reasoning);

        // Charts
        renderPriceChart(data);
        renderTechnicalChart(data);
        renderPerformanceChart(data);
        //renderVolumeChart(data);
    }

    // Display Reasoning
    function displayReasoning(reasoning) {
        const container = document.getElementById('reasoningContent');
        container.innerHTML = '';

        reasoning.forEach(item => {
            const reasoningItem = document.createElement('div');
            reasoningItem.className = 'reasoning-item';
            
            // Parse markdown-style bold text
            const formattedText = item.replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>');
            reasoningItem.innerHTML = formattedText;
            
            container.appendChild(reasoningItem);
        });
    }

    // Render Price History Chart
    function renderPriceChart(data) {
        const dates = data.historical_data.dates;
        const close = data.historical_data.close;

        // Add prediction point
        const predictionDate = new Date();
        predictionDate.setDate(predictionDate.getDate() + 1);
        const allDates = [...dates, predictionDate.toISOString().split('T')[0]];
        const allPrices = [...close, data.predicted_price];

        const trace1 = {
            x: dates,
            y: close,
            type: 'scatter',
            mode: 'lines',
            name: 'Historical Price',
            line: {
                color: '#667eea',
                width: 2
            }
        };

        const trace2 = {
            x: [dates[dates.length - 1], allDates[allDates.length - 1]],
            y: [close[close.length - 1], data.predicted_price],
            type: 'scatter',
            mode: 'lines+markers',
            name: 'Prediction',
            line: {
                color: '#10b981',
                width: 3,
                dash: 'dash'
            },
            marker: {
                size: 10,
                color: '#10b981'
            }
        };

        const layout = {
            title: false,
            xaxis: {
                title: 'Date',
                showgrid: false
            },
            yaxis: {
                title: 'Price',
                showgrid: true,
                gridcolor: '#f3f4f6'
            },
            plot_bgcolor: '#ffffff',
            paper_bgcolor: '#ffffff',
            font: {
                family: 'Inter, sans-serif'
            },
            margin: {
                l: 60,
                r: 40,
                t: 20,
                b: 60
            },
            legend: {
                orientation: 'h',
                y: -0.2
            }
        };

        Plotly.newPlot('priceChart', [trace1, trace2], layout, { responsive: true });
    }

    // Render Technical Indicators Chart
    function renderTechnicalChart(data) {
        const dates = data.historical_data.dates;
        const close = data.historical_data.close;
        const ti = data.technical_indicators;

        // Calculate moving averages for visualization
        const ma20 = Array(close.length).fill(ti.ma_20);
        const ma50 = Array(close.length).fill(ti.ma_50);

        const trace1 = {
            x: dates,
            y: close,
            type: 'scatter',
            mode: 'lines',
            name: 'Price',
            line: { color: '#667eea', width: 2 }
        };

        const trace2 = {
            x: dates,
            y: ma20,
            type: 'scatter',
            mode: 'lines',
            name: 'MA 20',
            line: { color: '#f59e0b', width: 1.5, dash: 'dash' }
        };

        const trace3 = {
            x: dates,
            y: ma50,
            type: 'scatter',
            mode: 'lines',
            name: 'MA 50',
            line: { color: '#ef4444', width: 1.5, dash: 'dash' }
        };

        const layout = {
            title: false,
            xaxis: { title: 'Date', showgrid: false },
            yaxis: { title: 'Price', showgrid: true, gridcolor: '#f3f4f6' },
            plot_bgcolor: '#ffffff',
            paper_bgcolor: '#ffffff',
            font: { family: 'Inter, sans-serif' },
            margin: { l: 60, r: 40, t: 20, b: 60 },
            legend: { orientation: 'h', y: -0.2 }
        };

        Plotly.newPlot('technicalChart', [trace1, trace2, trace3], layout, { responsive: true });
    }

    // Render Performance Chart
    function renderPerformanceChart(data) {
        const predicted = data.predictions_vs_actual.predicted;
        const actual = data.predictions_vs_actual.actual;
        const indices = Array.from({ length: predicted.length }, (_, i) => i + 1);

        const trace1 = {
            x: indices,
            y: actual,
            type: 'scatter',
            mode: 'lines+markers',
            name: 'Actual',
            line: { color: '#ef4444', width: 2 },
            marker: { size: 6 }
        };

        const trace2 = {
            x: indices,
            y: predicted,
            type: 'scatter',
            mode: 'lines+markers',
            name: 'Predicted',
            line: { color: '#10b981', width: 2 },
            marker: { size: 6 }
        };

        const layout = {
            title: false,
            xaxis: { title: 'Time Steps (Last 30 predictions)', showgrid: false },
            yaxis: { title: 'Price', showgrid: true, gridcolor: '#f3f4f6' },
            plot_bgcolor: '#ffffff',
            paper_bgcolor: '#ffffff',
            font: { family: 'Inter, sans-serif' },
            margin: { l: 60, r: 40, t: 20, b: 60 },
            legend: { orientation: 'h', y: -0.2 }
        };

        Plotly.newPlot('performanceChart', [trace1, trace2], layout, { responsive: true });
    }

    // Render Volume Chart
    /*function renderVolumeChart(data) {
        const dates = data.historical_data.dates;
        const volume = data.historical_data.volume;

        const colors = volume.map((v, i) => {
            if (i === 0) return '#667eea';
            return data.historical_data.close[i] >= data.historical_data.close[i - 1] ? '#10b981' : '#ef4444';
        });

        const trace = {
            x: dates,
            y: volume,
            type: 'bar',
            name: 'Volume',
            marker: {
                color: colors
            }
        };

        const layout = {
            title: false,
            xaxis: { title: 'Date', showgrid: false },
            yaxis: { title: 'Volume', showgrid: true, gridcolor: '#f3f4f6' },
            plot_bgcolor: '#ffffff',
            paper_bgcolor: '#ffffff',
            font: { family: 'Inter, sans-serif' },
            margin: { l: 60, r: 40, t: 20, b: 60 },
            showlegend: false
        };

        Plotly.newPlot('volumeChart', [trace], layout, { responsive: true });
    }*/

    // Utility Functions
    function formatCurrency(value) {
        return new Intl.NumberFormat('en-IN', {
            style: 'currency',
            currency: 'INR',
            minimumFractionDigits: 2,
            maximumFractionDigits: 2
        }).format(value);
    }

    function setLoadingState(isLoading) {
        const btnText = predictBtn.querySelector('.btn-text');
        const loader = predictBtn.querySelector('.loader');

        if (isLoading) {
            btnText.style.display = 'none';
            loader.style.display = 'inline-block';
            predictBtn.disabled = true;
            tickerInput.disabled = true;
        } else {
            btnText.style.display = 'inline';
            loader.style.display = 'none';
            predictBtn.disabled = false;
            tickerInput.disabled = false;
        }
    }

    function showError(message) {
        errorMessage.style.display = 'block';
        document.getElementById('errorText').textContent = message;
        errorMessage.scrollIntoView({ behavior: 'smooth', block: 'center' });
    }

    function hideError() {
        errorMessage.style.display = 'none';
    }
});