from flask import Flask, request, redirect, session, render_template_string
import sqlite3
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)       # Creates web app (app is the object that controls the website)
app.secret_key = "dev-secret-key"  # Needed for sessions. Fine for localhost practice.

DB_NAME = "users.db"

# Prepare the database
def init_db():
    conn = sqlite3.connect(DB_NAME) # Connect to the sqlite database
    cursor = conn.cursor()          # Object to send sql command to the database

    # Send sql command to sqlite, creates the table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL
        )
    """)

    conn.commit()   # Save the changes
    conn.close()    # Close the connection


# Define URLs using routes
@app.route("/")
def index():
    # Check if the user is already logged in
    if "username" in session:
        return redirect("/home")

    # Return to the browser (log in page) if user is not logged in
    return render_template_string("""
        <h1>Log In</h1>

        <form action="/login" method="POST">
            <input name="username" placeholder="Username" required>
            <br><br>
            <input name="password" type="password" placeholder="Password" required>
            <br><br>
            <button type="submit">Log In</button>
        </form>

        <br>

        <a href="/register">Create an account</a>
    """)


@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "GET":
        return render_template_string("""
            <h1>Create an account</h1>

            <form action="/register" method="POST">
                <input name="username" placeholder="Username" required>
                <br><br>
                <input name="password" type="password" placeholder="Password" required>
                <br><br>
                <button type="submit">Create Account</button>
            </form>

            <br>

            <a href="/">Back to Log In</a>
        """)

    username = request.form["username"]
    password = request.form["password"]

    password_hash = generate_password_hash(password)

    try:
        conn = sqlite3.connect(DB_NAME)
        cursor = conn.cursor()

        cursor.execute(
            "INSERT INTO users (username, password_hash) VALUES (?, ?)",
            (username, password_hash)
        )

        conn.commit()
        conn.close()

        return redirect("/")

    except sqlite3.IntegrityError:
        return "That username already exists. <a href='/register'>Try again</a>"


@app.route("/login", methods=["POST"])
def login():
    username = request.form["username"]
    password = request.form["password"]

    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()

    cursor.execute(
        "SELECT password_hash FROM users WHERE username = ?",
        (username,)
    )

    user = cursor.fetchone()
    conn.close()

    if user and check_password_hash(user[0], password):
        session["username"] = username
        return redirect("/home")

    return "Invalid username or password. <a href='/'>Try again</a>"


@app.route("/home")
def home():
    if "username" not in session:
        return redirect("/")

    return render_template_string("""
        <h1>Hello {{ username }}</h1>

        <a href="/logout">Log out</a>
    """, username=session["username"])


@app.route("/logout")
def logout():
    session.pop("username", None)
    return redirect("/")


# Flask app starts
if __name__ == "__main__":
    init_db()
    app.run(host="0.0.0.0", port=5000,debug=True)
