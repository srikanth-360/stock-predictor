# ============================================================================
# STOCK PREDICTION WEB APPLICATION - MAIN BACKEND
# Flask Application with LSTM Model Integration
# ============================================================================

from flask import Flask, render_template, request, jsonify
from datetime import datetime, timedelta
import yfinance as yf
import pandas as pd
import numpy as np
from sklearn.preprocessing import MinMaxScaler
from tensorflow.keras.models import Sequential
from tensorflow.keras.layers import LSTM, Dense, Dropout, Bidirectional
from tensorflow.keras.callbacks import EarlyStopping
import warnings
import io
import base64
import matplotlib
matplotlib.use('Agg')  # Use non-interactive backend
import matplotlib.pyplot as plt
import plotly.graph_objs as go
import plotly.express as px
from plotly.subplots import make_subplots
import json

warnings.filterwarnings('ignore')

app = Flask(__name__)
app.config['JSON_SORT_KEYS'] = False

# ============================================================================
# UTILITY FUNCTIONS
# ============================================================================

def create_features(df):
    """Create comprehensive technical indicators"""
    data = df.copy()
    
    # Price-based features
    data['Returns'] = data['Close'].pct_change()
    data['High-Low'] = data['High'] - data['Low']
    data['Close-Open'] = data['Close'] - data['Open']
    
    # Moving Averages
    for window in [5, 10, 20, 50, 100]:
        data[f'MA_{window}'] = data['Close'].rolling(window=window).mean()
        data[f'MA_{window}_diff'] = data['Close'] - data[f'MA_{window}']
    
    # Exponential Moving Averages
    for window in [12, 26]:
        data[f'EMA_{window}'] = data['Close'].ewm(span=window, adjust=False).mean()
    
    # MACD
    data['MACD'] = data['EMA_12'] - data['EMA_26']
    data['MACD_Signal'] = data['MACD'].ewm(span=9, adjust=False).mean()
    data['MACD_Hist'] = data['MACD'] - data['MACD_Signal']
    
    # RSI (Relative Strength Index)
    delta = data['Close'].diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
    rs = gain / loss
    data['RSI'] = 100 - (100 / (1 + rs))
    
    # Bollinger Bands
    data['BB_middle'] = data['Close'].rolling(window=20).mean()
    bb_std = data['Close'].rolling(window=20).std()
    data['BB_upper'] = data['BB_middle'] + (bb_std * 2)
    data['BB_lower'] = data['BB_middle'] - (bb_std * 2)
    data['BB_width'] = data['BB_upper'] - data['BB_lower']
    
    # Momentum
    data['Momentum'] = data['Close'] - data['Close'].shift(10)
    
    # Volume features
    data['Volume_MA_5'] = data['Volume'].rolling(window=5).mean()
    data['Volume_MA_20'] = data['Volume'].rolling(window=20).mean()
    data['Volume_Ratio'] = data['Volume'] / data['Volume_MA_20']
    
    # Volatility (Standard Deviation)
    data['Volatility'] = data['Returns'].rolling(window=20).std()
    
    # Lagged features
    for lag in [1, 2, 3, 5]:
        data[f'Close_Lag_{lag}'] = data['Close'].shift(lag)
        data[f'Volume_Lag_{lag}'] = data['Volume'].shift(lag)
    
    return data


def fetch_stock_data(ticker, days=365):
    """Fetch stock data with error handling"""
    try:
        end_date = datetime.now()
        start_date = end_date - timedelta(days=days)
        
        # Try different ticker formats
        ticker_formats = [ticker, f"{ticker}.NS", f"{ticker}.BO"]
        
        for t in ticker_formats:
            try:
                df = yf.download(t, start=start_date, end=end_date, progress=False)
                if not df.empty:
                    if isinstance(df.columns, pd.MultiIndex):
                        df.columns = df.columns.get_level_values(0)
                    return df, t
            except:
                continue
        
        return None, None
    except Exception as e:
        print(f"Error fetching data: {e}")
        return None, None


