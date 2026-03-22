from flask import Flask, render_template, request, redirect, session, flash
import mysql.connector

app = Flask(__name__)
app.secret_key = "secret"

CONNECT TO RAILWAY DATABASE
db = mysql.connector.connect(
    host="YOUR_HOST",
    user="YOUR_USER",
    password="YOUR_PASSWORD",
    database="YOUR_DB"
)


cursor = db.cursor(dictionary=True)

@app.route("/", methods=["GET","POST"])
def login():
    if request.method == "POST":
        sid = request.form["student_id"]

        cursor.execute("SELECT * FROM students WHERE id=%s", (sid,))
        user = cursor.fetchone()

        if user:
            if user["voted"] == "YES":
                flash("Already voted!")
            else:
                session["student"] = sid
                session["name"] = user["name"]
                return redirect("/vote")
        else:
            flash("Invalid ID")

    return render_template("login.html")

@app.route("/vote", methods=["GET","POST"])
def vote():
    if "student" not in session:
        return redirect("/")

    candidates = {
        "President":["Carillo","Palencia"],
        "VicePresident":["Villar","Aguilar"],
        "Secretary":["Lim","Tan"],
        "Treasurer":["Treñas","Mabilog"],
        "Auditor":["Brody","Saul"],
        "PIO":["Marcos","Robledo"],
        "PO":["Duterte","Aquino"]
    }

    if request.method == "POST":
        selected = [request.form.get(p) for p in candidates]

        rep1 = request.form.get("Rep1")
        rep2 = request.form.get("Rep2")

        all_choices = selected + [rep1, rep2]
        clean = [x for x in all_choices if x]

        # ❗ NO DUPLICATES
        if len(clean) != len(set(clean)):
            flash("Duplicate names not allowed!")
            return redirect("/vote")

        # ❗ CHECK IF ALREADY VOTED (DOUBLE SECURITY)
        cursor.execute("SELECT * FROM votes WHERE student_id=%s", (session["student"],))
        if cursor.fetchone():
            flash("Already voted!")
            return redirect("/")

        # SAVE VOTES
        for pos in candidates:
            cursor.execute("INSERT INTO votes VALUES (%s,%s,%s)",
                           (session["student"], pos, request.form.get(pos)))

        cursor.execute("INSERT INTO votes VALUES (%s,'Rep1',%s)", (session["student"], rep1))
        cursor.execute("INSERT INTO votes VALUES (%s,'Rep2',%s)", (session["student"], rep2))

        cursor.execute("UPDATE students SET voted='YES' WHERE id=%s", (session["student"],))
        db.commit()

        flash("Vote submitted!")
        session.clear()
        return redirect("/")

    return render_template("voting.html", candidates=candidates)

@app.route("/admin")
def admin():
    cursor.execute("""
        SELECT position, candidate, COUNT(*) as total
        FROM votes GROUP BY position, candidate
    """)
    data = cursor.fetchall()

    labels = [f"{d['position']} - {d['candidate']}" for d in data]
    values = [d['total'] for d in data]

    return render_template("admin.html", data=data, labels=labels, values=values)

app.run(debug=True)