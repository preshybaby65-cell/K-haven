# K-Haven platform starter

A small full-stack Flask + SQLite starter for K-Haven.

## Run locally
1. Install Python 3.10+.
2. Open a terminal in this folder.
3. Run: `python -m venv .venv`
4. Activate it, then run: `pip install -r requirements.txt`
5. Run: `python app.py`
6. Open `http://127.0.0.1:5000`

The database (`khaven.db`) is created automatically.

## Included
- Accounts with hashed passwords
- Story pages
- Chapter reading
- Favorites saved per account
- Story upload (first chapter)
- SQLite database
- Responsive pink K-Haven styling

## Before putting it online
Set a strong `KHAVEN_SECRET` environment variable, use HTTPS, add email/password reset and moderation, and move SQLite to a managed database if you expect many users.
