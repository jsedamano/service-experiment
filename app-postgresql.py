from flask import Flask, request, redirect, session, render_template_string
import os
import psycopg2
import re
import time
from werkzeug.exceptions import HTTPException
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)       # Creates web app (app is the object that controls the website)


def load_env_file(filename=".env"):
    if not os.path.exists(filename):
        return

    with open(filename) as env_file:
        for line in env_file:
            line = line.strip()

            if not line or line.startswith("#") or "=" not in line:
                continue

            key, value = line.split("=", 1)
            os.environ.setdefault(key.strip(), value.strip().strip("\"'"))


load_env_file()
app.secret_key = os.environ.get("SECRET_KEY", "dev-secret-key")  # Needed for sessions. Use a strong value in .env.
APP_HOST = os.environ.get("APP_HOST", "0.0.0.0")
APP_PORT = int(os.environ.get("APP_PORT", 5000))
FLASK_DEBUG = os.environ.get("FLASK_DEBUG", "false").lower() == "true"

MAX_LOGIN_ATTEMPTS = 3
LOGIN_TIMEOUT_SECONDS = 60
USERNAME_PATTERN = re.compile(r"^[A-Za-z0-9._-]{3,30}$")
MIN_PASSWORD_LENGTH = 8
MAX_PASSWORD_LENGTH = 128
login_attempts = {}

DB_CONFIG = {
    "dbname": os.environ["DB_NAME"],
    "user": os.environ["DB_USER"],
    "password": os.environ["DB_PASSWORD"],
    "host": os.environ["DB_HOST"],
    "port": int(os.environ.get("DB_PORT", 5432))
}

def get_db_connection():
    return psycopg2.connect(**DB_CONFIG)


def normalize_username(username):
    return username.strip()


def password_has_control_characters(password):
    return any(ord(character) < 32 or ord(character) == 127 for character in password)


def validate_username(username):
    if not USERNAME_PATTERN.fullmatch(username):
        return "Usernames must be 3-30 characters and can only use letters, numbers, dots, underscores, or hyphens."

    return None


def validate_registration_input(username, password):
    username_error = validate_username(username)
    if username_error:
        return username_error

    if len(password) < MIN_PASSWORD_LENGTH:
        return f"Passwords must be at least {MIN_PASSWORD_LENGTH} characters long."

    if len(password) > MAX_PASSWORD_LENGTH:
        return f"Passwords must be {MAX_PASSWORD_LENGTH} characters or fewer."

    if password_has_control_characters(password):
        return "Passwords cannot include control characters."

    return None


def login_input_looks_safe(username, password):
    return (
        validate_username(username) is None
        and len(password) <= MAX_PASSWORD_LENGTH
        and not password_has_control_characters(password)
    )


def get_login_attempt_key():
    return request.headers.get("X-Forwarded-For", request.remote_addr or "unknown").split(",")[0].strip()


def get_login_timeout_remaining():
    attempt_key = get_login_attempt_key()
    attempt = login_attempts.get(attempt_key)

    if not attempt:
        return 0

    locked_until = attempt.get("locked_until", 0)
    if not locked_until:
        return 0

    remaining_seconds = int(locked_until - time.time())

    if remaining_seconds <= 0:
        login_attempts.pop(attempt_key, None)
        return 0

    return remaining_seconds


def record_failed_login_attempt():
    attempt_key = get_login_attempt_key()
    attempt = login_attempts.setdefault(attempt_key, {"count": 0, "locked_until": 0})
    attempt["count"] += 1

    if attempt["count"] >= MAX_LOGIN_ATTEMPTS:
        attempt["locked_until"] = time.time() + LOGIN_TIMEOUT_SECONDS


def clear_login_attempts():
    login_attempts.pop(get_login_attempt_key(), None)


