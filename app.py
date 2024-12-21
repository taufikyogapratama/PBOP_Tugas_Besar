from flask import Flask, render_template

app = Flask(__name__)

@app.route("/")
def first_menu():
    return render_template("first_page.html")

@app.route("/halaman_admin")
def halaman_admin():
    return render_template("admin.html")

@app.route("/halaman_user")
def halaman_user():
    return render_template("user.html")