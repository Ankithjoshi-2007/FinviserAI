import pandas as pd
import numpy as np
import yfinance as yf
from typing import Dict, List, Any


FX_RATES = {
    'EUR': 1.07,  
    'CHF': 1.10,  
    'USD': 1.00   
}

USD_PER_BILLION = 1_000_000_000
USD_PER_MILLION = 1_000_000


TIERS_USD_BILLION = {
    "Large Cap": 10.0, 
    "Mid Cap": 2.0,     
    "Small Cap": 0.0     
}


COMPANY_MAP = {
    'Aeva Technologies Inc': 'AEVA',
    'The Oncology Institute': 'TOI',
    'Mattel Inc': 'MAT',
    'Avis Budget Group Inc': 'CAR',
    'Apple Inc.': 'AAPL',
    'Microsoft Corp': 'MSFT',
    'Amazon.com Inc': 'AMZN',
    'Alphabet Inc. (Class A)': 'GOOGL',
    'Tesla Inc': 'TSLA',
    'NVIDIA Corp': 'NVDA',
    'JPMorgan Chase & Co.': 'JPM',
    
}

company_names: List[str] = list(COMPANY_MAP.keys())
tickers: List[str] = list(COMPANY_MAP.values())


def classify_market_cap(market_cap_usd_billion: float) -> str:
    """
    Classifies a company based on its market capitalization in Billions USD.
    """
    if market_cap_usd_billion >= TIERS_USD_BILLION["Large Cap"]:
        return "Large Cap"
    elif market_cap_usd_billion >= TIERS_USD_BILLION["Mid Cap"]:
        return "Mid Cap"
    else:
        return "Small Cap"


def fetch_real_time_data(tickers: List[str]) -> List[Dict[str, Any]]:
    """
    Fetches real-time market cap data from Yahoo Finance and converts it to USD.
    """
    data_list: List[Dict[str, Any]] = []
    
    for name, ticker in COMPANY_MAP.items():
        try:
            # Fetch Ticker data
            stock = yf.Ticker(ticker)
            info = stock.info
            
            market_cap_native = info.get('marketCap')
            native_currency = info.get('currency', 'USD') # Get native currency

            if market_cap_native is not None and market_cap_native > 0:
                
               
                rate = FX_RATES.get(native_currency, 1.00) 
                market_cap_usd = market_cap_native * rate
                
               
                market_cap_usd_billion = market_cap_usd / USD_PER_BILLION
                
                category = classify_market_cap(market_cap_usd_billion)

                data_list.append({
                    'Company Name': name,
                    'Ticker': ticker,
                    'Native Currency': native_currency,
                 
                    'Current Market Value ($ Billion)': f"${market_cap_usd_billion:,.2f}", 
                    'Category': category
                })
            else:
                print(f"Warning: Market cap data not available for {name} ({ticker}).")
                data_list.append({
                    'Company Name': name,
                    'Ticker': ticker,
                    'Native Currency': native_currency,
                    'Current Market Value ($ Billion)': 'Data N/A',
                    'Category': 'N/A'
                })

        except Exception as e:
            print(f"Error fetching data for {name} ({ticker}): {e}")
            data_list.append({
                'Company Name': name,
                'Ticker': ticker,
                'Native Currency': 'Error',
                'Current Market Value ($ Billion)': 'Error',
                'Category': 'Error'
            })
            
    return data_list


def get_company_database():
    """
    Generates and returns a structured dictionary of company data for USA,
    categorized by market cap.
    """
    tickers = list(COMPANY_MAP.values())
    all_companies = fetch_real_time_data(tickers)
    
    db = {"Large Cap": [], "Mid Cap": [], "Small Cap": []}
    for company in all_companies:
        category = company["Category"]
        if category in db:
            db[category].append({
                "name": company["Company Name"],
                "ticker": company["Ticker"],
                "market_cap": company["Current Market Value ($ Billion)"]
            })
    return db


def get_stock_data_usa(ticker: str, period: str = '1M') -> Dict[str, Any] | None:
    """
    Fetches stock data for a given USA ticker from Yahoo Finance, including historical prices.
    """
    stock = yf.Ticker(ticker.upper())

    try:
        info = stock.info
        if not info:
            return None

        # Get historical data based on period
        interval = '1d'
        if period == '1D':
            history = stock.history(period="1d", interval="5m") # Daily data, 5-minute intervals
        elif period == '1W':
            history = stock.history(period="7d", interval="1h") # Weekly data, 1-hour intervals
        elif period == '1M':
            history = stock.history(period="1mo", interval="1d") # Monthly data, 1-day intervals
        elif period == '3M':
            history = stock.history(period="3mo", interval="1d") # 3-Month data, 1-day intervals
        elif period == '1Y':
            history = stock.history(period="1y", interval="1wk") # 1-Year data, 1-week intervals
        else:
            history = stock.history(period="1mo", interval="1d") # Default to 1M

        historical_prices = history['Close'].dropna().tolist() if not history.empty else []

        current_price = info.get('regularMarketPrice')
        previous_close = info.get('previousClose')

        if current_price is None or previous_close is None:
            if historical_prices:
                current_price = historical_prices[-1]
                if len(historical_prices) > 1:
                    previous_close = historical_prices[-2]
                else:
                    previous_close = current_price
            else:
                return None

        change = current_price - previous_close
        change_percent = (change / previous_close) * 100 if previous_close != 0 else 0

        market_cap_native = info.get('marketCap', 0)
        native_currency = info.get('currency', 'USD')
        rate = FX_RATES.get(native_currency, 1.00)
        market_cap_usd = market_cap_native * rate
        market_cap_display = f"${market_cap_usd / USD_PER_BILLION:.1f}B" if market_cap_usd >= USD_PER_BILLION else f"${market_cap_usd / USD_PER_MILLION:.1f}M"

        volume = info.get('regularMarketVolume', 0)
        high_52w = info.get('fiftyTwoWeekHigh')
        low_52w = info.get('fiftyTwoWeekLow')

        return {
            'name': info.get('longName', ticker.upper()),
            'price': round(current_price, 2),
            'change': round(change, 2),
            'changePercent': round(change_percent, 2),
            'marketCap': market_cap_display,
            'volume': f"{volume:,}",
            'high52w': round(high_52w, 2) if high_52w else 'N/A',
            'low52w': round(low_52w, 2) if low_52w else 'N/A',
            'history': [round(p, 2) for p in historical_prices] if historical_prices else []
        }

    except Exception as e:
        print(f"Error fetching data for {ticker}: {e}")
        return None

if __name__ == "__main__":
    live_data = fetch_real_time_data(list(COMPANY_MAP.values()))
    df = pd.DataFrame(live_data)
    print("Real-Time Market Capitalization Classification (Converted to USD):")
    print("-" * 115)
    print(df.to_markdown(index=False))
    print("-" * 115)
    print(f"Classification Tiers:\nLarge Cap: > ${TIERS_USD_BILLION['Large Cap']:.1f} Billion\nMid Cap: ${TIERS_USD_BILLION['Mid Cap']:.1f}-${TIERS_USD_BILLION['Large Cap']:.1f} Billion\nSmall Cap: < ${TIERS_USD_BILLION['Mid Cap']:.1f} Billion")
    print("\n*Data fetched live via yfinance, converted to USD using fixed exchange rates for demonstration.")