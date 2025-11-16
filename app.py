from flask import Flask, redirect, url_for, flash, session, render_template, request, jsonify
from flask_sqlalchemy import SQLAlchemy
import os
import requests
import json
from datetime import datetime, timedelta
from flask_login import LoginManager, login_required, UserMixin, current_user, login_user, logout_user
import database_india 
import database_europe 
import database_usa 
import random 
import finviserAI 
import yfinance as yf
app = Flask(__name__)
app.secret_key = "finviser"


instance_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'instance')
if not os.path.exists(instance_path):
    os.makedirs(instance_path)

app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///' + os.path.join(instance_path, 'users.sqlite3')
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

db = SQLAlchemy(app)

class User(db.Model, UserMixin):
    __tablename__ = "users"
    id = db.Column("id", db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(100), nullable=False, unique=True)
    password=db.Column(db.String(200), nullable=False)
  
    def __init__(self, name, email, password):
        self.name = name
        self.email = email
        self.password = password

login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

@app.route("/")
def home():
    return render_template("home.html")

@app.route("/dashboard")
def dashboard():
    company_data_categorized = {"Small Cap": [], "Mid Cap": [], "Large Cap": []}
    selected_region = session.get('selected_region', 'NA') # Default to NA

    if selected_region == 'INDIA':
        company_db = database_india.get_company_database()
        company_data_categorized["Small Cap"] = [{'name': c["name"], 'ticker': c["ticker"], 'market_cap': c["market_cap"]} for c in company_db["Small Cap"]]
        company_data_categorized["Mid Cap"] = [{'name': c["name"], 'ticker': c["ticker"], 'market_cap': c["market_cap"]} for c in company_db["Mid Cap"]]
        company_data_categorized["Large Cap"] = [{'name': c["name"], 'ticker': c["ticker"], 'market_cap': c["market_cap"]} for c in company_db["Large Cap"]]
    elif selected_region == 'EUROPE':
        company_db = database_europe.get_company_database()
        company_data_categorized["Small Cap"] = [{'name': c["name"], 'ticker': c["ticker"], 'market_cap': c["market_cap"]} for c in company_db["Small Cap"]]
        company_data_categorized["Mid Cap"] = [{'name': c["name"], 'ticker': c["ticker"], 'market_cap': c["market_cap"]} for c in company_db["Mid Cap"]]
        company_data_categorized["Large Cap"] = [{'name': c["name"], 'ticker': c["ticker"], 'market_cap': c["market_cap"]} for c in company_db["Large Cap"]]
    elif selected_region == 'NA':
        company_db = database_usa.get_company_database()
        company_data_categorized["Small Cap"] = [{'name': c["name"], 'ticker': c["ticker"], 'market_cap': c["market_cap"]} for c in company_db["Small Cap"]]
        company_data_categorized["Mid Cap"] = [{'name': c["name"], 'ticker': c["ticker"], 'market_cap': c["market_cap"]} for c in company_db["Mid Cap"]]
        company_data_categorized["Large Cap"] = [{'name': c["name"], 'ticker': c["ticker"], 'market_cap': c["market_cap"]} for c in company_db["Large Cap"]]
                
    return render_template("dashboard.html", company_data_categorized=company_data_categorized, selected_region=selected_region)

@app.route('/set_region', methods=['POST'])
def set_region():
    region = request.json.get('region')
    if region:
        session['selected_region'] = region
        return jsonify(success=True, selected_region=region)
    return jsonify(success=False, message='No region provided'), 400

@app.route("/api/ai_recommendations", methods=["POST"])
def get_ai_recommendations():
    if request.method == "POST":
        preferences = request.json
        region = preferences.get('region')

        company_database = {}
        if region == "USA":
            from database_usa import get_company_database
            company_database = get_company_database()
        elif region == "EU":
            from database_europe import get_company_database
            company_database = get_company_database()
        elif region == "INDIA":
            from database_india import get_company_database
            company_database = get_company_database()

        if not company_database:
            return jsonify(success=False, message="Could not retrieve company data for the selected region."), 400

        # Use the updated finviserAI.generate_recommendations
        recommendations = finviserAI.generate_recommendations(preferences, company_database)
        return jsonify(success=True, recommendations=recommendations)
    return jsonify(success=False, message="Invalid request method."), 400


