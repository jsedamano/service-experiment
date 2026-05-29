from flask import Flask, request, redirect, session, render_template_string
import psycopg2
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)       # Creates web app (app is the object that controls the website)
app.secret_key = "dev-secret-key"  # Needed for sessions. Fine for localhost practice.

DB_CONFIG = {
    "dbname": "login_db",
    "user": "login_user",
    "password": "Ubuntu2005&",
    "host": "localhost",
    "port": 5432
}

def get_db_connection():
    return psycopg2.connect(**DB_CONFIG)

# Error page
def service_unavailable_page():
    return render_template_string("""
        <!doctype html>
        <html lang="en">
        <head>
            <meta charset="utf-8">
            <meta name="viewport" content="width=device-width, initial-scale=1">
            <title>Service unavailable</title>
            <style>
                :root {
                    color-scheme: light;
                    --ink: #172033;
                    --muted: #5f6f89;
                    --panel: rgba(255, 255, 255, 0.84);
                    --line: rgba(23, 32, 51, 0.12);
                    --accent: #0f9f8f;
                    --accent-2: #e94f64;
                    --sky: #dff4ff;
                    --sun: #ffd166;
                }

                * {
                    box-sizing: border-box;
                }

                body {
                    min-height: 100vh;
                    margin: 0;
                    display: grid;
                    place-items: center;
                    padding: 24px;
                    font-family: Arial, Helvetica, sans-serif;
                    color: var(--ink);
                    background:
                        radial-gradient(circle at 18% 20%, rgba(255, 209, 102, 0.62), transparent 21rem),
                        radial-gradient(circle at 82% 16%, rgba(15, 159, 143, 0.22), transparent 24rem),
                        linear-gradient(135deg, #f7fbff 0%, #eaf7f3 48%, #fff7ed 100%);
                }

                .page {
                    width: min(920px, 100%);
                    display: grid;
                    grid-template-columns: minmax(0, 1fr) 280px;
                    gap: 34px;
                    align-items: center;
                    padding: 42px;
                    border: 1px solid var(--line);
                    border-radius: 8px;
                    background: var(--panel);
                    box-shadow: 0 24px 80px rgba(23, 32, 51, 0.14);
                    backdrop-filter: blur(12px);
                }

                .eyebrow {
                    margin: 0 0 12px;
                    font-size: 0.78rem;
                    font-weight: 700;
                    letter-spacing: 0.12em;
                    text-transform: uppercase;
                    color: var(--accent);
                }

                h1 {
                    margin: 0;
                    font-size: clamp(2.25rem, 7vw, 4.9rem);
                    line-height: 0.95;
                    letter-spacing: 0;
                }

                .message {
                    max-width: 560px;
                    margin: 22px 0 0;
                    color: var(--muted);
                    font-size: 1.12rem;
                    line-height: 1.7;
                }

                .status {
                    display: inline-flex;
                    align-items: center;
                    gap: 10px;
                    margin-top: 28px;
                    padding: 12px 16px;
                    border: 1px solid var(--line);
                    border-radius: 8px;
                    background: rgba(255, 255, 255, 0.72);
                    color: #3c4b61;
                    font-size: 0.95rem;
                }

                .pulse {
                    width: 10px;
                    height: 10px;
                    border-radius: 50%;
                    background: var(--accent-2);
                    box-shadow: 0 0 0 8px rgba(233, 79, 100, 0.13);
                }

                .illustration {
                    position: relative;
                    min-height: 260px;
                    display: grid;
                    place-items: center;
                }

                .sun {
                    position: absolute;
                    top: 10px;
                    right: 36px;
                    width: 72px;
                    height: 72px;
                    border-radius: 50%;
                    background: var(--sun);
                    box-shadow: 0 12px 34px rgba(255, 209, 102, 0.48);
                }

                .cloud {
                    position: absolute;
                    top: 70px;
                    left: 14px;
                    width: 150px;
                    height: 54px;
                    border-radius: 999px;
                    background: var(--sky);
                    box-shadow: 74px 28px 0 -12px rgba(223, 244, 255, 0.86);
                }

                .cloud::before,
                .cloud::after {
                    content: "";
                    position: absolute;
                    border-radius: 50%;
                    background: var(--sky);
                }

                .cloud::before {
                    width: 70px;
                    height: 70px;
                    left: 28px;
                    top: -34px;
                }

                .cloud::after {
                    width: 58px;
                    height: 58px;
                    right: 24px;
                    top: -22px;
                }

                .server {
                    position: relative;
                    width: 190px;
                    padding: 18px;
                    border: 1px solid var(--line);
                    border-radius: 8px;
                    background: #ffffff;
                    box-shadow: 0 18px 40px rgba(23, 32, 51, 0.14);
                }

                .server-row {
                    height: 44px;
                    margin-bottom: 12px;
                    border-radius: 6px;
                    border: 1px solid rgba(23, 32, 51, 0.12);
                    background: linear-gradient(90deg, #f7fafc, #eef6f6);
                    display: flex;
                    align-items: center;
                    gap: 8px;
                    padding: 0 12px;
                }

                .server-row:last-child {
                    margin-bottom: 0;
                }

                .light {
                    width: 9px;
                    height: 9px;
                    border-radius: 50%;
                    background: #ccd6e3;
                }

                .light.offline {
                    background: var(--accent-2);
                }

                .slot {
                    flex: 1;
                    height: 7px;
                    border-radius: 999px;
                    background: #dbe5ef;
                }

                @media (max-width: 720px) {
                    .page {
                        grid-template-columns: 1fr;
                        padding: 30px 24px;
                    }

                    .illustration {
                        order: -1;
                        min-height: 210px;
                    }
                }
            </style>
        </head>
        <body>
            <main class="page" role="main">
                <section>
                    <p class="eyebrow">Temporary outage</p>
                    <h1>We are sorry.</h1>
                    <p class="message">
                        This service is currently not available. Our database connection
                        is taking a break, but the app is still here and ready to welcome
                        you back soon.
                    </p>
                    <div class="status" aria-label="Service status">
                        <span class="pulse" aria-hidden="true"></span>
                        Service unavailable - please try again in a moment.
                    </div>
                </section>

                <section class="illustration" aria-hidden="true">
                    <div class="sun"></div>
                    <div class="cloud"></div>
                    <div class="server">
                        <div class="server-row">
                            <span class="light"></span>
                            <span class="slot"></span>
                        </div>
                        <div class="server-row">
                            <span class="light offline"></span>
                            <span class="slot"></span>
                        </div>
                        <div class="server-row">
                            <span class="light"></span>
                            <span class="slot"></span>
                        </div>
                    </div>
                </section>
            </main>
        </body>
        </html>
    """), 503


