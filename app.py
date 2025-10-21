import os

from cs50 import SQL
from flask import Flask, flash, redirect, render_template, request, session
from flask_session import Session
from werkzeug.security import check_password_hash, generate_password_hash

from helpers import apology, login_required, lookup, usd

# Configure application
app = Flask(__name__)

# Custom filter
app.jinja_env.filters["usd"] = usd

# Configure session to use filesystem (instead of signed cookies)
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
Session(app)

# Configure CS50 Library to use SQLite database
db = SQL("sqlite:///finance.db")


@app.after_request
def after_request(response):
    """Ensure responses aren't cached"""
    response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
    response.headers["Expires"] = 0
    response.headers["Pragma"] = "no-cache"
    return response


@app.route("/")
@login_required
def index():
    """Show portfolio of stocks"""
    # Get info
    stocks = db.execute(
        "SELECT symbol, SUM(shares) as total_shares FROM transactions WHERE user_id = :user_id GROUP BY symbol HAVING total_shares > 0",
        user_id=session["user_id"],
    )
    cash = db.execute(
        "SELECT cash FROM users WHERE id = :user_id", user_id=session["user_id"]
    )[0]["cash"]

    total_value = cash
    grand_total = cash

    for stock in stocks:
        quote = lookup(stock["symbol"])
        stock["name"] = quote["name"]
        stock["price"] = quote["price"]
        stock["value"] = stock["price"] * stock["total_shares"]
        total_value += stock["value"]
        grand_total += stock["value"]

    return render_template(
        "index.html",
        stocks=stocks,
        cash=usd(cash),
        total_value=usd(total_value),
        grand_total=usd(grand_total),
    )


@app.route("/buy", methods=["GET", "POST"])
@login_required
def buy():
    """Buy shares of stock"""
    ## Get user's cashhhh
    cash = db.execute(
        "SELECT cash FROM users WHERE id = :user_id", user_id=session["user_id"]
    )[0]["cash"]
    if request.method == "POST":
        type = "Buy"
        symbol = request.form.get("symbol").upper()
        shares = request.form.get("shares")
        if not symbol:
            return apology("must provide a symbol", 400)
        elif not shares or not shares.isdigit() or int(shares) <= 0:
            return apology("must provide a positive number", 400)

        quote = lookup(symbol)
        if quote is None:
            return apology("symbol not found", 400)

        price = quote["price"]
        total = int(shares) * price

        if cash < total:
            return apology("get more money to buy", 400)

        db.execute(
            "UPDATE users SET cash = cash - :total WHERE id = :user_id",
            total=total,
            user_id=session["user_id"],
        )

        db.execute(
            "INSERT INTO transactions (user_id, type, symbol, shares, price) VALUES (:user_id, :type, :symbol, :shares, :price)",
            user_id=session["user_id"],
            type=type,
            symbol=symbol,
            shares=shares,
            price=price,
        )

        flash(f"Bought {shares} shares of {symbol} for {usd(total)}")

        # Redirect user to home page
        return redirect("/")
    # User reached route via GET (as by clicking a link or via redirect)
    else:
        return render_template("buy.html", cash=cash)


@app.route("/history")
@login_required
def history():
    """Show history of transactions"""
    transactions = db.execute(
        "SELECT * FROM transactions WHERE user_id = :user_id ORDER BY timestamp DESC",
        user_id=session["user_id"],
    )
    return render_template("history.html", transactions=transactions)


@app.route("/login", methods=["GET", "POST"])
def login():
    """Log user in"""

    # Forget any user_id
    session.clear()

    # User reached route via POST (as by submitting a form via POST)
    if request.method == "POST":
        # Ensure username was submitted
        if not request.form.get("username"):
            return apology("must provide username", 403)

        # Ensure password was submitted
        elif not request.form.get("password"):
            return apology("must provide password", 403)

        # Query database for username
        rows = db.execute(
            "SELECT * FROM users WHERE username = ?", request.form.get("username")
        )

        # Ensure username exists and password is correct
        if len(rows) != 1 or not check_password_hash(
            rows[0]["hash"], request.form.get("password")
        ):
            return apology("invalid username and/or password", 403)

        # Remember which user has logged in
        session["user_id"] = rows[0]["id"]

        # Redirect user to home page
        return redirect("/")

    # User reached route via GET (as by clicking a link or via redirect)
    else:
        return render_template("login.html")


@app.route("/logout")
def logout():
    """Log user out"""

    # Forget any user_id
    session.clear()

    # Redirect user to login form
    return redirect("/")


