from flask import Flask, render_template, request, redirect, url_for, session, flash, abort
from werkzeug.security import generate_password_hash, check_password_hash
import sqlite3, os

BASE = os.path.dirname(os.path.abspath(__file__))
DB = os.path.join(BASE, "khaven.db")
app = Flask(__name__)
app.secret_key = os.environ.get("KHAVEN_SECRET", "change-this-secret-before-deploying")

def db():
    c = sqlite3.connect(DB)
    c.row_factory = sqlite3.Row
    return c

def init_db():
    c = db()
    c.executescript("""
    CREATE TABLE IF NOT EXISTS users(
      id INTEGER PRIMARY KEY AUTOINCREMENT,
      username TEXT UNIQUE NOT NULL,
      password TEXT NOT NULL
    );
    CREATE TABLE IF NOT EXISTS stories(
      id INTEGER PRIMARY KEY AUTOINCREMENT,
      title TEXT NOT NULL,
      author TEXT NOT NULL,
      genre TEXT NOT NULL,
      description TEXT NOT NULL,
      cover TEXT DEFAULT '🎀',
      created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );
    CREATE TABLE IF NOT EXISTS chapters(
      id INTEGER PRIMARY KEY AUTOINCREMENT,
      story_id INTEGER NOT NULL,
      number INTEGER NOT NULL,
      title TEXT NOT NULL,
      body TEXT NOT NULL,
      FOREIGN KEY(story_id) REFERENCES stories(id)
    );
    CREATE TABLE IF NOT EXISTS favorites(
      user_id INTEGER NOT NULL,
      story_id INTEGER NOT NULL,
      PRIMARY KEY(user_id, story_id),
      FOREIGN KEY(user_id) REFERENCES users(id),
      FOREIGN KEY(story_id) REFERENCES stories(id)
    );
    """)
    if c.execute("SELECT COUNT(*) FROM stories").fetchone()[0] == 0:
        samples = [
          ("Under the Rose","K-Haven Demo","Romance • Angst","A fictional demo story for K-Haven. Replace it with work you own or have permission to publish.","🌹"),
          ("Painted in You","K-Haven Demo","School • Fluff","A fictional fluffy school-romance demo.","🎨"),
          ("Between the Lines","K-Haven Demo","Office • Slow Burn","A fictional office slow-burn demo.","📖")
        ]
        for s in samples:
            sid = c.execute("INSERT INTO stories(title,author,genre,description,cover) VALUES(?,?,?,?,?)",s).lastrowid
            c.execute("INSERT INTO chapters(story_id,number,title,body) VALUES(?,?,?,?,?)",
                      (sid,1,"Chapter 1 — Beginning",
                       "This is a fictional sample chapter.\n\nReplace this text with your own original chapter or licensed content."))
    c.commit(); c.close()

@app.context_processor
def globals():
    return {"logged_in": "user_id" in session, "username": session.get("username")}

@app.route("/")
def home():
    c=db()
    stories=c.execute("SELECT * FROM stories ORDER BY id DESC").fetchall()
    c.close()
    return render_template("home.html", stories=stories)

@app.route("/register", methods=["GET","POST"])
def register():
    if request.method=="POST":
        username=request.form["username"].strip()
        password=request.form["password"]
        if len(username)<3 or len(password)<8:
            flash("Username must be 3+ characters and password 8+ characters.")
            return redirect(url_for("register"))
        c=db()
        try:
            c.execute("INSERT INTO users(username,password) VALUES(?,?)",(username,generate_password_hash(password)))
            c.commit()
            flash("Account created. Please log in.")
            return redirect(url_for("login"))
        except sqlite3.IntegrityError:
            flash("That username is already taken.")
        finally: c.close()
    return render_template("auth.html", mode="Register")

@app.route("/login", methods=["GET","POST"])
def login():
    if request.method=="POST":
        c=db(); u=c.execute("SELECT * FROM users WHERE username=?",(request.form["username"].strip(),)).fetchone(); c.close()
        if u and check_password_hash(u["password"],request.form["password"]):
            session["user_id"]=u["id"]; session["username"]=u["username"]
            return redirect(url_for("home"))
        flash("Incorrect username or password.")
    return render_template("auth.html", mode="Log in")

@app.route("/logout")
def logout():
    session.clear(); return redirect(url_for("home"))

@app.route("/story/<int:story_id>")
def story(story_id):
    c=db()
    s=c.execute("SELECT * FROM stories WHERE id=?",(story_id,)).fetchone()
    if not s: abort(404)
    chapters=c.execute("SELECT * FROM chapters WHERE story_id=? ORDER BY number",(story_id,)).fetchall()
    fav=False
    if "user_id" in session:
        fav=bool(c.execute("SELECT 1 FROM favorites WHERE user_id=? AND story_id=?",(session["user_id"],story_id)).fetchone())
    c.close()
    return render_template("story.html",story=s,chapters=chapters,fav=fav)

@app.post("/story/<int:story_id>/favorite")
def favorite(story_id):
    if "user_id" not in session:
        return redirect(url_for("login"))
    c=db()
    exists=c.execute("SELECT 1 FROM favorites WHERE user_id=? AND story_id=?",(session["user_id"],story_id)).fetchone()
    if exists: c.execute("DELETE FROM favorites WHERE user_id=? AND story_id=?",(session["user_id"],story_id))
    else: c.execute("INSERT INTO favorites(user_id,story_id) VALUES(?,?)",(session["user_id"],story_id))
    c.commit(); c.close()
    return redirect(request.referrer or url_for("story",story_id=story_id))

@app.route("/chapter/<int:chapter_id>")
def chapter(chapter_id):
    c=db()
    ch=c.execute("""SELECT chapters.*, stories.title AS story_title, stories.id AS story_id
                   FROM chapters JOIN stories ON stories.id=chapters.story_id
                   WHERE chapters.id=?""",(chapter_id,)).fetchone()
    if not ch: abort(404)
    c.close()
    return render_template("chapter.html",chapter=ch)

@app.route("/upload", methods=["GET","POST"])
def upload():
    if "user_id" not in session: return redirect(url_for("login"))
    if request.method=="POST":
        title=request.form["title"].strip(); genre=request.form["genre"].strip()
        desc=request.form["description"].strip(); author=session["username"]
        ch_title=request.form["chapter_title"].strip(); body=request.form["body"].strip()
        if not all([title,genre,desc,ch_title,body]):
            flash("Please fill every field."); return redirect(url_for("upload"))
        c=db()
        sid=c.execute("INSERT INTO stories(title,author,genre,description,cover) VALUES(?,?,?,?,?)",
                      (title,author,genre,desc,"🎀")).lastrowid
        c.execute("INSERT INTO chapters(story_id,number,title,body) VALUES(?,?,?,?)",(sid,1,ch_title,body))
        c.commit(); c.close()
        return redirect(url_for("story",story_id=sid))
    return render_template("upload.html")

if __name__=="__main__":
    init_db()
    app.run(debug=True)
