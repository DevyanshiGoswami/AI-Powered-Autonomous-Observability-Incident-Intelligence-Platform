from flask import Flask, jsonify
import sqlite3

app = Flask(__name__)

@app.route("/incidents")
def get_incidents():

    conn = sqlite3.connect("incidents.db")
    cursor = conn.cursor()

    cursor.execute("""
    SELECT timestamp, service, risk, causes
    FROM incidents
    ORDER BY id DESC
    LIMIT 20
    """)

    rows = cursor.fetchall()

    incidents = []

    for row in rows:
        incidents.append({
            "timestamp": row[0],
            "service": row[1],
            "risk": row[2],
            "causes": row[3]
        })

    return jsonify(incidents)


if __name__ == "__main__":
    app.run(port=5050)