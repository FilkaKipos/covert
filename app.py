from flask import Flask, render_template, request, jsonify
import requests
import sqlite3
from datetime import datetime

app = Flask(__name__)

def get_exchange_rates():
    url = "https://api.exchangeratesapi.io/latest"
    access_key = 'ad4d7785758dc6853db933df124d2d31'
    response = requests.get(f"{url}?access_key={access_key}")
    data = response.json()

    return data


def save_exchange_rates(rates):
    conn = sqlite3.connect('currency.db')
    cursor = conn.cursor()
    cursor.execute('''CREATE TABLE IF NOT EXISTS exchange_rates
                      (currency TEXT, rate REAL, last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP)''')
    for currency, rate in rates.items():
        cursor.execute('INSERT INTO exchange_rates (currency, rate) VALUES (?, ?)', (currency, rate))
    conn.commit()
    conn.close()

def get_last_update():
    conn = sqlite3.connect('currency.db')
    cursor = conn.cursor()
    cursor.execute('SELECT last_updated FROM exchange_rates ORDER BY last_updated DESC LIMIT 1')
    last_update = cursor.fetchone()
    conn.close()
    return last_update[0] if last_update else "Data not found"

def convert_currency(from_currency, to_currency, amount):
    conn = sqlite3.connect('currency.db')
    cursor = conn.cursor()
    cursor.execute('SELECT rate FROM exchange_rates WHERE currency = ?', (from_currency,))
    from_rate = cursor.fetchone()
    cursor.execute('SELECT rate FROM exchange_rates WHERE currency = ?', (to_currency,))
    to_rate = cursor.fetchone()
    conn.close()

    if not from_rate or not to_rate:
        return "Currency not found"

    conversion_rate = to_rate[0] / from_rate[0]
    return amount * conversion_rate

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/update_rates', methods=['POST'])
def update_rates():
    data = get_exchange_rates()
    save_exchange_rates(data['rates'])
    return jsonify({"message": "Rates updated successfully"})

@app.route('/last_update', methods=['GET'])
def last_update():
    last_update = get_last_update()
    return jsonify({"last_update": last_update})

@app.route('/convert', methods=['POST'])
def convert():
    from_currency = request.form['from_currency']
    to_currency = request.form['to_currency']
    amount = float(request.form['amount'])
    result = convert_currency(from_currency, to_currency, amount)
    return jsonify({"result": result})

if __name__ == '__main__':
    app.run(debug=True)
