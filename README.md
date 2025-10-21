# Finance — Stock Portfolio (Flask + SQLite)

A web application that lets users register, log in, quote stock prices, buy/sell shares, and view their transaction history.

Built as part of [CS50x](https://cs50.harvard.edu/x/2022/).

---

## 🧠 Features
- User registration and login with password hashing
- Real-time stock quotes using the IEX API
- Buy/sell stocks with balance checks
- Portfolio summary with current market prices
- Transaction history table
- Account deletion option
- Responsive HTML/CSS with Jinja templates

---

## 🧰 Tech Stack
- **Backend:** Python, Flask, Flask-Session
- **Frontend:** HTML, CSS (Jinja templates)
- **Database:** SQLite
- **API:** IEX Cloud (stock data)
- **Helpers:** Custom `helpers.py` with `login_required`, `lookup`, and `usd` filters

---

## ⚙️ How to Run Locally
```bash
# Install dependencies
pip install -r requirements.txt

# Initialize database
sqlite3 finance.db < schema.sql

# Set environment variables (example)
export API_KEY=YOUR_IEX_API_KEY
export FLASK_APP=app.py
export FLASK_DEBUG=1

# Run the app
flask run