def get_current_price(ticker):
    """Get TODAY's current/intraday price (not yesterday's close)"""
    try:
        ticker_obj = yf.Ticker(ticker)
        
        # Method 1: Try fast_info for current market price
        try:
            current = ticker_obj.fast_info.get('lastPrice')
            if current and current > 0:
                print(f"✓ Got current price from fast_info: ₹{current:.2f}")
                return float(current)
        except:
            pass
        
        # Method 2: Try regular info
        try:
            info = ticker_obj.info
            price_fields = ['currentPrice', 'regularMarketPrice', 'bid', 'ask']
            for field in price_fields:
                if field in info and info[field] is not None and info[field] > 0:
                    print(f"✓ Got current price from info.{field}: ₹{info[field]:.2f}")
                    return float(info[field])
        except:
            pass
        
        # Method 3: Get today's intraday data (most reliable)
        try:
            # Get today's data with 1-minute intervals
            today_data = ticker_obj.history(period='1d', interval='1m')
            if not today_data.empty:
                latest_price = float(today_data['Close'].iloc[-1])
                print(f"✓ Got current price from today's intraday data: ₹{latest_price:.2f}")
                return latest_price
        except:
            pass
        
        # Method 4: Get last 5 days and use most recent
        try:
            hist = ticker_obj.history(period='5d')
            if not hist.empty:
                latest = float(hist['Close'].iloc[-1])
                print(f"⚠ Using last available close: ₹{latest:.2f}")
                return latest
        except:
            pass
        
        return None
    except Exception as e:
        print(f"Error getting current price: {e}")
        return None


def build_and_train_model(X_train, y_train):
    """Build and train enhanced LSTM model"""
    model = Sequential([
        LSTM(50, return_sequences=True, input_shape=(X_train.shape[1], X_train.shape[2])),
        Dropout(0.2),
        
        # Removed middle layer, kept only 2 LSTM layers
        LSTM(30, return_sequences=False),  # Reduced from 80
        Dropout(0.2),
        
        # Simplified dense layers
        Dense(25, activation='relu'),
        Dense(1)
        
        """Bidirectional(LSTM(50, return_sequences=True, input_shape=(X_train.shape[1], X_train.shape[2]))),
        Dropout(0.3),
        Bidirectional(LSTM(80, return_sequences=True)),
        Dropout(0.3),
        LSTM(60, return_sequences=False),
        Dropout(0.2),
        Dense(50, activation='relu'),
        Dense(25, activation='relu'),
        Dense(1)"""
    ])
    
    model.compile(optimizer='adam', loss='mean_squared_error', metrics=['mae'])
    
    early_stop = EarlyStopping(monitor='loss', patience=3, restore_best_weights=True) #patience=5
    
    history = model.fit(
        X_train, y_train,
        batch_size=32,
        epochs=30,
        validation_split=0.1,
        callbacks=[early_stop],
        verbose=0
    )
    
    return model, history


def generate_prediction_reasoning(df_features, predicted_price, current_price):
    """Generate AI reasoning for the prediction"""
    reasoning = []
    
    # Price change analysis
    price_change = predicted_price - current_price
    price_change_pct = (price_change / current_price) * 100
    
    if price_change > 0:
        reasoning.append(f"📈 **Bullish Signal**: The model predicts a price increase of ₹{abs(price_change):.2f} ({price_change_pct:+.2f}%)")
    else:
        reasoning.append(f"📉 **Bearish Signal**: The model predicts a price decrease of ₹{abs(price_change):.2f} ({price_change_pct:+.2f}%)")
    
    # RSI Analysis
    rsi = df_features['RSI'].iloc[-1]
    if rsi > 70:
        reasoning.append(f"⚠️ **RSI ({rsi:.1f})**: Stock is overbought, potential correction expected")
    elif rsi < 30:
        reasoning.append(f"✅ **RSI ({rsi:.1f})**: Stock is oversold, potential bounce expected")
    else:
        reasoning.append(f"➡️ **RSI ({rsi:.1f})**: Stock is in neutral territory")
    
    # Moving Average Analysis
    ma_20 = df_features['MA_20'].iloc[-1]
    ma_50 = df_features['MA_50'].iloc[-1]
    
    if current_price > ma_20 > ma_50:
        reasoning.append(f"✅ **Moving Averages**: Price is above MA20 (₹{ma_20:.2f}) and MA50 (₹{ma_50:.2f}) - Strong uptrend")
    elif current_price < ma_20 < ma_50:
        reasoning.append(f"⚠️ **Moving Averages**: Price is below MA20 (₹{ma_20:.2f}) and MA50 (₹{ma_50:.2f}) - Downtrend")
    else:
        reasoning.append(f"➡️ **Moving Averages**: Mixed signals - MA20: ₹{ma_20:.2f}, MA50: ₹{ma_50:.2f}")
    
    # MACD Analysis
    macd = df_features['MACD'].iloc[-1]
    macd_signal = df_features['MACD_Signal'].iloc[-1]
    
    if macd > macd_signal:
        reasoning.append(f"✅ **MACD**: Bullish crossover detected (MACD: {macd:.2f} > Signal: {macd_signal:.2f})")
    else:
        reasoning.append(f"⚠️ **MACD**: Bearish signal (MACD: {macd:.2f} < Signal: {macd_signal:.2f})")
    
    # Volatility Analysis
    volatility = df_features['Volatility'].iloc[-1] * 100
    reasoning.append(f"📊 **Volatility**: {volatility:.2f}% - {'High' if volatility > 2 else 'Moderate' if volatility > 1 else 'Low'} market volatility")
    
    # Volume Analysis
    volume_ratio = df_features['Volume_Ratio'].iloc[-1]
    if volume_ratio > 1.5:
        reasoning.append(f"📈 **Volume**: High volume ({volume_ratio:.1f}x average) - Strong interest")
    elif volume_ratio < 0.7:
        reasoning.append(f"📉 **Volume**: Low volume ({volume_ratio:.1f}x average) - Weak interest")
    else:
        reasoning.append(f"➡️ **Volume**: Normal trading volume ({volume_ratio:.1f}x average)")
    
    # Bollinger Bands
    bb_upper = df_features['BB_upper'].iloc[-1]
    bb_lower = df_features['BB_lower'].iloc[-1]
    
    if current_price > bb_upper:
        reasoning.append(f"⚠️ **Bollinger Bands**: Price above upper band (₹{bb_upper:.2f}) - Potential reversal")
    elif current_price < bb_lower:
        reasoning.append(f"✅ **Bollinger Bands**: Price below lower band (₹{bb_lower:.2f}) - Potential bounce")
    else:
        reasoning.append(f"➡️ **Bollinger Bands**: Price within bands (₹{bb_lower:.2f} - ₹{bb_upper:.2f})")
    
    return reasoning


