from flask import Flask, render_template, request, redirect, url_for, flash, session
from flask_mysqldb import MySQL

app = Flask(__name__)

from flask_mysqldb import MySQL

app = Flask(__name__)

app.config['MYSQL_HOST'] = "127.0.0.1"
app.config['MYSQL_USER'] = "root"
app.config['MYSQL_PASSWORD'] = ""
app.config['MYSQL_DB'] = "perpustakaan"
app.config['SECRET_KEY'] = 'kunci_rahasia'


mysql = MySQL(app)

@app.route("/", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form['username']
        password = request.form['password']

        # Periksa tabel `peminjam`
        cur = mysql.connection.cursor()
        cur.execute("SELECT * FROM peminjam WHERE nama_peminjam = %s AND password = %s", (username, password))
        peminjam = cur.fetchone()

        if peminjam:
            user_id = peminjam[0]  # Mengambil id_peminjam
            session['user_id'] = user_id
            cur.close()
            return redirect(url_for("pinjam_buku"))  # Jika ditemukan di tabel `peminjam`

        # Periksa tabel `petugas`
        cur.execute("SELECT * FROM petugas WHERE nama_petugas = %s AND password = %s", (username, password))
        petugas = cur.fetchone()

        if petugas:
            cur.close()
            return redirect(url_for("halaman_admin"))  # Jika ditemukan di tabel `petugas`

        cur.close()
        return redirect(url_for("register"))  # Jika tidak ditemukan di kedua tabel

    return render_template("login.html")


@app.route("/register")
def register():
    return render_template("register.html")

@app.route("/register_user", methods=['GET', 'POST'])
def register_user():    
    if request.method == "POST":
        username = request.form['username']
        password = request.form['password']

        cur = mysql.connection.cursor()
        cur.execute("INSERT INTO peminjam (nama_peminjam,  password) VALUES (%s, %s)", (username, password))
        mysql.connection.commit()
        cur.close()
        return redirect(url_for("login"))

@app.route("/halaman_admin")
def halaman_admin():
    return render_template("admin.html")

@app.route("/pinjam_buku", methods=["GET", "POST"])
def pinjam_buku():
    username = request.args.get('username')
    id_peminjam = request.args.get('id_peminjam')
    user_id = session.get('user_id')
    if user_id is None:
        return redirect(url_for("login"))

    cur = mysql.connection.cursor()
    
    # Ambil daftar buku dan petugas
    cur.execute("SELECT * FROM buku")
    buku_list = cur.fetchall()

    cur.execute("SELECT * FROM petugas")
    petugas_list = cur.fetchall()

    if request.method == "POST":
        judul_buku = request.form['judul_buku']

        # Cek apakah buku ada di database
        cur.execute("SELECT * FROM buku WHERE judul_buku = %s", (judul_buku,))
        buku = cur.fetchone()

        if not buku:
            # Buku tidak ditemukan, tampilkan pesan error
            flash("Buku tidak ditemukan", "error")
            return redirect(url_for("pinjam_buku", username=username, id_peminjam=id_peminjam))

        # Mendapatkan id_petugas
        id_petugas = request.form['petugas']

        # Menyimpan data peminjaman ke tabel peminjaman
        cur.execute("INSERT INTO peminjaman (id_buku, id_petugas, id_peminjam) VALUES (%s, %s, %s)",
                    (buku[0], id_petugas, user_id))  # Buku[0] adalah id_buku
        mysql.connection.commit()

        cur.close()
        return redirect(url_for("berhasil"))  # Redirect kembali

    cur.close()
    return render_template("pinjam_buku.html", buku_list=buku_list, petugas_list=petugas_list, username=username)

@app.route("/berhasil")
def berhasil():
    return render_template("selesai.html")

if __name__ == "__main__":
    app.run(debug=True)