import os
import sqlite3
import time

from flask import Flask, jsonify, request

from prometheus_client import Counter, Histogram, start_http_server

REQUEST_COUNT = Counter(
    "flask_requests_total",
    "Total number of HTTP requests",
    ["endpoint", "status"],
)
REQUEST_LATENCY = Histogram(
    "flask_request_latency_seconds",
    "HTTP request latency in seconds",
    ["endpoint"],
)

app = Flask(__name__)
app.config["SECRET_KEY"] = os.environ.get("SECRET_KEY", "dev-only-fallback")
DB_PATH = "expenses.db"


def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    conn = get_db()
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS expenses (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            item TEXT NOT NULL,
            amount REAL NOT NULL,
            category TEXT NOT NULL
        )
        """
    )
    count = conn.execute("SELECT COUNT(*) FROM expenses").fetchone()[0]
    if count == 0:
        conn.executemany(
            "INSERT INTO expenses (item, amount, category) VALUES (?, ?, ?)",
            [("coffee", 3.50, "food"), ("bus ticket", 2.20, "transport")],
        )
    conn.commit()
    conn.close()


init_db()


@app.before_request
def start_timer():
    request.start_time = time.perf_counter()


@app.after_request
def track_requests(response):
    REQUEST_LATENCY.labels(endpoint=request.path).observe(
        time.perf_counter() - request.start_time
    )
    REQUEST_COUNT.labels(endpoint=request.path, status=response.status_code).inc()
    return response


@app.route("/health")
def health():
    return jsonify(status="ok"), 200


@app.route("/expenses", methods=["GET"])
def get_expenses():
    conn = get_db()
    rows = conn.execute("SELECT * FROM expenses").fetchall()
    conn.close()
    return jsonify([dict(row) for row in rows])


@app.route("/expenses", methods=["POST"])
def add_expense():
    data = request.get_json()
    if not data or not all(k in data for k in ("item", "amount", "category")):
        return jsonify(message="invalid expense"), 400
    conn = get_db()
    cursor = conn.execute(
        "INSERT INTO expenses (item, amount, category) VALUES (?, ?, ?)",
        (data["item"], data["amount"], data["category"]),
    )
    conn.commit()
    conn.close()
    return jsonify(message="created", id=cursor.lastrowid), 201


start_http_server(9200)

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5050)