def app_page(title, eyebrow, body, **context):
    rendered_body = render_template_string(body, **context)

    return render_template_string("""
        <!doctype html>
        <html lang="en">
        <head>
            <meta charset="utf-8">
            <meta name="viewport" content="width=device-width, initial-scale=1">
            <title>{{ title }}</title>
            <style>
                :root {
                    color-scheme: light;
                    --ink: #172033;
                    --muted: #5f6f89;
                    --panel: rgba(255, 255, 255, 0.86);
                    --line: rgba(23, 32, 51, 0.12);
                    --accent: #0f9f8f;
                    --accent-dark: #087a71;
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

                .shell {
                    width: min(980px, 100%);
                    display: grid;
                    grid-template-columns: minmax(0, 1fr) 360px;
                    gap: 34px;
                    align-items: stretch;
                    padding: 42px;
                    border: 1px solid var(--line);
                    border-radius: 8px;
                    background: var(--panel);
                    box-shadow: 0 24px 80px rgba(23, 32, 51, 0.14);
                    backdrop-filter: blur(12px);
                }

                .intro {
                    position: relative;
                    min-height: 420px;
                    display: flex;
                    flex-direction: column;
                    justify-content: space-between;
                    overflow: hidden;
                    padding: 6px 0;
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
                    font-size: clamp(2.45rem, 7vw, 5rem);
                    line-height: 0.95;
                    letter-spacing: 0;
                }

                .intro-text {
                    max-width: 500px;
                    margin: 22px 0 0;
                    color: var(--muted);
                    font-size: 1.08rem;
                    line-height: 1.7;
                }

                .scene {
                    position: relative;
                    min-height: 180px;
                    margin-top: 24px;
                }

                .sun {
                    position: absolute;
                    top: 12px;
                    left: 22px;
                    width: 72px;
                    height: 72px;
                    border-radius: 50%;
                    background: var(--sun);
                    box-shadow: 0 12px 34px rgba(255, 209, 102, 0.48);
                }

                .cloud {
                    position: absolute;
                    top: 80px;
                    left: 42px;
                    width: 160px;
                    height: 54px;
                    border-radius: 999px;
                    background: var(--sky);
                    box-shadow: 86px 24px 0 -12px rgba(223, 244, 255, 0.86);
                }

                .cloud::before,
                .cloud::after {
                    content: "";
                    position: absolute;
                    border-radius: 50%;
                    background: var(--sky);
                }

                .cloud::before {
                    width: 72px;
                    height: 72px;
                    left: 30px;
                    top: -34px;
                }

                .cloud::after {
                    width: 58px;
                    height: 58px;
                    right: 24px;
                    top: -22px;
                }

                .spark {
                    position: absolute;
                    right: 42px;
                    bottom: 20px;
                    width: 82px;
                    height: 82px;
                    border-radius: 50%;
                    border: 16px solid rgba(15, 159, 143, 0.18);
                    box-shadow: inset 0 0 0 14px rgba(233, 79, 100, 0.12);
                }

                .panel {
                    align-self: center;
                    padding: 28px;
                    border: 1px solid var(--line);
                    border-radius: 8px;
                    background: rgba(255, 255, 255, 0.78);
                    box-shadow: 0 18px 40px rgba(23, 32, 51, 0.11);
                }

                .panel h2 {
                    margin: 0 0 6px;
                    font-size: 1.55rem;
                    line-height: 1.2;
                    letter-spacing: 0;
                }

                .panel p {
                    margin: 0 0 22px;
                    color: var(--muted);
                    line-height: 1.55;
                }

                .alert {
                    display: grid;
                    grid-template-columns: 12px minmax(0, 1fr);
                    gap: 12px;
                    align-items: start;
                    margin: 0 0 18px;
                    padding: 14px;
                    border: 1px solid rgba(233, 79, 100, 0.24);
                    border-radius: 8px;
                    background: rgba(233, 79, 100, 0.08);
                    color: #7d2534;
                    line-height: 1.45;
                }

                .alert-dot {
                    width: 10px;
                    height: 10px;
                    margin-top: 6px;
                    border-radius: 50%;
                    background: var(--accent-2);
                    box-shadow: 0 0 0 6px rgba(233, 79, 100, 0.13);
                }

                .alert strong {
                    display: block;
                    margin-bottom: 2px;
                    color: #5f1e2a;
                }

                form {
                    display: grid;
                    gap: 14px;
                }

                label {
                    display: grid;
                    gap: 7px;
                    color: #34445b;
                    font-size: 0.92rem;
                    font-weight: 700;
                }

                input {
                    width: 100%;
                    min-height: 48px;
                    border: 1px solid rgba(23, 32, 51, 0.16);
                    border-radius: 8px;
                    padding: 0 14px;
                    color: var(--ink);
                    background: #ffffff;
                    font: inherit;
                    outline: none;
                    transition: border-color 0.18s ease, box-shadow 0.18s ease;
                }

                input:focus {
                    border-color: rgba(15, 159, 143, 0.8);
                    box-shadow: 0 0 0 4px rgba(15, 159, 143, 0.14);
                }

                input.has-error {
                    border-color: rgba(233, 79, 100, 0.72);
                    box-shadow: 0 0 0 4px rgba(233, 79, 100, 0.11);
                }

                button,
                .button {
                    min-height: 48px;
                    display: inline-flex;
                    align-items: center;
                    justify-content: center;
                    border: 0;
                    border-radius: 8px;
                    padding: 0 18px;
                    color: #ffffff;
                    background: var(--accent);
                    font: inherit;
                    font-weight: 700;
                    text-decoration: none;
                    cursor: pointer;
                    box-shadow: 0 12px 26px rgba(15, 159, 143, 0.26);
                    transition: transform 0.18s ease, background 0.18s ease;
                }

                button:hover,
                .button:hover {
                    background: var(--accent-dark);
                    transform: translateY(-1px);
                }

                button:disabled,
                input:disabled {
                    cursor: not-allowed;
                    opacity: 0.62;
                }

                button:disabled:hover {
                    background: var(--accent);
                    transform: none;
                }

                .link-row {
                    margin-top: 18px;
                    color: var(--muted);
                    font-size: 0.95rem;
                    line-height: 1.5;
                }

                a {
                    color: var(--accent-dark);
                    font-weight: 700;
                    text-decoration: none;
                }

                a:hover {
                    text-decoration: underline;
                }

                .welcome-card {
                    display: grid;
                    gap: 18px;
                    text-align: left;
                }

                .avatar {
                    width: 64px;
                    height: 64px;
                    display: grid;
                    place-items: center;
                    border-radius: 8px;
                    color: #ffffff;
                    background: linear-gradient(135deg, var(--accent), var(--accent-2));
                    font-size: 1.7rem;
                    font-weight: 700;
                    box-shadow: 0 14px 30px rgba(233, 79, 100, 0.18);
                }

                .welcome-name {
                    margin: 0;
                    font-size: 1.9rem;
                    line-height: 1.1;
                    letter-spacing: 0;
                }

                .welcome-note {
                    margin: 0;
                    color: var(--muted);
                    line-height: 1.6;
                }

                @media (max-width: 800px) {
                    .shell {
                        grid-template-columns: 1fr;
                        padding: 30px 24px;
                    }

                    .intro {
                        min-height: 260px;
                    }

                    .scene {
                        min-height: 130px;
                    }

                    .panel {
                        padding: 24px;
                    }
                }
            </style>
        </head>
        <body>
            <main class="shell">
                <section class="intro" aria-label="Welcome">
                    <div>
                        <p class="eyebrow">{{ eyebrow }}</p>
                        <h1>{{ title }}</h1>
                        <p class="intro-text">
                            A simple account space with a calm little interface.
                            Sign in, settle in, and keep moving.
                        </p>
                    </div>
                    <div class="scene" aria-hidden="true">
                        <div class="sun"></div>
                        <div class="cloud"></div>
                        <div class="spark"></div>
                    </div>
                </section>

                <section class="panel">
                    {{ body|safe }}
                </section>
            </main>
        </body>
        </html>
    """, title=title, eyebrow=eyebrow, body=rendered_body)


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
                        This service is currently not available. Something needs our
                        attention behind the scenes, but the app is still here and ready
                        to welcome you back soon.
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


