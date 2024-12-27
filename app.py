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
            return redirect(url_for("admin_peminjaman"))  # Jika ditemukan di tabel `petugas`

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

@app.route("/admin_peminjaman")
def admin_peminjaman():
    cur = mysql.connection.cursor()

    # Query untuk mendapatkan data yang diminta
    cur.execute("""
        SELECT peminjaman.id_peminjaman, 
               peminjam.nama_peminjam, 
               buku.judul_buku, 
               petugas.nama_petugas, 
               peminjaman.tanggal 
        FROM peminjaman
        JOIN peminjam ON peminjaman.id_peminjam = peminjam.id_peminjam
        JOIN buku ON peminjaman.id_buku = buku.id_buku
        JOIN petugas ON peminjaman.id_petugas = petugas.id_petugas
    """)
    data_peminjaman = cur.fetchall()  # Mengambil semua hasil query
    cur.close()

    # Pass data ke template
    return render_template("admin_df_peminjaman.html", data_peminjaman=data_peminjaman)

@app.route("/hapus_peminjaman/<int:id_peminjaman>", methods=["POST"])
def hapus_peminjaman(id_peminjaman):
    cur = mysql.connection.cursor()
    
    # Hapus data berdasarkan id_peminjaman
    cur.execute("DELETE FROM peminjaman WHERE id_peminjaman = %s", (id_peminjaman,))
    mysql.connection.commit()
    cur.close()
    
    # flash("Data peminjaman berhasil dihapus!", "success")
    return redirect(url_for("admin_peminjaman"))

@app.route("/daftar_buku")
def daftar_buku():
    cur = mysql.connection.cursor()

    # Ambil id_buku, judul_buku, dan genre dari tabel buku
    cur.execute("SELECT id_buku, judul_buku, genre FROM buku")
    buku_list = cur.fetchall()  # Mengambil semua hasil query
    cur.close()

    # Pass data buku ke template
    return render_template("daftar_buku.html", buku_list=buku_list)

@app.route("/edit_buku/<int:id_buku>", methods=["GET", "POST"])
def edit_buku(id_buku):
    cur = mysql.connection.cursor()

    if request.method == "POST":
        judul_buku = request.form['judul_buku']
        genre = request.form['genre']

        # Update data buku di database
        cur.execute("UPDATE buku SET judul_buku = %s, genre = %s WHERE id_buku = %s", 
                    (judul_buku, genre, id_buku))
        mysql.connection.commit()
        cur.close()
        return redirect(url_for("daftar_buku"))

    # Ambil data buku untuk diisi di form
    cur.execute("SELECT * FROM buku WHERE id_buku = %s", (id_buku,))
    buku = cur.fetchone()
    cur.close()
    return render_template("edit_buku.html", buku=buku)

@app.route("/hapus_buku/<int:id_buku>", methods=["POST"])
def hapus_buku(id_buku):
    cur = mysql.connection.cursor()

    # Hapus buku dari database
    cur.execute("DELETE FROM buku WHERE id_buku = %s", (id_buku,))
    mysql.connection.commit()
    cur.close()
    return redirect(url_for("daftar_buku"))

@app.route("/tambah_buku", methods=["GET", "POST"])
def tambah_buku():
    if request.method == "POST":
        judul_buku = request.form['judul_buku']
        genre = request.form['genre']

        # Insert data buku ke database
        cur = mysql.connection.cursor()
        cur.execute("INSERT INTO buku (judul_buku, genre) VALUES (%s, %s)", (judul_buku, genre))
        mysql.connection.commit()
        cur.close()
        return redirect(url_for("daftar_buku"))

    return render_template("tambah_buku.html")


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

@app.route("/petugas")
def petugas():
    cur = mysql.connection.cursor()

    # Query untuk mengambil semua data petugas
    cur.execute("SELECT id_petugas, nama_petugas, password FROM petugas")
    petugas_list = cur.fetchall()  # Mengambil semua hasil query
    cur.close()

    # Pass data petugas ke template
    return render_template("petugas.html", petugas_list=petugas_list)

@app.route("/tambah_petugas", methods=["GET", "POST"])
def tambah_petugas():
    if request.method == "POST":
        nama_petugas = request.form['nama_petugas']
        password = request.form['password']

        cur = mysql.connection.cursor()
        cur.execute("INSERT INTO petugas (nama_petugas, password) VALUES (%s, %s)", 
                    (nama_petugas, password))
        mysql.connection.commit()
        cur.close()

        return redirect(url_for("petugas"))  # Redirect kembali ke halaman petugas

    return render_template("tambah_petugas.html")

@app.route("/daftar_akun_user")
def daftar_akun_user():
    # Ambil data dari tabel peminjam
    cur = mysql.connection.cursor()
    cur.execute("SELECT id_peminjam, nama_peminjam, password FROM peminjam")
    peminjam_list = cur.fetchall()
    cur.close()

    # Pass data peminjam ke template
    return render_template("peminjam.html", peminjam_list=peminjam_list)



if __name__ == "__main__":
    app.run(debug=True)