@app.route("/api/stock/<ticker>")
def get_stock_data(ticker):
    period = request.args.get('period', '1M')
    ticker_upper = ticker.upper()

    # Special handling for TCS (India)
    if ticker_upper == 'TCS':
        # Try NSE:TCS first, fallback to BSE:TCS
        for tcs_ticker in ['TCS.NS', 'TCS.BO']:
            try:
                stock = yf.Ticker(tcs_ticker)
                info = stock.info
                hist = stock.history(period='1mo')
                price_inr = info.get('regularMarketPrice')
                previous_close_inr = info.get('regularMarketPreviousClose')
                change_inr = None
                change_percent = None
                if price_inr is not None and previous_close_inr is not None:
                    change_inr = price_inr - previous_close_inr
                    change_percent = (change_inr / previous_close_inr) * 100 if previous_close_inr != 0 else 0
                market_cap_inr = info.get('marketCap')
                volume = info.get('volume')
                high_52w_inr = info.get('fiftyTwoWeekHigh')
                low_52w_inr = info.get('fiftyTwoWeekLow')
                name = info.get('shortName', 'Tata Consultancy Services')
                currency = info.get('currency', 'INR')

                # Fetch INR to USD exchange rate
                try:
                    fx_resp = requests.get('https://api.exchangerate.host/latest?base=INR&symbols=USD', timeout=5)
                    fx_data = fx_resp.json()
                    inr_usd = fx_data['rates']['USD'] if 'rates' in fx_data and 'USD' in fx_data['rates'] else 0.012
                except Exception as fx_e:
                    print(f"Error fetching INR to USD rate: {fx_e}")
                    inr_usd = 0.012  # fallback

                # Convert all INR values to USD
                price = round(price_inr * inr_usd, 2) if price_inr else 0
                previous_close = round(previous_close_inr * inr_usd, 2) if previous_close_inr else 0
                change = round(change_inr * inr_usd, 2) if change_inr else 0
                market_cap = round(market_cap_inr * inr_usd, 2) if market_cap_inr else 0
                high_52w = round(high_52w_inr * inr_usd, 2) if high_52w_inr else 0
                low_52w = round(low_52w_inr * inr_usd, 2) if low_52w_inr else 0

                history_prices = hist['Close'].tolist() if 'Close' in hist else []
                history_prices_usd = [round(p * inr_usd, 2) for p in history_prices] if history_prices else ([price] * 30 if price else [])

                data = {
                    'name': name,
                    'price': price,
                    'change': change,
                    'changePercent': change_percent if change_percent else 0,
                    'marketCap': market_cap,
                    'volume': volume if volume else 0,
                    'high52w': high_52w,
                    'low52w': low_52w,
                    'history': history_prices_usd,
                    'currency': 'USD'
                }
                return jsonify(success=True, data=data)
            except Exception as e:
                print(f"Error fetching TCS data from {tcs_ticker}: {e}")
        return jsonify(success=False, message='Stock data not found for TCS.'), 404

    try:
        stock = yf.Ticker(ticker_upper)
        info = stock.info
        hist = stock.history(period='1mo')
        price = info.get('regularMarketPrice')
        previous_close = info.get('regularMarketPreviousClose')
        change = None
        change_percent = None
        if price is not None and previous_close is not None:
            change = price - previous_close
            change_percent = (change / previous_close) * 100 if previous_close != 0 else 0
        market_cap = info.get('marketCap')
        volume = info.get('volume')
        high_52w = info.get('fiftyTwoWeekHigh')
        low_52w = info.get('fiftyTwoWeekLow')
        name = info.get('shortName', ticker_upper)
        currency = info.get('currency', 'USD')

        # Prepare history for chart (close prices)
        history_prices = hist['Close'].tolist() if 'Close' in hist else []
        if not history_prices:
            history_prices = [price] * 30 if price else []

        data = {
            'name': name,
            'price': price if price else 0,
            'change': change if change else 0,
            'changePercent': change_percent if change_percent else 0,
            'marketCap': market_cap if market_cap else 0,
            'volume': volume if volume else 0,
            'high52w': high_52w if high_52w else 0,
            'low52w': low_52w if low_52w else 0,
            'history': history_prices,
            'currency': currency
        }
        return jsonify(success=True, data=data)
    except Exception as e:
        print(f"Error fetching real-time data: {e}")
        return jsonify(success=False, message='Stock data not found.'), 404
 


@app.route("/signup", methods=["GET", "POST"])
def signup():
    if request.method == "POST":
        name = request.form["nm"]
        email = request.form["email"]
        password = request.form["password"]
        if User.query.filter_by(email=email).first():
            flash("Email already registered. Please login.", "error")
            return render_template("home.html", show_login=True)
        new_user = User(name, email, password)
        db.session.add(new_user)
        db.session.commit()
        flash("Signup successful! Please login.", "success")
        return render_template("home.html", show_login=True)
    return redirect(url_for("home"))


@app.route('/login', methods=["POST", "GET"])
def login():
    if request.method == "POST":
        email = request.form["email"]
        password = request.form["password"]
        user = User.query.filter_by(email=email, password=password).first()
        if user:
            login_user(user)
            flash("Login successful!", "success")
            return redirect(url_for("home"))
        else:
            flash("Invalid credentials. Please try again.", "error")
            return render_template("home.html", show_login=True)
    return redirect(url_for("home"))

@app.route('/profile')
@login_required
def profile():
    return render_template('profile.html', current_user=current_user)

@app.route('/logout')
@login_required
def logout():
    logout_user()
    flash("You have been logged out.", "info")
    return redirect(url_for('home'))


@app.route('/market_data')
@login_required
def market_data():
    return render_template('market_data.html')

@app.route('/about')
def about():
    return render_template('about.html')


if __name__ == "__main__":
    with app.app_context():
        db.create_all()
    import os
    os.environ['WERKZEUG_DEBUG_PIN'] = 'off'
    app.run(debug=True, use_reloader=False)