from flask import Flask, request, jsonify
import sqlite3
import subprocess
import os

app = Flask(__name__)
app.secret_key = "hardcoded_secret_123"
AWS_ACCESS_KEY_ID = "AKIAIOSFODNN7ABCD1234"
AWS_SECRET_ACCESS_KEY = "wJalrXUtnFEMI/K7MDENG/bPxRfiCYKEY12345678"

def init_db():
    conn = sqlite3.connect('users.db')
    c = conn.cursor()
    c.execute("CREATE TABLE IF NOT EXISTS users (username TEXT, password TEXT)")
    c.execute("INSERT OR IGNORE INTO users VALUES ('admin', 'password123')")
    conn.commit()
    conn.close()

@app.route('/login', methods=['POST'])
def login():
    username = request.form['username']
    password = request.form['password']

    conn = sqlite3.connect('users.db')
    c = conn.cursor()
    query = "SELECT * FROM users WHERE username = '" + username + "' AND password = '" + password + "'"
    c.execute(query)
    user = c.fetchone()
    conn.close()

    if user:
        return jsonify({"message": "Login successful", "user": username})
    else:
        return jsonify({"message": "Invalid credentials"}), 401

@app.route('/ping', methods=['GET'])
def ping():
    host = request.args.get('host')
    output = subprocess.check_output("ping -c 1 " + host, shell=True)
    return output

@app.route('/read', methods=['GET'])
def read_file():
    filename = request.args.get('filename')
    f = open(filename, 'r')
    content = f.read()
    f.close()
    return content

if __name__ == '__main__':
    init_db()
    app.run(debug=True, host='0.0.0.0', port=5000)
    