@app.route("/quote", methods=["GET", "POST"])
@login_required
def quote():
    """Get stock quote."""
    if request.method == "POST":
        symbol = request.form.get("symbol")
        quote = lookup(symbol)
        if not quote:
            return apology("the symbol is invalid", 400)
        return render_template("quote.html", quote=quote)
    else:
        return render_template("quote.html")


@app.route("/register", methods=["GET", "POST"])
def register():
    """Register user"""
    # Forget any user_id
    session.clear()

    # User reached route via POST (as by submitting a form via POST)
    if request.method == "POST":
        # Ensure username was submitted
        if not request.form.get("username"):
            return apology("must provide username", 400)

        # Ensure password was submitted
        elif not request.form.get("password"):
            return apology("must provide password", 400)

        # Ensure confirmation password was submitted
        elif not request.form.get("confirmation"):
            return apology("must provide confirmation", 400)

        # Match
        elif request.form.get("password") != request.form.get("confirmation"):
            return apology("passwords don't match", 400)

        # Query database for username
        rows = db.execute(
            "SELECT * FROM users WHERE username = ?", request.form.get("username")
        )

        # Ensure username do not exist
        if len(rows) != 0:
            return apology("username already exists", 400)

        # Insert the new user in the database
        db.execute(
            "INSERT INTO users (username, hash) VALUES (?, ?)",
            request.form.get("username"),
            generate_password_hash(request.form.get("password")),
        )

        # Query database for the new user
        rows = db.execute(
            "SELECT * FROM users WHERE username = ?", request.form.get("username")
        )

        # Remember which user has logged in
        session["user_id"] = rows[0]["id"]

        # Redirect user to home page
        return redirect("/")

    # User reached route via GET (as by clicking a link or via redirect)
    else:
        return render_template("register.html")


@app.route("/sell", methods=["GET", "POST"])
@login_required
def sell():
    """Sell shares of stock"""
    ## Get the stock of the user
    stocks = db.execute(
        "SELECT symbol, SUM(shares) as total_shares FROM transactions WHERE user_id = :user_id GROUP BY symbol HAVING total_shares > 0",
        user_id=session["user_id"],
    )

    if request.method == "POST":
        type = "Sell"
        symbol = request.form.get("symbol").upper()
        shares = request.form.get("shares")
        if not symbol:
            return apology("must provide symbol", 400)
        elif not shares or not shares.isdigit() or int(shares) <= 0:
            return apology("must provide a positive number", 400)
        else:
            shares = int(shares)

        for stock in stocks:
            if stock["symbol"] == symbol:
                if stock["total_shares"] < shares:
                    return apology("not enough shares", 400)
                else:
                    quote = lookup(symbol)
                    if quote is None:
                        return apology("the symbol is invalid")
                    price = quote["price"]
                    total_sale = price * shares

                    ## update info
                    db.execute(
                        "UPDATE users SET cash = cash + :total_sale WHERE id = :user_id",
                        total_sale=total_sale,
                        user_id=session["user_id"],
                    )

                    db.execute(
                        "INSERT INTO transactions (user_id, type, symbol, shares, price) VALUES (:user_id, :type, :symbol, :shares, :price)",
                        user_id=session["user_id"],
                        type=type,
                        symbol=symbol,
                        shares=-shares,
                        price=price,
                    )

                    flash(f"Sold {shares} shares of {symbol} for {usd(total_sale)}")
                    return redirect("/")

        return apology("symbol not found")
    # User reached route via GET (as by clicking a link or via redirect)
    else:
        return render_template("sell.html", stocks=stocks)


@app.route("/delete", methods=["GET", "POST"])
@login_required
def delete():
    """GET confirmation for deleting"""
    if request.method == "POST":
        # Ensure username was submitted
        if not request.form.get("username"):
            return apology("must provide username", 403)

        elif not request.form.get("password"):
            return apology("must provide password", 403)

        # Query database for username
        rows = db.execute(
            "SELECT * FROM users WHERE username = ?", request.form.get("username")
        )

        # Ensure username exists and password is correct
        if len(rows) != 1 or not check_password_hash(
            rows[0]["hash"], request.form.get("password")
        ):
            return apology("invalid username and/or password", 403)

        ## DELETE transactions from transactions DB
        db.execute(
            "DELETE FROM transactions WHERE user_id = :user_id",
            user_id=session["user_id"],
        )

        ## DELETE user from users DB
        db.execute("DELETE FROM users WHERE id = :user_id", user_id=session["user_id"])

        # Forget any user_id
        session.clear()

        # Redirect user to login
        return redirect("/")
    else:
        return render_template("delete.html")
