# Number Guessing Game (Flask + SQLite)

    pip install -r requirements.txt
    python app.py
Open http://127.0.0.1:5000

- Secret number is stored server-side (SQLite `games` table), so it cannot be read from the browser
- 3 difficulty levels, limited attempts, higher/lower hints, narrowing range bar
- Leaderboard + win stats from the database
- Responsive CSS Grid layout, keyboard friendly, print-friendly light theme