# ============================================================================
# ROUTES
# ============================================================================

@app.route('/')
def index():
    """Render main page"""
    return render_template('index.html')


@app.route('/predict', methods=['POST'])
def predict():
    """Main prediction endpoint"""
    try:
        data = request.get_json()
        ticker = data.get('ticker', 'RELIANCE').upper().strip()
        
        if not ticker:
            return jsonify({'error': 'Please enter a valid ticker symbol'}), 400
        
        # Fetch stock data
        print(f"Fetching data for {ticker}...")
        df, used_ticker = fetch_stock_data(ticker)
        
        if df is None or df.empty:
            return jsonify({'error': f'Could not fetch data for {ticker}. Please check the ticker symbol.'}), 404
        
        # Get company info
        try:
            ticker_obj = yf.Ticker(used_ticker)
            company_name = ticker_obj.info.get('longName', ticker)
        except:
            company_name = ticker
        
        # Create features
        df_features = create_features(df)
        df_features = df_features.dropna()
        
        # Define target
        df_features['target'] = df_features['Close'].shift(-1)
        df_features = df_features.dropna()
        
        # Prepare data for LSTM
        feature_columns = [col for col in df_features.columns 
                          if col not in ['target', 'Open', 'High', 'Low', 'Close', 'Adj Close', 'Volume']]
        
        target = df_features['target'].values
        features = df_features[feature_columns].values
        
        # Scale data
        scaler_features = MinMaxScaler(feature_range=(0, 1))
        scaled_features = scaler_features.fit_transform(features)
        
        scaler_target = MinMaxScaler(feature_range=(0, 1))
        scaled_target = scaler_target.fit_transform(target.reshape(-1, 1))
        
        # Create sequences
        sequence_length = 30
        X, y = [], []
        
        for i in range(sequence_length, len(scaled_features)):
            X.append(scaled_features[i-sequence_length:i])
            y.append(scaled_target[i, 0])
        
        X, y = np.array(X), np.array(y)
        
        # Split data
        split_index = int(len(X) * 0.8)
        X_train, X_test = X[:split_index], X[split_index:]
        y_train, y_test = y[:split_index], y[split_index:]
        
        # Train model
        print("Training model...")
        model, history = build_and_train_model(X_train, y_train)
        
        # Make predictions on test set
        predictions = model.predict(X_test, verbose=0)
        predictions_actual = scaler_target.inverse_transform(predictions)
        y_test_actual = scaler_target.inverse_transform(y_test.reshape(-1, 1))
        
        # Calculate metrics
        mape = np.mean(np.abs((y_test_actual - predictions_actual) / y_test_actual)) * 100
        accuracy = 100 - mape
        rmse = np.sqrt(np.mean((predictions_actual - y_test_actual) ** 2))
        mae = np.mean(np.abs(predictions_actual - y_test_actual))
        
        # Predict tomorrow's price
        last_sequence = scaled_features[-sequence_length:]
        last_sequence = last_sequence.reshape(1, sequence_length, X_train.shape[2])
        
        tomorrow_scaled = model.predict(last_sequence, verbose=0)
        tomorrow_price = scaler_target.inverse_transform(tomorrow_scaled)[0][0]
        
        # Get current price (real-time or latest available)
        current_price = get_current_price(used_ticker)
        is_today_price = True
        
        # Fallback to historical data if real-time fetch fails
        if current_price is None:
            current_price = df_features['Close'].iloc[-1]
            is_today_price = False
            print(f"⚠ Using historical closing price: {current_price}")
        else:
            print(f"✓ Using current/intraday price: {current_price}")
        
        price_change = tomorrow_price - current_price
        price_change_percent = (price_change / current_price) * 100
        
        # Generate reasoning
        reasoning = generate_prediction_reasoning(df_features, tomorrow_price, current_price)
        
        # Prepare response
        response = {
            'ticker': used_ticker,
            'company_name': company_name,
            'current_price': float(current_price),
            'price_timestamp': datetime.now().strftime('%Y-%m-%d %I:%M:%S %p'),
            'is_today_price': is_today_price,
            'predicted_price': float(tomorrow_price),
            'price_change': float(price_change),
            'price_change_percent': float(price_change_percent),
            'prediction_date': (datetime.now() + timedelta(days=1)).strftime('%Y-%m-%d'),
            'accuracy': float(accuracy),
            'mape': float(mape),
            'rmse': float(rmse),
            'mae': float(mae),
            'reasoning': reasoning,
            'signal': 'BULLISH' if price_change > 0 else 'BEARISH' if price_change < 0 else 'NEUTRAL',
            'historical_data': {
                'dates': df.index[-60:].strftime('%Y-%m-%d').tolist(),
                'close': df['Close'].iloc[-60:].tolist(),
                'high': df['High'].iloc[-60:].tolist(),
                'low': df['Low'].iloc[-60:].tolist(),
                'open': df['Open'].iloc[-60:].tolist(),
                'volume': df['Volume'].iloc[-60:].tolist()
            },
            'technical_indicators': {
                'rsi': float(df_features['RSI'].iloc[-1]),
                'macd': float(df_features['MACD'].iloc[-1]),
                'macd_signal': float(df_features['MACD_Signal'].iloc[-1]),
                'ma_20': float(df_features['MA_20'].iloc[-1]),
                'ma_50': float(df_features['MA_50'].iloc[-1]),
                'bb_upper': float(df_features['BB_upper'].iloc[-1]),
                'bb_lower': float(df_features['BB_lower'].iloc[-1]),
                'volatility': float(df_features['Volatility'].iloc[-1] * 100)
            },
            'predictions_vs_actual': {
                'predicted': predictions_actual.flatten()[-30:].tolist(),
                'actual': y_test_actual.flatten()[-30:].tolist()
            }
        }
        
        return jsonify(response)
        
    except Exception as e:
        print(f"Error in prediction: {str(e)}")
        import traceback
        traceback.print_exc()
        return jsonify({'error': f'An error occurred: {str(e)}'}), 500


@app.route('/search/<ticker>')
def search_ticker(ticker):
    """Search for ticker information"""
    try:
        ticker_obj = yf.Ticker(ticker)
        info = ticker_obj.info
        
        return jsonify({
            'symbol': ticker,
            'name': info.get('longName', ticker),
            'sector': info.get('sector', 'N/A'),
            'industry': info.get('industry', 'N/A'),
            'exchange': info.get('exchange', 'N/A')
        })
    except:
        return jsonify({'error': 'Ticker not found'}), 404


if __name__ == '__main__':
    print("\n" + "="*70)
    print("🚀 STOCK PREDICTION WEB APPLICATION")
    print("="*70)
    print("\n📊 Starting Flask server...")
    print("🌐 Open your browser and go to: http://localhost:5000")
    print("="*70 + "\n")

    app.run(debug=True, host='0.0.0.0', port=5000)
