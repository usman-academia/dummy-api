from flask import Flask, request, jsonify
from flask_cors import CORS
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address

# ========================= #
# ==== Configure App ====== #
# ========================= #
app = Flask(__name__)
CORS(app)

# ========================= #
# ==== API Keys =========== #
# ========================= #
VALID_API_KEYS = {
    "A9d#4fG2kL@q": "Shahrukh",
    "R7!sB8xYp$Wm": "Salman",
    "Z6v%J3nQe^Tf": "Amir"
}

# ========================= #
# ==== Limiter Setup ====== #
# ========================= #
def get_limiter_key():
    api_key = request.headers.get("X-API-KEY")
    if api_key in VALID_API_KEYS:
        return api_key  # per-user
    return get_remote_address()  # fallback per-IP

limiter = Limiter(
    key_func=get_limiter_key,
    app=app,
    default_limits=[]
)

# ========================= #
# ==== Helper Functions === #
# ========================= #
def get_numbers():
    try:
        data = request.get_json()
    except Exception:
        return None, jsonify({"status": "error", "message": "Expecting JSON format"}), 400

    if not data:
        return None, jsonify({"status": "error", "message": "JSON body is required"}), 400

    missing_keys = [k for k in ["first_number", "second_number"] if k not in data]
    if missing_keys:
        return None, jsonify({"status": "error", "message": f"Missing keys: {', '.join(missing_keys)}"}), 400

    try:
        a = float(data["first_number"])
        b = float(data["second_number"])
    except ValueError:
        return None, jsonify({"status": "error", "message": "Numbers must be numeric"}), 400

    return (a, b), None, None

# ========================= #
# ==== API Key Enforcement #
# ========================= #
@app.before_request
def require_api_key_for_user_routes():
    route = request.endpoint
    api_key = request.headers.get("X-API-KEY")
    if route in ["mul", "div"] and api_key not in VALID_API_KEYS:
        return jsonify({"status": "error", "message": "API key missing or invalid"}), 401

# ========================= #
# ==== Routes ============= #
# ========================= #
@app.route("/")
def home():
    return jsonify({"message": "Calculator API is running!", "status": "online"}), 200

@app.route("/add", methods=["POST"])
@limiter.limit("5 per minute")
def add():
    nums, error, code = get_numbers()
    if error:
        return error, code
    a, b = nums
    return jsonify({"result": a + b})

@app.route("/sub", methods=["POST"])
@limiter.limit("5 per minute")
def sub():
    nums, error, code = get_numbers()
    if error:
        return error, code
    a, b = nums
    return jsonify({"result": a - b})

@app.route("/mul", methods=["POST"])
@limiter.limit("10 per minute")
def mul():
    nums, error, code = get_numbers()
    if error:
        return error, code
    a, b = nums
    return jsonify({"result": a * b})

@app.route("/div", methods=["POST"])
@limiter.limit("5 per minute")
@limiter.limit("10 per hour")
def div():
    nums, error, code = get_numbers()
    if error:
        return error, code
    a, b = nums
    if b == 0:
        return jsonify({"status": "error", "message": "Division by zero is not allowed"}), 400
    return jsonify({"result": a / b})

# ========================= #
# ==== JSON for Limits ==== #
# ========================= #
@app.errorhandler(429)
def ratelimit_handler(e):
    return jsonify({
        "status": "error",
        "message": "Rate limit exceeded",
        "retry_after_seconds": e.retry_after
    }), 429

import os

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    print("="*50)
    print("CALCULATOR API (Per-IP + Per-User)")
    print("="*50)
    app.run(host='0.0.0.0', port=port)
