import os
import time
import logging
from flask import Flask, request, jsonify
from flask_jwt_extended import JWTManager, jwt_required, get_jwt_identity
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
        CREATE TABLE IF NOT EXISTS tasks (
            id SERIAL PRIMARY KEY,
            title VARCHAR(200) NOT NULL,
            description TEXT,
            status VARCHAR(20) DEFAULT 'pending',
            user_id INTEGER NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """))
    conn.commit()


@app.get("/health")
def health():
    return jsonify({"status": "ok", "service": "task-service"})


@app.get("/tasks")
@jwt_required()
def list_tasks():
    user_id = get_jwt_identity()
    with engine.connect() as conn:
        rows = conn.execute(
            text("SELECT id, title, description, status, created_at, updated_at FROM tasks WHERE user_id = :uid ORDER BY created_at DESC"),
            {"uid": user_id},
        ).fetchall()
    return jsonify([
        {"id": r[0], "title": r[1], "description": r[2], "status": r[3],
         "created_at": str(r[4]), "updated_at": str(r[5])}
        for r in rows
    ])


@app.post("/tasks")
@jwt_required()
def create_task():
    user_id = get_jwt_identity()
    data = request.get_json()
    if not data or "title" not in data:
        return jsonify({"error": "title is required"}), 400

    with engine.connect() as conn:
        row = conn.execute(
            text("INSERT INTO tasks (title, description, user_id) VALUES (:t, :d, :uid) RETURNING id, title, description, status, created_at"),
            {"t": data["title"], "d": data.get("description", ""), "uid": user_id},
        ).fetchone()
        conn.commit()

    return jsonify({"id": row[0], "title": row[1], "description": row[2], "status": row[3], "created_at": str(row[4])}), 201


@app.put("/tasks/<int:task_id>")
@jwt_required()
def update_task(task_id):
    user_id = get_jwt_identity()
    data = request.get_json()
    if not data:
        return jsonify({"error": "request body required"}), 400

    allowed = {"title", "description", "status"}
    updates = {k: v for k, v in data.items() if k in allowed}
    if not updates:
        return jsonify({"error": "no valid fields to update"}), 400

    set_clause = ", ".join(f"{k} = :{k}" for k in updates)
    updates["id"] = task_id
    updates["uid"] = user_id

    with engine.connect() as conn:
        result = conn.execute(
            text(f"UPDATE tasks SET {set_clause}, updated_at = NOW() WHERE id = :id AND user_id = :uid RETURNING id"),
            updates,
        )
        conn.commit()
        if not result.fetchone():
            return jsonify({"error": "Task not found"}), 404

    return jsonify({"message": "Task updated"})


@app.delete("/tasks/<int:task_id>")
@jwt_required()
def delete_task(task_id):
    user_id = get_jwt_identity()
    with engine.connect() as conn:
        result = conn.execute(
            text("DELETE FROM tasks WHERE id = :id AND user_id = :uid RETURNING id"),
            {"id": task_id, "uid": user_id},
        )
        conn.commit()
        if not result.fetchone():
            return jsonify({"error": "Task not found"}), 404

    return jsonify({"message": "Task deleted"})


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