@app.errorhandler(psycopg2.OperationalError)
@app.errorhandler(psycopg2.InterfaceError)
def handle_database_connection_error(error):
    return service_unavailable_page()


def init_db():
    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id SERIAL PRIMARY KEY,
            username TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL
        )
    """)

    conn.commit()
    cursor.close()
    conn.close()


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

    conn = None
    cursor = None

    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO users (username, password_hash) VALUES (%s, %s)",
            (username, password_hash)
        )

        conn.commit()
        return redirect("/")

    except psycopg2.IntegrityError:
        return "That username already exists. <a href='/register'>Try again</a>"
    except (psycopg2.OperationalError, psycopg2.InterfaceError):
        return service_unavailable_page()
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()


@app.route("/login", methods=["POST"])
def login():
    username = request.form["username"]
    password = request.form["password"]

    conn = None
    cursor = None

    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute(
            "SELECT password_hash FROM users WHERE username = %s",
            (username,)
        )

        user = cursor.fetchone()

    except (psycopg2.OperationalError, psycopg2.InterfaceError):
        return service_unavailable_page()
    finally:
        if cursor:
            cursor.close()
        if conn:
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
    try:
        init_db()
    except (psycopg2.OperationalError, psycopg2.InterfaceError):
        print("PostgreSQL is unavailable. Starting the web app with the friendly error page enabled.")
    app.run(host="0.0.0.0", port=5000,debug=True)