@app.errorhandler(Exception)
def handle_unexpected_error(error):
    if isinstance(error, HTTPException):
        return error

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


def login_page(error=None, username="", timeout_remaining=0):
    return app_page("Log In", "Welcome back", """
        <h2>Access your account</h2>
        <p>
            {% if timeout_remaining %}
                Too many failed attempts. Try again when the countdown ends.
            {% else %}
                Enter your username and password to continue.
            {% endif %}
        </p>

        {% if error %}
            <div class="alert" role="alert">
                <span class="alert-dot" aria-hidden="true"></span>
                <span>
                    <strong>Could not sign you in</strong>
                    {{ error }}
                </span>
            </div>
        {% endif %}

        <form action="/login" method="POST">
            <label>
                Username
                <input class="{% if error %}has-error{% endif %}" name="username" value="{{ username }}" placeholder="Your username" autocomplete="username" minlength="3" maxlength="30" pattern="[A-Za-z0-9._-]{3,30}" title="Use 3-30 letters, numbers, dots, underscores, or hyphens." required {% if timeout_remaining %}disabled{% endif %}>
            </label>

            <label>
                Password
                <input class="{% if error %}has-error{% endif %}" name="password" type="password" placeholder="Your password" autocomplete="current-password" maxlength="128" required {% if timeout_remaining %}disabled{% endif %}>
            </label>

            <button id="login-button" type="submit" {% if timeout_remaining %}disabled{% endif %}>
                {% if timeout_remaining %}
                    Locked for {{ timeout_remaining }} seconds
                {% else %}
                    Log In
                {% endif %}
            </button>
        </form>

        {% if timeout_remaining %}
            <script>
                let timeLeft = {{ timeout_remaining }};
                const formControls = document.querySelectorAll("input, #login-button");
                const loginButton = document.querySelector("#login-button");

                const countdown = setInterval(() => {
                    timeLeft -= 1;

                    if (timeLeft <= 0) {
                        clearInterval(countdown);
                        formControls.forEach((control) => control.disabled = false);
                        loginButton.textContent = "Log In";
                        return;
                    }

                    loginButton.textContent = `Locked for ${timeLeft} seconds`;
                }, 1000);
            </script>
        {% endif %}

        <div class="link-row">
            New here? <a href="/register">Create an account</a>
        </div>
    """, error=error, username=username, timeout_remaining=timeout_remaining)


