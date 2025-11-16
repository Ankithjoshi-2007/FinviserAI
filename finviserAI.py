import os
import google.generativeai as genai
import json
from dotenv import load_dotenv
from database_usa import get_company_database as get_usa_db
from database_europe import get_company_database as get_eu_db
from database_india import get_company_database as get_india_db

load_dotenv()

API_KEY = os.getenv("GEMINI_API_KEY")

if not API_KEY:
    print("Error: GEMINI_API_KEY environment variable not set.")
    print("Please set it in your environment or create a .env file with the key.")
    exit()

genai.configure(api_key=API_KEY)

def get_user_preferences():
    """Gathers investment preferences from the user."""
    print("--- Personal Finance Agent ---")
    print("Please provide your investment preferences.")

    region = ""
    valid_regions = ["USA", "INDIA", "EU"]
    while region not in valid_regions:
        region = input("Choose a region for investment (USA, India, EU): ").upper()
        if region not in valid_regions:
            print("Invalid region. Please choose from USA, India, or EU.")

    risk_appetite = input("What is your risk appetite? (e.g., Low, Medium, High): ")
    investment_horizon = input("What is your investment horizon? (e.g., Short-term, Long-term): ")
    preferred_sectors = input("Any preferred sectors? (e.g., Technology, Healthcare, Finance, or leave blank): ")
    
    salary = input("What is your annual salary in USD? (e.g., $50,000 or leave blank if not applicable): ")
    loan = input("Do you have any outstanding loans? If yes, please specify amount and type in USD (e.g., $25,000 student loan, or leave blank if none): ")
    monthly_expense = input("What is your approximate monthly expense in USD? (e.g., $3,000 or leave blank if not applicable): ")

    return {
        "region": region,
        "risk_appetite": risk_appetite,
        "investment_horizon": investment_horizon,
        "preferred_sectors": preferred_sectors,
        "salary": salary,
        "loan": loan,
        "monthly_expense": monthly_expense
    }

def generate_recommendations(preferences, database):
    """
    Uses the Gemini API to generate stock recommendations based on user preferences
    and a company database.
    """
    print("\nAnalyzing market data and generating recommendations... This may take a moment.")

    prompt = f"""
    You are a sophisticated personal finance agent. Your task is to recommend stocks
    based on the user's preferences and your analysis of real-time financial data.

    **Company Database:**
    {json.dumps(database, indent=2)}

    **User Preferences:**
    - Risk Appetite: {preferences['risk_appetite']}
    - Investment Horizon: {preferences['investment_horizon']}
    - Preferred Sectors: {preferences['preferred_sectors'] or 'Any'}
    - Annual Salary: {preferences['salary'] or 'Not specified'}
    - Outstanding Loans: {preferences['loan'] or 'None'}
    - Monthly Expenses: {preferences['monthly_expense'] or 'Not specified'}

    **Instructions:**
    1.  Analyze the provided company database.
    2.  For your analysis, consult real-time financial news sources (like Google Finance, Yahoo Finance)
        and gauge public and market sentiment from social media (like X and Reddit).
    3.  Consider the user's financial profile (salary, loans, monthly expenses) when making recommendations.
        Factor in their financial capacity, debt obligations, and cash flow when suggesting investment amounts
        and risk levels.
    4.  Based on the user's preferences, financial situation, and your analysis, recommend exactly THREE companies from each category
        (Small Cap, Mid Cap, and Large Cap).
    5.  For each recommendation, provide a concise, human-readable justification (2-3 sentences) explaining
        why it's a good fit, citing the market sentiment, recent news or performance, and how it aligns with
        their financial capacity and risk tolerance.

    **Response Format:**
    Provide the output in a clear, well-structured format. For example:

    ***

    ### Investment Recommendations

    Here are your personalized stock recommendations based on your preferences:

    **Small Cap Recommendations**
    - **[Company Name (Ticker)]**: [Justification based on your analysis]
    - **[Company Name (Ticker)]**: [Justification based on your analysis]

    **Mid Cap Recommendations**
    - **[Company Name (Ticker)]**: [Justification based on your analysis]
    - **[Company Name (Ticker)]**: [Justification based on your analysis]

    **Large Cap Recommendations**
    - **[Company Name (Ticker)]**: [Justification based on your analysis]
    - **[Company Name (Ticker)]**: [Justification based on your analysis]

    **Disclaimer**: This is not financial advice. Please consult with a professional financial advisor
    before making any investment decisions.
    """

    try:
        model = genai.GenerativeModel('gemini-pro-latest')
        response = model.generate_content(prompt)
        return response.text
    except Exception as e:
        return f"An error occurred while communicating with the Gemini API: {e}"

def main():
    """Main function to run the personal finance agent."""
    user_preferences = get_user_preferences()
    
    print(f"\nFetching real-time market data for {user_preferences['region']}...")
    region = user_preferences['region']
    if region == "USA":
        company_database = get_usa_db()
    elif region == "EU":
        company_database = get_eu_db()
    elif region == "INDIA":
        company_database = get_india_db()
    
    
    recommendations = generate_recommendations(user_preferences, company_database)
    print("\n" + "="*50)
    print(recommendations)
    print("="*50)


if __name__ == "__main__":
    main()
