import os
import time
import logging
from flask import Flask, request, jsonify
from flask_jwt_extended import JWTManager, create_access_token, jwt_required, get_jwt_identity
from werkzeug.security import generate_password_hash, check_password_hash
from sqlalchemy import create_engine, text
from sqlalchemy.exc import OperationalError

logging.basicConfig(level=logging.INFO)
log = logging.getLogger(__name__)

app = Flask(__name__)
app.config["JWT_SECRET_KEY"] = os.environ["JWT_SECRET_KEY"]
jwt = JWTManager(app)

DB_URL = (
    f"postgresql://{os.environ['DB_USER']}:{os.environ['DB_PASSWORD']}"
    f"@{os.environ['DB_HOST']}:{os.environ.get('DB_PORT', 5432)}/{os.environ['DB_NAME']}"
)


def get_engine(retries=10, delay=3):
    for i in range(retries):
        try:
            engine = create_engine(DB_URL)
            with engine.connect() as conn:
                conn.execute(text("SELECT 1"))
            log.info("Database connected")
            return engine
        except OperationalError as e:
            log.warning(f"DB not ready ({i+1}/{retries}): {e}")
            time.sleep(delay)
    raise RuntimeError("Could not connect to database")


engine = get_engine()

with engine.connect() as conn:
    conn.execute(text("""
        CREATE TABLE IF NOT EXISTS users (
            id SERIAL PRIMARY KEY,
            username VARCHAR(50) UNIQUE NOT NULL,
            email VARCHAR(100) UNIQUE NOT NULL,
            password_hash VARCHAR(255) NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """))
    conn.commit()


@app.get("/health")
def health():
    return jsonify({"status": "ok", "service": "user-service"})


@app.post("/register")
def register():
    data = request.get_json()
    if not data or not all(k in data for k in ("username", "email", "password")):
        return jsonify({"error": "username, email, and password are required"}), 400

    pw_hash = generate_password_hash(data["password"])
    try:
        with engine.connect() as conn:
            result = conn.execute(
                text("INSERT INTO users (username, email, password_hash) VALUES (:u, :e, :p) RETURNING id"),
                {"u": data["username"], "e": data["email"], "p": pw_hash},
            )
            conn.commit()
            user_id = result.fetchone()[0]
    except Exception as e:
        return jsonify({"error": "Username or email already exists"}), 409

    token = create_access_token(identity=str(user_id))
    return jsonify({"token": token, "user_id": user_id}), 201


@app.post("/login")
def login():
    data = request.get_json()
    if not data or "email" not in data or "password" not in data:
        return jsonify({"error": "email and password are required"}), 400

    with engine.connect() as conn:
        row = conn.execute(
            text("SELECT id, password_hash FROM users WHERE email = :e"),
            {"e": data["email"]},
        ).fetchone()

    if not row or not check_password_hash(row[1], data["password"]):
        return jsonify({"error": "Invalid credentials"}), 401

    token = create_access_token(identity=str(row[0]))
    return jsonify({"token": token, "user_id": row[0]})


@app.get("/me")
@jwt_required()
def me():
    user_id = get_jwt_identity()
    with engine.connect() as conn:
        row = conn.execute(
            text("SELECT id, username, email, created_at FROM users WHERE id = :id"),
            {"id": user_id},
        ).fetchone()

    if not row:
        return jsonify({"error": "User not found"}), 404

    return jsonify({"id": row[0], "username": row[1], "email": row[2], "created_at": str(row[3])})


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