def register_page(error=None, username=""):
    return app_page("Create Account", "Start fresh", """
        <h2>Make your profile</h2>
        <p>Choose a username and password to create your account.</p>

        {% if error %}
            <div class="alert" role="alert">
                <span class="alert-dot" aria-hidden="true"></span>
                <span>
                    <strong>Could not create account</strong>
                    {{ error }}
                </span>
            </div>
        {% endif %}

        <form action="/register" method="POST">
            <label>
                Username
                <input class="{% if error %}has-error{% endif %}" name="username" value="{{ username }}" placeholder="Choose a username" autocomplete="username" minlength="3" maxlength="30" pattern="[A-Za-z0-9._-]{3,30}" title="Use 3-30 letters, numbers, dots, underscores, or hyphens." required>
            </label>

            <label>
                Password
                <input name="password" type="password" placeholder="Choose a password" autocomplete="new-password" minlength="8" maxlength="128" required>
            </label>

            <button type="submit">Create Account</button>
        </form>

        <div class="link-row">
            Already have an account? <a href="/">Back to Log In</a>
        </div>
    """, error=error, username=username)


# Define URLs using routes
@app.route("/")
def index():
    # Check if the user is already logged in
    if "username" in session:
        return redirect("/home")

    # Return to the browser (log in page) if user is not logged in
    timeout_remaining = get_login_timeout_remaining()
    if timeout_remaining:
        return login_page(
            f"Too many failed attempts. Please wait {timeout_remaining} seconds before trying again.",
            timeout_remaining=timeout_remaining
        ), 429

    return login_page()


@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "GET":
        return register_page()

    username = normalize_username(request.form.get("username", ""))
    password = request.form.get("password", "")
    validation_error = validate_registration_input(username, password)

    if validation_error:
        return register_page(validation_error, username), 400

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
        return register_page(
            "Try another username, or go back to the log in page if this account is yours.",
            username
        ), 409
    except (psycopg2.OperationalError, psycopg2.InterfaceError):
        return service_unavailable_page()
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()


@app.route("/login", methods=["POST"])
def login():
    username = normalize_username(request.form.get("username", ""))
    password = request.form.get("password", "")
    timeout_remaining = get_login_timeout_remaining()

    if timeout_remaining:
        return login_page(
            f"Too many failed attempts. Please wait {timeout_remaining} seconds before trying again.",
            username,
            timeout_remaining
        ), 429

    if not login_input_looks_safe(username, password):
        record_failed_login_attempt()
        timeout_remaining = get_login_timeout_remaining()

        if timeout_remaining:
            return login_page(
                f"Too many failed attempts. Please wait {timeout_remaining} seconds before trying again.",
                username,
                timeout_remaining
            ), 429

        return login_page(
            "Check your username and password, then try again.",
            username
        ), 401

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
        clear_login_attempts()
        session["username"] = username
        return redirect("/home")

    record_failed_login_attempt()
    timeout_remaining = get_login_timeout_remaining()

    if timeout_remaining:
        return login_page(
            f"Too many failed attempts. Please wait {timeout_remaining} seconds before trying again.",
            username,
            timeout_remaining
        ), 429

    return login_page(
        "Check your username and password, then try again.",
        username
    ), 401


@app.route("/home")
def home():
    if "username" not in session:
        return redirect("/")

    username = session["username"]

    return app_page("Hello", "Signed in", """
        <div class="welcome-card">
            <div class="avatar">{{ initial }}</div>
            <div>
                <h2 class="welcome-name">Hello {{ username }}</h2>
                <p class="welcome-note">
                    You are signed in and ready to use the service.
                </p>
            </div>
            <a class="button" href="/logout">Log out</a>
        </div>
    """, username=username, initial=username[:1].upper())


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
    app.run(host=APP_HOST, port=APP_PORT, debug=FLASK_DEBUG)
