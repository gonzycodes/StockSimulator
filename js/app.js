// Configuration
        const API_BASE = 'http://localhost:5000/api';
        
        // State
        let currentSymbol = 'AAPL';
        let currentPrice = 0;
        let currentPeriod = '5d';
        let currentInterval = '15m';
        let currentOrderType = 'market';
        let chart = null;
        let candlestickSeries = null;
        let markersSeries = null;  // For showing buy/sell markers
        let portfolio = { cash: 10000, holdings: {} };
        let priceUpdateInterval = null;
        let lastCandleTime = 0;
        let lastFetchTime = 0;
        let cachedPrice = null;
        let fetchInProgress = false;
        let tradeHistory = [];  // Store all trades for this session
        let stopLossOrders = {}; // Store stop loss orders per symbol: {symbol: {price: X, quantity: Y}}
        let stopLossSeries = null; // Price line for stop loss visualization
        let takeProfitOrders = {}; // Store take profit orders per symbol
        let takeProfitSeries = null; // Price line for take profit visualization

        // Initialize chart
        function initChart() {
            const chartContainer = document.getElementById('chart');
            chart = LightweightCharts.createChart(chartContainer, {
                layout: {
                    background: { color: '#0a0e14' },
                    textColor: '#e6edf3',
                },
                grid: {
                    vertLines: { color: '#1a1f2e' },
                    horzLines: { color: '#1a1f2e' },
                },
                crosshair: {
                    mode: LightweightCharts.CrosshairMode.Normal,
                },
                rightPriceScale: {
                    borderColor: '#30363d',
                },
                timeScale: {
                    borderColor: '#30363d',
                    timeVisible: true,
                    secondsVisible: false,
                },
                watermark: {
                    visible: false,
                    fontSize: 48,
                    horzAlign: 'center',
                    vertAlign: 'center',
                    color: 'rgba(230, 237, 243, 0.05)',
                    text: 'Stock Simulator',
                },
                localization: {
                    locale: 'sv-SE',
                    timeFormatter: (timestamp) => {
                        const date = new Date(timestamp * 1000);
                        const hours = String(date.getHours()).padStart(2, '0');
                        const minutes = String(date.getMinutes()).padStart(2, '0');
                        return `${hours}:${minutes}`;
                    },
                },
            });

            candlestickSeries = chart.addCandlestickSeries({
                upColor: '#00ff88',
                downColor: '#ff3366',
                borderUpColor: '#00ff88',
                borderDownColor: '#ff3366',
                wickUpColor: '#00ff88',
                wickDownColor: '#ff3366',
            });
            
            // Add series for trade markers (buy/sell indicators)
            markersSeries = candlestickSeries;

            // Handle resize
            new ResizeObserver(() => {
                chart.timeScale().fitContent();
            }).observe(chartContainer);
        }

        // Add trade marker to chart
        function addTradeMarker(action, ticker, quantity, price, timestamp) {
            if (!markersSeries || ticker !== currentSymbol) return;
            
            // Store trade in history
            const trade = {
                action: action,
                ticker: ticker,
                quantity: quantity,
                price: price,
                timestamp: timestamp || Math.floor(Date.now() / 1000),
            };
            
            tradeHistory.push(trade);
            
            // Update markers on chart
            updateTradeMarkers();
        }
        
        // Update all trade markers on chart
        function updateTradeMarkers() {
            if (!markersSeries) return;
            
            // Filter trades for current symbol
            const symbolTrades = tradeHistory.filter(t => t.ticker === currentSymbol);
            
            // Create markers array
            const markers = symbolTrades.map(trade => {
                const isBuy = trade.action === 'buy';
                
                return {
                    time: trade.timestamp,
                    position: isBuy ? 'belowBar' : 'aboveBar',
                    color: isBuy ? '#00ff88' : '#ff3366',
                    shape: isBuy ? 'arrowUp' : 'arrowDown',
                    text: isBuy ? `BUY ${trade.quantity}` : `SELL ${trade.quantity}`,
                };
            });
            
            // Set markers on series
            markersSeries.setMarkers(markers);
        }
        
        // Clear trade markers (when switching symbols)
        function clearTradeMarkers() {
            if (markersSeries) {
                markersSeries.setMarkers([]);
            }
        }

        // Set stop loss order
        function setStopLoss() {
            const stopPrice = parseFloat(document.getElementById('stopLossInput').value);
            
            if (!stopPrice || stopPrice <= 0) {
                showNotification('Enter a valid stop loss price', 'error');
                return;
            }

            const holding = portfolio.holdings[currentSymbol] || 0;
            if (holding <= 0) {
                showNotification('You need to own shares to set a stop loss', 'error');
                return;
            }

            // Validate stop loss is below current price (for long positions)
            if (stopPrice >= currentPrice) {
                showNotification('Stop loss must be below current price', 'error');
                return;
            }

            // Store stop loss order
            stopLossOrders[currentSymbol] = {
                price: stopPrice,
                quantity: holding,
            };

            // Show stop loss line on chart
            updateStopLossLine();

            // Update UI
            document.getElementById('setStopLossBtn').style.display = 'none';
            document.getElementById('clearStopLossBtn').style.display = 'block';
            document.getElementById('stopLossInfo').style.display = 'block';
            document.getElementById('stopLossInfo').innerHTML = `
                <strong>Active Stop Loss:</strong><br>
                Price: ${stopPrice.toFixed(2)} SEK<br>
                Quantity: ${holding.toFixed(4)} shares<br>
                <span style="color: var(--text-secondary); font-size: 10px;">
                Will auto-sell if price drops to ${stopPrice.toFixed(2)}
                </span>
            `;

            showNotification(`Stop loss set at ${stopPrice.toFixed(2)} SEK`, 'success');
        }

        // Clear stop loss
        function clearStopLoss() {
            delete stopLossOrders[currentSymbol];
            updateStopLossLine();

            document.getElementById('stopLossInput').value = '';
            document.getElementById('setStopLossBtn').style.display = 'block';
            document.getElementById('clearStopLossBtn').style.display = 'none';
            document.getElementById('stopLossInfo').style.display = 'none';

            showNotification('Stop loss cleared', 'success');
        }

        // Update stop loss line on chart
        function updateStopLossLine() {
            // Remove existing line
            if (stopLossSeries) {
                candlestickSeries.removePriceLine(stopLossSeries);
                stopLossSeries = null;
            }

            // Add new line if stop loss exists for current symbol
            const stopLoss = stopLossOrders[currentSymbol];
            if (stopLoss) {
                stopLossSeries = candlestickSeries.createPriceLine({
                    price: stopLoss.price,
                    color: '#ffcc00',
                    lineWidth: 2,
                    lineStyle: 2, // Dashed
                    axisLabelVisible: true,
                    title: `Stop Loss (${stopLoss.quantity.toFixed(4)})`,
                });
            }
        }

        // Check if stop loss is triggered
        function checkStopLoss() {
            const stopLoss = stopLossOrders[currentSymbol];
            if (!stopLoss) return;

            // If current price drops to or below stop loss, execute sell
            if (currentPrice <= stopLoss.price) {
                console.log(`Stop loss triggered! Selling ${stopLoss.quantity} ${currentSymbol} at ${currentPrice}`);
                
                // Execute automatic sell
                executeStopLossSell(stopLoss.quantity);
                
                // Remove stop loss
                delete stopLossOrders[currentSymbol];
                updateStopLossLine();
                
                document.getElementById('setStopLossBtn').style.display = 'block';
                document.getElementById('clearStopLossBtn').style.display = 'none';
                document.getElementById('stopLossInfo').style.display = 'none';
            }
        }

        // Execute stop loss sell
        async function executeStopLossSell(quantity) {
            showNotification(`🛡️ Stop Loss Triggered! Selling ${quantity} ${currentSymbol}`, 'error');
            
            // Set quantity and execute sell
            document.getElementById('quantityInput').value = quantity;
            await executeTrade('sell');
        }

        // Set take profit order
        function setTakeProfit() {
            const targetPrice = parseFloat(document.getElementById('takeProfitInput').value);
            
            if (!targetPrice || targetPrice <= 0) {
                showNotification('Enter a valid take profit price', 'error');
                return;
            }

            const holding = portfolio.holdings[currentSymbol] || 0;
            if (holding <= 0) {
                showNotification('You need to own shares to set a take profit', 'error');
                return;
            }

            // Validate take profit is above current price (for long positions)
            if (targetPrice <= currentPrice) {
                showNotification('Take profit must be above current price', 'error');
                return;
            }

            // Store take profit order
            takeProfitOrders[currentSymbol] = {
                price: targetPrice,
                quantity: holding,
            };

            // Show take profit line on chart
            updateTakeProfitLine();

            // Update UI
            document.getElementById('setTakeProfitBtn').style.display = 'none';
            document.getElementById('clearTakeProfitBtn').style.display = 'block';
            document.getElementById('takeProfitInfo').style.display = 'block';
            document.getElementById('takeProfitInfo').innerHTML = `
                <strong>Active Take Profit:</strong><br>
                Price: ${targetPrice.toFixed(2)} SEK<br>
                Quantity: ${holding.toFixed(4)} shares<br>
                <span style="color: var(--text-secondary); font-size: 10px;">
                Will auto-sell if price rises to ${targetPrice.toFixed(2)}
                </span>
            `;

            showNotification(`Take profit set at ${targetPrice.toFixed(2)} SEK`, 'success');
        }

        // Clear take profit
        function clearTakeProfit() {
            delete takeProfitOrders[currentSymbol];
            updateTakeProfitLine();

            document.getElementById('takeProfitInput').value = '';
            document.getElementById('setTakeProfitBtn').style.display = 'block';
            document.getElementById('clearTakeProfitBtn').style.display = 'none';
            document.getElementById('takeProfitInfo').style.display = 'none';

            showNotification('Take profit cleared', 'success');
        }

        // Update take profit line on chart
        function updateTakeProfitLine() {
            // Remove existing line
            if (takeProfitSeries) {
                candlestickSeries.removePriceLine(takeProfitSeries);
                takeProfitSeries = null;
            }

            // Add new line if take profit exists for current symbol
            const takeProfit = takeProfitOrders[currentSymbol];
            if (takeProfit) {
                takeProfitSeries = candlestickSeries.createPriceLine({
                    price: takeProfit.price,
                    color: '#00ff88',
                    lineWidth: 2,
                    lineStyle: 2, // Dashed
                    axisLabelVisible: true,
                    title: `Take Profit (${takeProfit.quantity.toFixed(4)})`,
                });
            }
        }

        // Check if take profit is triggered
        function checkTakeProfit() {
            const takeProfit = takeProfitOrders[currentSymbol];
            if (!takeProfit) return;

            // If current price rises to or above take profit, execute sell
            if (currentPrice >= takeProfit.price) {
                console.log(`Take profit triggered! Selling ${takeProfit.quantity} ${currentSymbol} at ${currentPrice}`);
                
                // Execute automatic sell
                executeTakeProfitSell(takeProfit.quantity);
                
                // Remove take profit
                delete takeProfitOrders[currentSymbol];
                updateTakeProfitLine();
                
                document.getElementById('setTakeProfitBtn').style.display = 'block';
                document.getElementById('clearTakeProfitBtn').style.display = 'none';
                document.getElementById('takeProfitInfo').style.display = 'none';
            }
        }

        // Execute take profit sell
        async function executeTakeProfitSell(quantity) {
            showNotification(`🎯 Take Profit Triggered! Selling ${quantity} ${currentSymbol}`, 'success');
            
            // Set quantity and execute sell
            document.getElementById('quantityInput').value = quantity;
            await executeTrade('sell');
        }

        // Fixed scale - auto-scroll to current price
        function fixedScale() {
            if (!chart) return;
            
            // Get visible range
            const timeScale = chart.timeScale();
            
            // Fit content to show recent data with current price centered
            timeScale.fitContent();
            
            // Small animation feedback
            const btn = document.getElementById('fixedScaleBtn');
            btn.style.transform = 'scale(0.95)';
            setTimeout(() => {
                btn.style.transform = 'scale(1)';
            }, 100);
        }
        function startPriceUpdates() {
            // Clear any existing interval
            if (priceUpdateInterval) {
                clearInterval(priceUpdateInterval);
            }
            
            // Fast updates - 500ms (0.5 seconds) for all timeframes
            // This matches TradingView's real-time speed
            const updateFrequency = 500;
            
            // Start interval
            priceUpdateInterval = setInterval(async () => {
                await updateLivePrice();
            }, updateFrequency);
            
            // Initial update
            updateLivePrice();
        }

        // Stop price updates
        function stopPriceUpdates() {
            if (priceUpdateInterval) {
                clearInterval(priceUpdateInterval);
                priceUpdateInterval = null;
            }
        }

        // Update live price and current candle
        async function updateLivePrice() {
            // Prevent concurrent fetches
            if (fetchInProgress) return;
            
            try {
                fetchInProgress = true;
                
                // Fetch fresh quote
                const quote = await fetchQuote(currentSymbol);
                if (!quote || !quote.price) return;
                
                const newPrice = quote.price;
                
                // Only update if price changed significantly (or first fetch)
                if (cachedPrice === null || Math.abs(newPrice - cachedPrice) > 0.001) {
                    currentPrice = newPrice;
                    cachedPrice = newPrice;
                    lastFetchTime = Date.now();
                    
                    // Update price display with flash effect
                    const priceEl = document.getElementById('currentPrice');
                    const priceText = quote.price_sek 
                        ? `${newPrice.toFixed(2)} ${quote.currency} (${quote.price_sek.toFixed(2)} SEK)`
                        : `${newPrice.toFixed(2)} ${quote.currency}`;
                    
                    // Determine if price went up or down
                    const priceChange = cachedPrice !== null ? newPrice - cachedPrice : 0;
                    
                    priceEl.textContent = priceText;
                    
                    // Flash effect based on price movement
                    if (priceChange > 0) {
                        priceEl.style.color = 'var(--accent-green)';
                        setTimeout(() => {
                            priceEl.style.color = 'var(--text-primary)';
                        }, 200);
                    } else if (priceChange < 0) {
                        priceEl.style.color = 'var(--accent-red)';
                        setTimeout(() => {
                            priceEl.style.color = 'var(--text-primary)';
                        }, 200);
                    }
                    
                    // Update the current (last) candle with new price
                    updateCurrentCandle(newPrice);
                    
                    // Check stop loss triggers
                    checkStopLoss();
                    
                    // Check take profit triggers
                    checkTakeProfit();
                    
                    // Update estimate if needed
                    updateEstimate();
                }
                
            } catch (error) {
                console.error('Error updating live price:', error);
            } finally {
                fetchInProgress = false;
            }
        }

        // Update the current candle with live price
        function updateCurrentCandle(newPrice) {
            try {
                // Get current candle data
                const now = Math.floor(Date.now() / 1000);
                
                // Calculate interval duration in seconds
                const intervalSeconds = {
                    '1m': 60,
                    '5m': 300,
                    '15m': 900,
                    '1h': 3600,
                    '1d': 86400,
                    '1wk': 604800
                }[currentInterval] || 300;
                
                // Round to current candle time
                const currentCandleTime = Math.floor(now / intervalSeconds) * intervalSeconds;
                
                // Get existing data
                const data = candlestickSeries.data();
                if (!data || data.length === 0) return;
                
                const lastCandle = data[data.length - 1];
                
                // Check if we're still in the same candle period
                if (lastCandle.time === currentCandleTime || lastCandleTime === currentCandleTime) {
                    // Update existing candle
                    const updatedCandle = {
                        time: currentCandleTime,
                        open: lastCandle.open,
                        high: Math.max(lastCandle.high, newPrice),
                        low: Math.min(lastCandle.low, newPrice),
                        close: newPrice,
                    };
                    
                    candlestickSeries.update(updatedCandle);
                    lastCandleTime = currentCandleTime;
                    
                } else if (currentCandleTime > lastCandle.time) {
                    // New candle period - create new candle
                    const newCandle = {
                        time: currentCandleTime,
                        open: lastCandle.close,
                        high: newPrice,
                        low: newPrice,
                        close: newPrice,
                    };
                    
                    candlestickSeries.update(newCandle);
                    lastCandleTime = currentCandleTime;
                }
                
                // Update price change calculation
                const firstPrice = data[0].close;
                const change = ((newPrice - firstPrice) / firstPrice) * 100;
                const changeEl = document.getElementById('priceChange');
                changeEl.textContent = (change >= 0 ? '+' : '') + change.toFixed(2) + '%';
                changeEl.className = 'price-change ' + (change >= 0 ? 'positive' : 'negative');
                
            } catch (error) {
                console.error('Error updating candle:', error);
            }
        }
        async function fetchHistoricalData(symbol, period, interval) {
            try {
                const controller = new AbortController();
                const timeoutId = setTimeout(() => controller.abort(), 15000); // 15 second timeout
                
                const response = await fetch(
                    `${API_BASE}/historical/${symbol}?period=${period}&interval=${interval}`,
                    { signal: controller.signal }
                );
                
                clearTimeout(timeoutId);
                
                if (!response.ok) {
                    const error = await response.json();
                    throw new Error(error.error || `API error: ${response.status}`);
                }
                
                const result = await response.json();
                
                if (!result.data || result.data.length === 0) {
                    throw new Error('No data returned from API');
                }
                
                return result.data;
            } catch (error) {
                if (error.name === 'AbortError') {
                    console.error('Request timeout - data fetch took too long');
                    throw new Error('Request timeout. Try a different timeframe.');
                }
                
                console.error('Error fetching historical data:', error);
                throw error;
            }
        }

        // Fetch current quote from API
        async function fetchQuote(symbol) {
            try {
                const response = await fetch(`${API_BASE}/quote/${symbol}`);
                
                if (!response.ok) {
                    throw new Error(`API error: ${response.status}`);
                }
                
                return await response.json();
            } catch (error) {
                console.error('Error fetching quote:', error);
                return null;
            }
        }

        // Fetch portfolio from API
        async function fetchPortfolio() {
            try {
                const response = await fetch(`${API_BASE}/portfolio`);
                
                if (!response.ok) {
                    throw new Error(`API error: ${response.status}`);
                }
                
                const data = await response.json();
                portfolio = {
                    cash: data.cash,
                    holdings: data.holdings,
                    total_value: data.total_value
                };
                return data;
            } catch (error) {
                console.error('Error fetching portfolio:', error);
                return null;
            }
        }

        // Generate mock historical data (fallback)
        function generateMockData(symbol, period) {
            const now = Date.now();
            const intervals = {
                '1d': { count: 78, interval: 5 * 60 * 1000 },      // 5 min bars
                '5d': { count: 390, interval: 5 * 60 * 1000 },     // 5 min bars
                '1mo': { count: 20, interval: 24 * 60 * 60 * 1000 }, // daily
                '3mo': { count: 60, interval: 24 * 60 * 60 * 1000 }, // daily
                '1y': { count: 250, interval: 24 * 60 * 60 * 1000 }, // daily
            };

            const config = intervals[period];
            const basePrice = Math.random() * 200 + 50;
            const data = [];

            for (let i = config.count; i >= 0; i--) {
                const time = new Date(now - i * config.interval);
                const open = basePrice + (Math.random() - 0.5) * 10;
                const volatility = Math.random() * 5;
                const close = open + (Math.random() - 0.5) * volatility;
                const high = Math.max(open, close) + Math.random() * 2;
                const low = Math.min(open, close) - Math.random() * 2;

                data.push({
                    time: Math.floor(time.getTime() / 1000),
                    open: open,
                    high: high,
                    low: low,
                    close: close,
                });
            }

            return data;
        }

        // Update chart data
        async function updateChart(symbol, period, interval) {
            showLoading(true);
            
            // Stop existing price updates
            stopPriceUpdates();
            
            try {
                // Fetch real historical data
                const data = await fetchHistoricalData(symbol, period, interval);
                
                if (!data || data.length === 0) {
                    showNotification('No data available for this timeframe', 'error');
                    showLoading(false);
                    return;
                }
                
                candlestickSeries.setData(data);
                
                // Track last candle time
                lastCandleTime = data[data.length - 1].time;
                
                // Update current price from latest candle
                const lastCandle = data[data.length - 1];
                currentPrice = lastCandle.close;
                
                // Also fetch live quote for more accurate current price
                const quote = await fetchQuote(symbol);
                if (quote && quote.price) {
                    currentPrice = quote.price;
                    
                    // Update price display with currency info
                    const priceText = quote.price_sek 
                        ? `${quote.price.toFixed(2)} ${quote.currency} (${quote.price_sek.toFixed(2)} SEK)`
                        : `${quote.price.toFixed(2)} ${quote.currency}`;
                        
                    document.getElementById('currentPrice').textContent = priceText;
                } else {
                    document.getElementById('currentPrice').textContent = currentPrice.toFixed(2);
                }
                
                // Update symbol - show just the symbol, interval is shown in button
                document.getElementById('currentSymbol').textContent = symbol;
                
                // Calculate price change
                const firstPrice = data[0].close;
                const change = ((currentPrice - firstPrice) / firstPrice) * 100;
                const changeEl = document.getElementById('priceChange');
                changeEl.textContent = (change >= 0 ? '+' : '') + change.toFixed(2) + '%';
                changeEl.className = 'price-change ' + (change >= 0 ? 'positive' : 'negative');

                // Update symbol price in sidebar
                const symbolItem = document.querySelector(`[data-symbol="${symbol}"]`);
                if (symbolItem) {
                    const priceEl = symbolItem.querySelector('.symbol-price');
                    priceEl.textContent = currentPrice.toFixed(2);
                }

                chart.timeScale().fitContent();
                updateEstimate();
                
                // Update trade markers for current symbol
                updateTradeMarkers();
                
                // Update stop loss line for current symbol
                updateStopLossLine();
                
                // Update take profit line for current symbol
                updateTakeProfitLine();
                
                // Update stop loss UI
                const stopLoss = stopLossOrders[currentSymbol];
                if (stopLoss) {
                    document.getElementById('stopLossInput').value = stopLoss.price;
                    document.getElementById('setStopLossBtn').style.display = 'none';
                    document.getElementById('clearStopLossBtn').style.display = 'block';
                    document.getElementById('stopLossInfo').style.display = 'block';
                    document.getElementById('stopLossInfo').innerHTML = `
                        <strong>Active Stop Loss:</strong><br>
                        Price: ${stopLoss.price.toFixed(2)} SEK<br>
                        Quantity: ${stopLoss.quantity.toFixed(4)} shares
                    `;
                } else {
                    document.getElementById('stopLossInput').value = '';
                    document.getElementById('setStopLossBtn').style.display = 'block';
                    document.getElementById('clearStopLossBtn').style.display = 'none';
                    document.getElementById('stopLossInfo').style.display = 'none';
                }
                
                // Update take profit UI
                const takeProfit = takeProfitOrders[currentSymbol];
                if (takeProfit) {
                    document.getElementById('takeProfitInput').value = takeProfit.price;
                    document.getElementById('setTakeProfitBtn').style.display = 'none';
                    document.getElementById('clearTakeProfitBtn').style.display = 'block';
                    document.getElementById('takeProfitInfo').style.display = 'block';
                    document.getElementById('takeProfitInfo').innerHTML = `
                        <strong>Active Take Profit:</strong><br>
                        Price: ${takeProfit.price.toFixed(2)} SEK<br>
                        Quantity: ${takeProfit.quantity.toFixed(4)} shares
                    `;
                } else {
                    document.getElementById('takeProfitInput').value = '';
                    document.getElementById('setTakeProfitBtn').style.display = 'block';
                    document.getElementById('clearTakeProfitBtn').style.display = 'none';
                    document.getElementById('takeProfitInfo').style.display = 'none';
                }
                
                // Start live price updates
                startPriceUpdates();
                
            } catch (error) {
                console.error('Chart update error:', error);
                showNotification(error.message || 'Failed to load chart data', 'error');
            } finally {
                showLoading(false);
            }
        }

        // Show/hide loading
        function showLoading(show) {
            document.getElementById('loading').classList.toggle('active', show);
        }

        // Show notification
        function showNotification(message, type = 'success') {
            const notification = document.createElement('div');
            notification.className = `notification ${type}`;
            notification.textContent = message;
            document.body.appendChild(notification);

            setTimeout(() => {
                notification.remove();
            }, 3000);
        }

        // Update total estimate
        function updateEstimate() {
            const qty = parseFloat(document.getElementById('quantityInput').value) || 0;
            const price = currentOrderType === 'limit' 
                ? (parseFloat(document.getElementById('limitPriceInput').value) || 0)
                : currentPrice;
            
            const total = qty * price;
            document.getElementById('totalEstimate').value = total.toFixed(2) + ' SEK';
        }

        // Update portfolio display
        async function updatePortfolio() {
            const portfolioData = await fetchPortfolio();
            
            if (!portfolioData) {
                console.error('Failed to fetch portfolio');
                return;
            }
            
            portfolio = {
                cash: portfolioData.cash,
                holdings: portfolioData.holdings,
                total_value: portfolioData.total_value
            };
            
            document.getElementById('cashBalance').textContent = portfolio.cash.toFixed(2) + ' SEK';
            document.getElementById('portfolioValue').textContent = portfolio.total_value.toFixed(2) + ' SEK';
            
            const pnl = portfolio.total_value - 10000;
            const pnlEl = document.getElementById('profitLoss');
            pnlEl.textContent = (pnl >= 0 ? '+' : '') + pnl.toFixed(2) + ' SEK';

            // Update holdings list with detailed info and sell buttons
            const holdingsList = document.getElementById('holdingsList');
            if (Object.keys(portfolio.holdings).length === 0) {
                holdingsList.innerHTML = '<div style="color: var(--text-secondary); font-size: 12px; text-align: center; padding: 20px;">No holdings yet</div>';
            } else {
                const holdingsDetailed = portfolioData.holdings_detailed || {};
                holdingsList.innerHTML = Object.entries(portfolio.holdings)
                    .map(([symbol, qty]) => {
                        const detail = holdingsDetailed[symbol] || {};
                        const value = detail.value || 0;
                        const currentPrice = detail.current_price || 0;
                        
                        return `
                            <div class="holding-item">
                                <div class="holding-info">
                                    <div class="holding-symbol">${symbol}</div>
                                    <div class="holding-qty">${qty.toFixed(4)} shares</div>
                                    ${currentPrice > 0 ? `<div class="holding-price">@ ${currentPrice.toFixed(2)} SEK</div>` : ''}
                                    ${value > 0 ? `<div class="holding-value">${value.toFixed(2)} SEK</div>` : ''}
                                </div>
                                <div class="holding-actions">
                                    <button class="quick-trade-btn partial-sell" onclick="loadPositionToSell('${symbol}', ${qty})" title="Sell partial amount">
                                        Partial
                                    </button>
                                    <button class="quick-sell-btn" onclick="quickSell('${symbol}', ${qty})" title="Sell all shares">
                                        Sell All
                                    </button>
                                </div>
                            </div>
                        `;
                    }).join('');
            }
        }

        // Load position to sell panel (partial sell)
        function loadPositionToSell(ticker, maxQuantity) {
            // Switch to that ticker's chart
            currentSymbol = ticker;
            
            // Update active symbol in sidebar
            document.querySelectorAll('.symbol-item').forEach(item => {
                item.classList.toggle('active', item.dataset.symbol === ticker);
            });
            
            // Update chart
            updateChart(currentSymbol, currentPeriod, currentInterval);
            
            // Set quantity to half of holdings (user can adjust)
            const suggestedQty = (maxQuantity / 2).toFixed(4);
            document.getElementById('quantityInput').value = suggestedQty;
            document.getElementById('quantityInput').focus();
            document.getElementById('quantityInput').select();
            
            updateEstimate();
            
            // Highlight the sell button
            const sellBtn = document.getElementById('sellBtn');
            sellBtn.style.animation = 'pulse 0.5s ease 2';
            setTimeout(() => {
                sellBtn.style.animation = '';
            }, 1000);
        }

        // Quick sell function for holdings
        async function quickSell(ticker, quantity) {
            // Switch to that ticker's chart
            currentSymbol = ticker;
            
            // Update active symbol in sidebar
            document.querySelectorAll('.symbol-item').forEach(item => {
                item.classList.toggle('active', item.dataset.symbol === ticker);
            });
            
            // Update chart
            await updateChart(currentSymbol, currentPeriod, currentInterval);
            
            // Set quantity in input
            document.getElementById('quantityInput').value = quantity.toFixed(4);
            updateEstimate();
            
            // Confirm sell
            const proceed = confirm(`Sell all ${quantity.toFixed(4)} shares of ${ticker}?`);
            if (proceed) {
                await executeTrade('sell');
            }
        }

        // Execute trade via API
        async function executeTrade(action) {
            const qty = parseFloat(document.getElementById('quantityInput').value);
            
            if (!qty || qty <= 0) {
                showNotification('Please enter a valid quantity', 'error');
                return;
            }

            const limitPrice = currentOrderType === 'limit'
                ? parseFloat(document.getElementById('limitPriceInput').value)
                : null;

            showLoading(true);

            try {
                const response = await fetch(`${API_BASE}/trade`, {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                    },
                    body: JSON.stringify({
                        action: action,
                        ticker: currentSymbol,
                        quantity: qty,
                        order_type: currentOrderType,
                        limit_price: limitPrice,
                    }),
                });

                const result = await response.json();

                if (!response.ok) {
                    throw new Error(result.error || 'Trade failed');
                }

                const tx = result.transaction;
                const actionText = action.toUpperCase();
                showNotification(
                    `${actionText}: ${tx.quantity} ${tx.ticker} @ ${tx.price.toFixed(2)} SEK`,
                    'success'
                );
                
                // Add marker to chart
                addTradeMarker(action, currentSymbol, tx.quantity, tx.price, tx.timestamp ? new Date(tx.timestamp).getTime() / 1000 : null);

                // Update portfolio display
                await updatePortfolio();
                
                // Reset quantity
                document.getElementById('quantityInput').value = '1';
                updateEstimate();

            } catch (error) {
                console.error('Trade error:', error);
                showNotification(error.message || 'Trade failed', 'error');
            } finally {
                showLoading(false);
            }
        }

        // Event Listeners
        document.addEventListener('DOMContentLoaded', () => {
            initChart();
            updateChart(currentSymbol, currentPeriod, currentInterval);
            updatePortfolio();

            // Symbol selection
            document.querySelectorAll('.symbol-item').forEach(item => {
                item.addEventListener('click', (e) => {
                    document.querySelectorAll('.symbol-item').forEach(i => i.classList.remove('active'));
                    item.classList.add('active');
                    
                    currentSymbol = item.dataset.symbol;
                    updateChart(currentSymbol, currentPeriod, currentInterval);
                });
            });

            // Timeframe selection
            document.querySelectorAll('.timeframe-btn').forEach(btn => {
                btn.addEventListener('click', () => {
                    document.querySelectorAll('.timeframe-btn').forEach(b => b.classList.remove('active'));
                    btn.classList.add('active');
                    
                    currentPeriod = btn.dataset.period;
                    currentInterval = btn.dataset.interval;
                    updateChart(currentSymbol, currentPeriod, currentInterval);
                });
            });

            // Order type selection
            document.querySelectorAll('.order-type-btn').forEach(btn => {
                btn.addEventListener('click', () => {
                    document.querySelectorAll('.order-type-btn').forEach(b => b.classList.remove('active'));
                    btn.classList.add('active');
                    
                    currentOrderType = btn.dataset.type;
                    document.getElementById('limitPriceGroup').style.display = 
                        currentOrderType === 'limit' ? 'block' : 'none';
                    updateEstimate();
                });
            });

            // Quantity input
            document.getElementById('quantityInput').addEventListener('input', updateEstimate);
            document.getElementById('limitPriceInput').addEventListener('input', updateEstimate);

            // Trade buttons
            document.getElementById('buyBtn').addEventListener('click', () => executeTrade('buy'));
            document.getElementById('sellBtn').addEventListener('click', () => executeTrade('sell'));
            
            // Stop loss buttons
            document.getElementById('setStopLossBtn').addEventListener('click', setStopLoss);
            document.getElementById('clearStopLossBtn').addEventListener('click', clearStopLoss);
            
            // Take profit buttons
            document.getElementById('setTakeProfitBtn').addEventListener('click', setTakeProfit);
            document.getElementById('clearTakeProfitBtn').addEventListener('click', clearTakeProfit);
            
            // Fixed scale button
            document.getElementById('fixedScaleBtn').addEventListener('click', fixedScale);
            
            // Auto-suggest stop loss (5% below current price)
            document.getElementById('stopLossInput').addEventListener('focus', () => {
                const currentInput = document.getElementById('stopLossInput').value;
                if (!currentInput && currentPrice > 0) {
                    const suggestedStop = currentPrice * 0.95; // 5% below
                    document.getElementById('stopLossHint').textContent = `(Suggested: ${suggestedStop.toFixed(2)})`;
                }
            });
            
            // Auto-suggest take profit (5% above current price)
            document.getElementById('takeProfitInput').addEventListener('focus', () => {
                const currentInput = document.getElementById('takeProfitInput').value;
                if (!currentInput && currentPrice > 0) {
                    const suggestedTarget = currentPrice * 1.05; // 5% above
                    document.getElementById('takeProfitHint').textContent = `(Suggested: ${suggestedTarget.toFixed(2)})`;
                }
            });
        });