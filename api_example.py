"""
API Usage Example
=================
This file demonstrates how to use the stock predictor API programmatically.
"""

import requests
import json

# Base URL (make sure the Flask app is running)
BASE_URL = "http://localhost:5000"

def predict_stock(ticker):
    """
    Get stock prediction for a given ticker
    """
    url = f"{BASE_URL}/predict"
    
    payload = {
        "ticker": ticker
    }
    
    headers = {
        "Content-Type": "application/json"
    }
    
    try:
        print(f"\n{'='*70}")
        print(f"Fetching prediction for {ticker}...")
        print('='*70)
        
        response = requests.post(url, json=payload, headers=headers)
        
        if response.status_code == 200:
            data = response.json()
            
            print(f"\n🏢 Company: {data['company_name']}")
            print(f"📊 Ticker: {data['ticker']}")
            print(f"\n💰 Current Price: ₹{data['current_price']:.2f}")
            print(f"🔮 Predicted Price: ₹{data['predicted_price']:.2f}")
            print(f"📈 Change: {data['price_change']:+.2f} ({data['price_change_percent']:+.2f}%)")
            print(f"🎯 Signal: {data['signal']}")
            
            print(f"\n📊 Model Performance:")
            print(f"   • Accuracy: {data['accuracy']:.2f}%")
            print(f"   • MAPE: {data['mape']:.2f}%")
            print(f"   • RMSE: ₹{data['rmse']:.2f}")
            print(f"   • MAE: ₹{data['mae']:.2f}")
            
            print(f"\n🧠 Key Insights:")
            for i, reason in enumerate(data['reasoning'][:3], 1):
                print(f"   {i}. {reason}")
            
            print(f"\n✅ Prediction successful!")
            return data
        else:
            error_data = response.json()
            print(f"\n❌ Error: {error_data.get('error', 'Unknown error')}")
            return None
            
    except requests.exceptions.ConnectionError:
        print("\n❌ Error: Could not connect to the server.")
        print("Make sure the Flask app is running (python app.py)")
        return None
    except Exception as e:
        print(f"\n❌ Error: {str(e)}")
        return None


def search_ticker(ticker):
    """
    Search for ticker information
    """
    url = f"{BASE_URL}/search/{ticker}"
    
    try:
        response = requests.get(url)
        
        if response.status_code == 200:
            data = response.json()
            print(f"\n📋 Ticker Information:")
            print(f"   • Symbol: {data['symbol']}")
            print(f"   • Name: {data['name']}")
            print(f"   • Sector: {data['sector']}")
            print(f"   • Industry: {data['industry']}")
            print(f"   • Exchange: {data['exchange']}")
            return data
        else:
            print(f"\n❌ Ticker not found: {ticker}")
            return None
            
    except Exception as e:
        print(f"\n❌ Error: {str(e)}")
        return None


if __name__ == "__main__":
    print("""
╔══════════════════════════════════════════════════════════════════╗
║           STOCK PREDICTOR API - USAGE EXAMPLE                    ║
╚══════════════════════════════════════════════════════════════════╝
    """)
    
    # Example 1: Predict stock price
    print("\n[Example 1] Predicting RELIANCE stock...")
    reliance_data = predict_stock("RELIANCE")
    
    # Example 2: Predict another stock
    print("\n[Example 2] Predicting TCS stock...")
    tcs_data = predict_stock("TCS")
    
    # Example 3: Search ticker information
    print("\n[Example 3] Searching ticker information...")
    ticker_info = search_ticker("INFY")
    
    # Example 4: Save results to JSON
    if reliance_data:
        print("\n[Example 4] Saving results to file...")
        with open('prediction_results.json', 'w') as f:
            json.dump(reliance_data, f, indent=2)
        print("✅ Results saved to 'prediction_results.json'")
    
    print("\n" + "="*70)
    print("✨ Examples completed!")
    print("="*70 + "\n")