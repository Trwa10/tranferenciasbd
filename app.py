
import os
from flask import Flask, render_template, request, redirect, url_for, session
from werkzeug.utils import secure_filename
from dotenv import load_dotenv
import pandas as pd
import xmlrpc.client
import json
import datetime

# Load environment variables
load_dotenv()

ODOO_URL = os.getenv("ODOO_URL")
ODOO_DB = os.getenv("ODOO_DB")
ODOO_USER = os.getenv("ODOO_USER")
ODOO_PASSWORD = os.getenv("ODOO_PASSWORD")
SECRET_KEY = os.getenv("SECRET_KEY", "supersecretkey")

# Flask setup
app = Flask(__name__)
app.secret_key = SECRET_KEY
app.config["UPLOAD_FOLDER"] = "uploads"
app.config["LOG_FOLDER"] = "logs"
os.makedirs(app.config["UPLOAD_FOLDER"], exist_ok=True)
os.makedirs(app.config["LOG_FOLDER"], exist_ok=True)

# Odoo connection
common = xmlrpc.client.ServerProxy(f"{ODOO_URL}/xmlrpc/2/common")
uid = common.authenticate(ODOO_DB, ODOO_USER, ODOO_PASSWORD, {})
models = xmlrpc.client.ServerProxy(f"{ODOO_URL}/xmlrpc/2/object")

# Load users
with open("usuarios.json") as f:
    usuarios = json.load(f)

@app.route("/", methods=["GET", "POST"])
def login():
    if "user" in session:
        return redirect(url_for("dashboard"))
    error = None
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]
        if username in usuarios and usuarios[username] == password:
            session["user"] = username
            return redirect(url_for("dashboard"))
        error = "Credenciales incorrectas"
    return render_template("login.html", error=error)

@app.route("/logout")
def logout():
    session.pop("user", None)
    return redirect(url_for("login"))

@app.route("/dashboard", methods=["GET", "POST"])
def dashboard():
    if "user" not in session:
        return redirect(url_for("login"))
    logs = []
    if request.method == "POST":
        files = request.files.getlist("files")
        for file in files:
            if file and file.filename.endswith(".txt"):
                filename = secure_filename(file.filename)
                filepath = os.path.join(app.config["UPLOAD_FOLDER"], filename)
                file.save(filepath)
                result = procesar_archivo(filepath, session["user"])
                logs.append((filename, result))
    return render_template("dashboard.html", logs=logs, user=session["user"])

def procesar_archivo(filepath, usuario):
    nombre = os.path.basename(filepath)
    log_lines = []
    try:
        df = pd.read_csv(filepath, sep=";", encoding="latin-1", dtype=str)
        grupo = df.groupby("NBR_CLIENTE")
        for cliente, items in grupo:
            picking_id = models.execute_kw(ODOO_DB, uid, ODOO_PASSWORD,
                'stock.picking', 'create', [{
                    'picking_type_id': 1,
                    'location_id': 18,
                    'location_dest_id': 18,
                    'origin': f"Auto-importación {cliente}",
                }])
            for _, row in items.iterrows():
                cod = str(row['COD_BARRA']).strip().replace(" ", "").replace("-", "")
                qty = float(row['CANTIDAD'])
                productos = models.execute_kw(ODOO_DB, uid, ODOO_PASSWORD,
                    'product.product', 'search_read',
                    [[['barcode', '=', cod]]],
                    {'fields': ['id', 'uom_id'], 'limit': 1})
                if not productos:
                    productos = models.execute_kw(ODOO_DB, uid, ODOO_PASSWORD,
                        'product.product', 'search_read',
                        [[['default_code', '=', cod]]],
                        {'fields': ['id', 'uom_id'], 'limit': 1})
                if not productos:
                    log_lines.append(f"❌ Producto no encontrado: {cod}")
                    continue
                prod = productos[0]
                models.execute_kw(ODOO_DB, uid, ODOO_PASSWORD,
                    'stock.move', 'create', [[{
                        'name': row['DESCRIPCION'],
                        'product_id': prod['id'],
                        'product_uom_qty': qty,
                        'product_uom': prod['uom_id'][0],
                        'picking_id': picking_id,
                        'location_id': 18,
                        'location_dest_id': 18,
                    }]])
            log_lines.append(f"✅ Transferencia creada ID {picking_id} para {cliente}")
        os.remove(filepath)
        today = datetime.date.today().isoformat()
        log_file = f"{today}_{usuario}_{nombre}.log"
        log_path = os.path.join(app.config["LOG_FOLDER"], log_file)
        with open(log_path, "w", encoding="utf-8") as f:
            f.write("\n".join(log_lines))
        return "Procesado correctamente"
    except Exception as e:
        return f"❌ Error: {e}"

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
