import pandas as pd
import numpy as np
import yfinance as yf
from typing import Dict, List, Any




USD_PER_MILLION = 1_000_000  
USD_PER_BILLION = 1_000_000_000 


INR_TO_USD_RATE = 1 / 83.0 


TIERS_USD_BILLION = {
    "Large Cap": 10.0,  
    "Mid Cap": 2.0,    
    "Small Cap": 0.0     
}

COMPANY_MAP = {
    'INFOSYS Ltd': 'INFY.NS',
    'Gujarat State Fertilizers & Chemicals Ltd': 'GSFC.NS',
    'Dixon Technologies': 'DIXON.NS',
    'Mankind Pharma Ltd': 'MANKIND.NS',
    'Arvind Ltd': 'ARVIND.NS',
    'TCS Ltd': 'TCS.NS'
}

company_names: List[str] = list(COMPANY_MAP.keys())
tickers: List[str] = list(COMPANY_MAP.values())


def classify_market_cap(market_cap_usd_billion: float) -> str:
    """
    Classifies a company based on its market capitalization in Billions USD.
    """
    # Classification now uses the USD Tiers
    if market_cap_usd_billion >= TIERS_USD_BILLION["Large Cap"]:
        return "Large Cap"
    elif market_cap_usd_billion >= TIERS_USD_BILLION["Mid Cap"]:
        return "Mid Cap"
    else:
        return "Small Cap"


def fetch_real_time_data(tickers: List[str]) -> List[Dict[str, Any]]:
    """
    Fetches real-time market cap data from Yahoo Finance (in INR) and converts it to USD.
    """
    data_list: List[Dict[str, Any]] = []
    
    for name, ticker in COMPANY_MAP.items():
        try:
            # Fetch Ticker data
            stock = yf.Ticker(ticker)
            info = stock.info
            
        
            market_cap_inr = info.get('marketCap')
            
            if market_cap_inr is not None and market_cap_inr > 0:
                
                
                market_cap_usd = market_cap_inr * INR_TO_USD_RATE
                
            
                market_cap_usd_billion = market_cap_usd / USD_PER_BILLION
                
                
                market_cap_usd_million = market_cap_usd / USD_PER_MILLION
                
                category = classify_market_cap(market_cap_usd_billion)

                data_list.append({
                    'Company Name': name,
                    'Ticker': ticker,
                    # Display value in USD Millions, formatted
                    'Current Market Value ($ Million)': f"${market_cap_usd_million:,.2f}", 
                    'Category': category
                })
            else:
                print(f"Warning: Market cap data not available for {name} ({ticker}).")
                data_list.append({
                    'Company Name': name,
                    'Ticker': ticker,
                    'Current Market Value ($ Million)': 'Data N/A',
                    'Category': 'N/A'
                })

        except Exception as e:
            print(f"Error fetching data for {name} ({ticker}): {e}")
            data_list.append({
                'Company Name': name,
                'Ticker': ticker,
                'Current Market Value ($ Million)': 'Error',
                'Category': 'Error'
            })
            
    return data_list


def get_stock_data_india(ticker: str, period: str = '1M') -> Dict[str, Any] | None:
    """
    Fetches stock data for a given Indian ticker from Yahoo Finance, including historical prices.
    """
    # Ensure the ticker is an NSE ticker if it's a known company
    yf_ticker = COMPANY_MAP.get(ticker.upper(), ticker.upper() + '.NS')
    stock = yf.Ticker(yf_ticker)

    try:
        info = stock.info
        if not info:
            return None

        
        yf_period_map = {
            '1D': '1d',
            '1W': '5d',
            '1M': '1mo',
            '3M': '3mo',
            '1Y': '1y',
        }
        yf_period = yf_period_map.get(period, '1mo')
        hist = stock.history(period=yf_period)

        
        history_prices = hist['Close'].tolist()

        current_price = info.get('currentPrice')
        previous_close = info.get('previousClose')
        
        if current_price is None or previous_close is None:
            if history_prices:
                current_price = history_prices[-1]
                if len(history_prices) > 1:
                    previous_close = history_prices[-2]
                else:
                    previous_close = current_price
            else:
                return None

        change = current_price - previous_close
        change_percent = (change / previous_close) * 100 if previous_close else 0

        # Format market cap and volume for display
        market_cap = info.get('marketCap')
        market_cap_display = f"₹{market_cap:,.0f}" if market_cap else 'N/A'
        volume = info.get('volume')
        volume_display = f"{volume:,.0f}" if volume else 'N/A'
        
        high_52w = info.get('fiftyTwoWeekHigh')
        low_52w = info.get('fiftyTwoWeekLow')

        return {
            'name': info.get('longName', ticker.upper()),
            'price': round(current_price, 2),
            'change': round(change, 2),
            'changePercent': round(change_percent, 2),
            'marketCap': market_cap_display,
            'volume': volume_display,
            'high52w': round(high_52w, 2) if high_52w else 'N/A',
            'low52w': round(low_52w, 2) if low_52w else 'N/A',
            'history': [round(p, 2) for p in history_prices] if history_prices else []
        }
    except Exception as e:
        print(f"Error fetching stock data for {ticker}: {e}")
        return None


def get_company_database():
    """
    Generates and returns a structured dictionary of company data for India,
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
                "market_cap": company["Current Market Value ($ Million)"]
            })
    return db

if __name__ == "__main__":
    live_data = fetch_real_time_data(list(COMPANY_MAP.values()))
    df = pd.DataFrame(live_data)
    
    large_cap_million = TIERS_USD_BILLION['Large Cap'] * 1000
    mid_cap_million = TIERS_USD_BILLION['Mid Cap'] * 1000
    
    print("Real-Time Market Capitalization Classification (Converted to USD):")
    print("-" * 100)
    print(df.to_markdown(index=False))
    print("-" * 100)
    print(f"Classification Tiers (in Millions USD):\nLarge Cap: > ${large_cap_million:,.0f} Million\nMid Cap: ${mid_cap_million:,.0f}-${large_cap_million:,.0f} Million\nSmall Cap: < ${mid_cap_million:,.0f} Million")
    print("\n*Data fetched live via yfinance in INR, converted to USD using a fixed exchange rate for demonstration.")