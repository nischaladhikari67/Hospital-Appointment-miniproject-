# app.py
from flask import Flask, render_template, request, jsonify
import mysql.connector

app = Flask(__name__)

DB_CONFIG = {
    'host': 'localhost',
    'user': 'root',
    'password': 'strongpassword@#',
    'database': 'hospital_db'
}

def get_db_connection():
    return mysql.connector.connect(**DB_CONFIG)

# --- Page Navigation Routes ---

@app.route('/')
def index_page():
    return render_template('index.html')

@app.route('/book')
def book_page():
    return render_template('book.html')

@app.route('/view')
def view_page():
    return render_template('view.html')

# --- API Endpoints ---

@app.route('/api/appointments', methods=['GET'])
def get_appointments():
    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        query = """
            SELECT id, patient_name, doctor_name, 
                   DATE_FORMAT(appointment_date, '%Y-%m-%d') as appointment_date, 
                   TIME_FORMAT(appointment_time, '%H:%i') as appointment_time, 
                   description, status 
            FROM appointments 
            ORDER BY appointment_date, appointment_time
        """
        cursor.execute(query)
        appointments = cursor.fetchall()
        cursor.close()
        conn.close()
        return jsonify({'status': 'success', 'data': appointments})
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500

@app.route('/api/appointments', methods=['POST'])
def create_appointment():
    try:
        data = request.json
        conn = get_db_connection()
        cursor = conn.cursor()
        query = """
            INSERT INTO appointments (patient_name, doctor_name, appointment_date, appointment_time, description)
            VALUES (%s, %s, %s, %s, %s)
        """
        values = (
            data['patient_name'], 
            data['doctor_name'], 
            data['appointment_date'], 
            data['appointment_time'],
            data.get('description', '')
        )
        cursor.execute(query, values)
        conn.commit()
        cursor.close()
        conn.close()
        return jsonify({'status': 'success', 'message': 'Appointment booked successfully!'}), 201
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500

@app.route('/api/appointments/<int:app_id>/status', methods=['PUT'])
def update_status(app_id):
    try:
        new_status = request.json.get('status')
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("UPDATE appointments SET status = %s WHERE id = %s", (new_status, app_id))
        conn.commit()
        cursor.close()
        conn.close()
        return jsonify({'status': 'success', 'message': f'Status updated to {new_status}!'})
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500

@app.route('/api/appointments/<int:app_id>', methods=['DELETE'])
def cancel_appointment(app_id):
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("DELETE FROM appointments WHERE id = %s", (app_id,))
        conn.commit()
        cursor.close()
        conn.close()
        return jsonify({'status': 'success', 'message': 'Appointment deleted!'})
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True, port=5000)