from flask import Flask, jsonify

app = Flask(__name__)

expenses = [
	{"id": 1, "item": "coffee", "amount": 3.50, "category": "food"},
	{"id": 2, "item": "bus ticket", "amount": 2.20, "category": "transport"},
]


@app.route("/health")
def health():
	return jsonify(status="ok"), 200


@app.route("/expenses", methods=["GET"])
def get_expenses():
	return jsonify(expenses)


@app.route("/expenses", methods=["POST"])
def add_expense():
	return jsonify(message="created"), 201


if __name__ == "__main__":
	app.run(host="0.0.0.0", port=5050)
