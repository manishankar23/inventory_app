from flask import Flask, render_template, request, redirect, url_for
import sqlite3
from datetime import datetime

app = Flask(__name__)
DATABASE = 'inventory.db'

# ---- Database Connection ----
def get_db_connection():
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    return conn

# ---- Create Tables ----
def init_db():
    conn = get_db_connection()
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS Product (
                    product_id TEXT PRIMARY KEY,
                    name TEXT NOT NULL
                )''')
    c.execute('''CREATE TABLE IF NOT EXISTS Location (
                    location_id TEXT PRIMARY KEY,
                    name TEXT NOT NULL
                )''')
    c.execute('''CREATE TABLE IF NOT EXISTS ProductMovement (
                    movement_id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp TEXT,
                    from_location TEXT,
                    to_location TEXT,
                    product_id TEXT,
                    qty INTEGER
                )''')
    conn.commit()
    conn.close()

init_db()

# ---- Product Routes ----
@app.route('/products', methods=['GET', 'POST'])
def products():
    conn = get_db_connection()
    if request.method == 'POST':
        pid = request.form['product_id']
        name = request.form['name']
        conn.execute("INSERT INTO Product (product_id, name) VALUES (?, ?)", (pid, name))
        conn.commit()
        return redirect(url_for('products'))
    products = conn.execute("SELECT * FROM Product").fetchall()
    conn.close()
    return render_template('products.html', products=products)

# ---- Location Routes ----
@app.route('/locations', methods=['GET', 'POST'])
def locations():
    conn = get_db_connection()
    if request.method == 'POST':
        lid = request.form['location_id']
        name = request.form['name']
        conn.execute("INSERT INTO Location (location_id, name) VALUES (?, ?)", (lid, name))
        conn.commit()
        return redirect(url_for('locations'))
    locations = conn.execute("SELECT * FROM Location").fetchall()
    conn.close()
    return render_template('locations.html', locations=locations)

# ---- Product Movements ----
@app.route('/movements', methods=['GET', 'POST'])
def movements():
    conn = get_db_connection()
    if request.method == 'POST':
        product_id = request.form['product_id']
        from_loc = request.form['from_location'] or None
        to_loc = request.form['to_location'] or None
        qty = int(request.form['qty'])
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        conn.execute('''INSERT INTO ProductMovement (timestamp, from_location, to_location, product_id, qty)
                        VALUES (?, ?, ?, ?, ?)''', (timestamp, from_loc, to_loc, product_id, qty))
        conn.commit()
        return redirect(url_for('movements'))

    movements = conn.execute("SELECT * FROM ProductMovement").fetchall()
    products = conn.execute("SELECT * FROM Product").fetchall()
    locations = conn.execute("SELECT * FROM Location").fetchall()
    conn.close()
    return render_template('movements.html', movements=movements, products=products, locations=locations)

# ---- Report ----
@app.route('/report')
def report():
    conn = get_db_connection()
    query = '''
        SELECT 
            p.name AS product,
            l.name AS location,
            IFNULL(SUM(
                CASE WHEN pm.to_location = l.location_id THEN pm.qty ELSE 0 END
                - CASE WHEN pm.from_location = l.location_id THEN pm.qty ELSE 0 END
            ), 0) AS balance
        FROM Product p
        CROSS JOIN Location l
        LEFT JOIN ProductMovement pm ON p.product_id = pm.product_id
        GROUP BY p.product_id, l.location_id
    '''
    report_data = conn.execute(query).fetchall()
    conn.close()
    return render_template('report.html', report_data=report_data)

# ---- Home ----
@app.route('/')
def index():
    return render_template('base.html')

if __name__ == '__main__':
    app.run(debug=True)
