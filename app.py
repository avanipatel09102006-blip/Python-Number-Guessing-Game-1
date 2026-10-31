"""Number Guessing Game: Flask backend + SQLite (games & leaderboard)."""
import random
import sqlite3
from pathlib import Path

from flask import Flask, jsonify, render_template, request

DB_PATH = Path(__file__).with_name("game.db")
app = Flask(__name__)

# difficulty -> (highest number, max attempts)
LEVELS = {"easy": (50, 8), "medium": (100, 7), "hard": (500, 9)}


def db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    with db() as conn:
        conn.execute(
            """CREATE TABLE IF NOT EXISTS games (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                player TEXT NOT NULL, difficulty TEXT NOT NULL,
                secret INTEGER NOT NULL, high INTEGER NOT NULL,
                max_attempts INTEGER NOT NULL, attempts INTEGER DEFAULT 0,
                status TEXT DEFAULT 'playing',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP)"""
        )


@app.route("/")
def index():
    return render_template("index.html")


@app.post("/api/start")
def start():
    data = request.get_json(silent=True) or {}
    player = (data.get("player") or "Guest").strip()[:20] or "Guest"
    level = data.get("difficulty", "medium")
    if level not in LEVELS:
        return jsonify(error="Unknown difficulty"), 400
    high, max_attempts = LEVELS[level]
    secret = random.randint(1, high)  # secret stays on the server
    with db() as conn:
        cur = conn.execute(
            "INSERT INTO games (player, difficulty, secret, high, max_attempts) VALUES (?,?,?,?,?)",
            (player, level, secret, high, max_attempts),
        )
    return jsonify(game_id=cur.lastrowid, high=high, max_attempts=max_attempts)


@app.post("/api/guess")
def guess():
    data = request.get_json(silent=True) or {}
    try:
        game_id, value = int(data["game_id"]), int(data["guess"])
    except (KeyError, TypeError, ValueError):
        return jsonify(error="Enter a whole number"), 400
    with db() as conn:
        g = conn.execute("SELECT * FROM games WHERE id=?", (game_id,)).fetchone()
        if not g:
            return jsonify(error="Game not found"), 404
        if g["status"] != "playing":
            return jsonify(error="This game is over. Start a new one."), 400
        if not 1 <= value <= g["high"]:
            return jsonify(error=f"Pick a number between 1 and {g['high']}"), 400

        attempts = g["attempts"] + 1
        if value == g["secret"]:
            status, hint = "won", "correct"
        elif attempts >= g["max_attempts"]:
            status, hint = "lost", "higher" if value < g["secret"] else "lower"
        else:
            status, hint = "playing", "higher" if value < g["secret"] else "lower"
        conn.execute("UPDATE games SET attempts=?, status=? WHERE id=?", (attempts, status, game_id))

    out = {"hint": hint, "attempts": attempts, "status": status,
           "attempts_left": g["max_attempts"] - attempts}
    if status == "lost":
        out["secret"] = g["secret"]
    return jsonify(out)


@app.get("/api/leaderboard")
def leaderboard():
    with db() as conn:
        rows = conn.execute(
            """SELECT player, difficulty, attempts FROM games WHERE status='won'
               ORDER BY attempts ASC, id ASC LIMIT 10"""
        ).fetchall()
    return jsonify([dict(r) for r in rows])


@app.get("/api/stats")
def stats():
    with db() as conn:
        r = conn.execute(
            """SELECT COUNT(*) AS played,
                      COALESCE(SUM(status='won'),0) AS won FROM games WHERE status!='playing'"""
        ).fetchone()
    return jsonify(played=r["played"], won=r["won"])


init_db()
if __name__ == "__main__":
    app.run(debug=True)
