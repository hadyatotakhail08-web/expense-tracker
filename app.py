import os
import sqlite3

from flask import Flask, jsonify, request

app = Flask(__name__)
app.config["SECRET_KEY"] = os.environ.get("SECRET_KEY", "dev-only-fallback")
DB_PATH = "expenses.db"
from flask import Flask, jsonify, request
import sqlite3

app = Flask(__name__)
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


@app.route("/health")
def health():
	return jsonify(status="broken"), 200


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


if __name__ == "__main__":
	app.run(host="0.0.0.0", port=5050)
