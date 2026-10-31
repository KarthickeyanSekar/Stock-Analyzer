"""Synthetic NIFTY 50 universe: real public symbols and sectors, made-up prices.

The constituent list is a representative sample of NIFTY 50 names (index membership
changes over time); it is used only to make the POC look realistic.
"""

from datetime import date

# (symbol, company name, sector)
NIFTY50: tuple[tuple[str, str, str], ...] = (
    ("ADANIENT", "Adani Enterprises", "Metals & Mining"),
    ("ADANIPORTS", "Adani Ports and SEZ", "Services"),
    ("APOLLOHOSP", "Apollo Hospitals", "Healthcare"),
    ("ASIANPAINT", "Asian Paints", "Consumer Durables"),
    ("AXISBANK", "Axis Bank", "Financial Services"),
    ("BAJAJ-AUTO", "Bajaj Auto", "Automobile"),
    ("BAJFINANCE", "Bajaj Finance", "Financial Services"),
    ("BAJAJFINSV", "Bajaj Finserv", "Financial Services"),
    ("BEL", "Bharat Electronics", "Capital Goods"),
    ("BHARTIARTL", "Bharti Airtel", "Telecommunication"),
    ("CIPLA", "Cipla", "Healthcare"),
    ("COALINDIA", "Coal India", "Oil Gas & Fuels"),
    ("DRREDDY", "Dr. Reddy's Laboratories", "Healthcare"),
    ("EICHERMOT", "Eicher Motors", "Automobile"),
    ("ETERNAL", "Eternal", "Consumer Services"),
    ("GRASIM", "Grasim Industries", "Construction Materials"),
    ("HCLTECH", "HCL Technologies", "Information Technology"),
    ("HDFCBANK", "HDFC Bank", "Financial Services"),
    ("HDFCLIFE", "HDFC Life Insurance", "Financial Services"),
    ("HEROMOTOCO", "Hero MotoCorp", "Automobile"),
    ("HINDALCO", "Hindalco Industries", "Metals & Mining"),
    ("HINDUNILVR", "Hindustan Unilever", "FMCG"),
    ("ICICIBANK", "ICICI Bank", "Financial Services"),
    ("INDUSINDBK", "IndusInd Bank", "Financial Services"),
    ("INFY", "Infosys", "Information Technology"),
    ("ITC", "ITC", "FMCG"),
    ("JIOFIN", "Jio Financial Services", "Financial Services"),
    ("JSWSTEEL", "JSW Steel", "Metals & Mining"),
    ("KOTAKBANK", "Kotak Mahindra Bank", "Financial Services"),
    ("LT", "Larsen & Toubro", "Construction"),
    ("M&M", "Mahindra & Mahindra", "Automobile"),
    ("MARUTI", "Maruti Suzuki India", "Automobile"),
    ("NESTLEIND", "Nestle India", "FMCG"),
    ("NTPC", "NTPC", "Power"),
    ("ONGC", "Oil & Natural Gas Corporation", "Oil Gas & Fuels"),
    ("POWERGRID", "Power Grid Corporation of India", "Power"),
    ("RELIANCE", "Reliance Industries", "Oil Gas & Fuels"),
    ("SBILIFE", "SBI Life Insurance", "Financial Services"),
    ("SBIN", "State Bank of India", "Financial Services"),
    ("SHRIRAMFIN", "Shriram Finance", "Financial Services"),
    ("SUNPHARMA", "Sun Pharmaceutical Industries", "Healthcare"),
    ("TATACONSUM", "Tata Consumer Products", "FMCG"),
    ("TATAMOTORS", "Tata Motors", "Automobile"),
    ("TATASTEEL", "Tata Steel", "Metals & Mining"),
    ("TCS", "Tata Consultancy Services", "Information Technology"),
    ("TECHM", "Tech Mahindra", "Information Technology"),
    ("TITAN", "Titan Company", "Consumer Durables"),
    ("TRENT", "Trent", "Consumer Services"),
    ("ULTRACEMCO", "UltraTech Cement", "Construction Materials"),
    ("WIPRO", "Wipro", "Information Technology"),
)

# (annual drift, annual volatility, beta to the market factor) by sector.
SECTOR_PROFILE: dict[str, tuple[float, float, float]] = {
    "Financial Services": (0.12, 0.26, 1.15),
    "Information Technology": (0.11, 0.24, 0.85),
    "Automobile": (0.13, 0.28, 1.05),
    "FMCG": (0.09, 0.18, 0.60),
    "Healthcare": (0.11, 0.23, 0.70),
    "Metals & Mining": (0.10, 0.36, 1.35),
    "Oil Gas & Fuels": (0.08, 0.27, 1.00),
    "Power": (0.12, 0.25, 0.95),
    "Capital Goods": (0.16, 0.30, 1.10),
    "Construction": (0.13, 0.26, 1.05),
    "Construction Materials": (0.10, 0.25, 0.95),
    "Consumer Durables": (0.10, 0.24, 0.85),
    "Consumer Services": (0.18, 0.38, 1.20),
    "Services": (0.12, 0.32, 1.20),
    "Telecommunication": (0.14, 0.24, 0.80),
}

# Sample NSE trading holidays (fixed national holidays); a real provider supplies the full list.
SAMPLE_HOLIDAYS: frozenset[date] = frozenset(
    date(year, month, day)
    for year in range(2021, 2028)
    for month, day in ((1, 26), (5, 1), (8, 15), (10, 2), (12, 25))
)

# Synthetic splits: (symbol, ex-date, ratio new shares per old share).
SAMPLE_SPLITS: tuple[tuple[str, date, int], ...] = (
    ("BAJFINANCE", date(2025, 6, 16), 2),
    ("TITAN", date(2024, 3, 11), 5),
)
