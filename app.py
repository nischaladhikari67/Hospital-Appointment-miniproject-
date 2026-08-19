from flask import Flask, render_template, request, jsonify, session, redirect, url_for
import os
import mysql.connector

app = Flask(__name__)
app.secret_key = 'ntn_healthcare_super_secret_key'

DB_CONFIG = {
    'host': os.getenv('MYSQLHOST', 'mysql.railway.internal'),
    'user': os.getenv('MYSQLUSER', 'root'),
    'password': os.getenv('MYSQLPASSWORD', 'wbUgtxPCaUHldIJIpLUCIzRJtdQiEAwt'),
    'database': os.getenv('MYSQLDATABASE', 'hospital_db'),
    'port': int(os.getenv('MYSQLPORT', 3306))
}

def get_db():
    return mysql.connector.connect(**DB_CONFIG)

# --- Routes ---

@app.route('/')
def home():
    # Public Landing Page & Patient Booking
    return render_template('index.html')

@app.route('/staff-portal')
def staff_portal():
    # Login & Registration Page for Doctors & Admins
    return render_template('login.html')

@app.route('/doctor')
def doctor_page():
    if session.get('role') != 'doctor':
        return redirect('/staff-portal')
    return render_template('doctor_dashboard.html', user=session)

@app.route('/admin')
def admin_page():
    if session.get('role') != 'admin':
        return redirect('/staff-portal')
    return render_template('admin_dashboard.html', user=session)

# --- Public APIs ---

@app.route('/api/doctors', methods=['GET'])
def get_public_doctors():
    conn = get_db()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT id, full_name, specialty FROM users WHERE role = 'doctor'")
    doctors = cursor.fetchall()
    cursor.close()
    conn.close()
    return jsonify({'status': 'success', 'data': doctors})

@app.route('/api/patient/book', methods=['POST'])
def public_book_appointment():
    data = request.json or {}
    conn = get_db()
    cursor = conn.cursor(dictionary=True)
    
    # 1. Determine the doctor_id securely
    doctor_id = data.get('doctor_id')
    
    # Fallback: If frontend sent 'doctor_name' instead of 'doctor_id'
    if not doctor_id and 'doctor_name' in data:
        cursor.execute("SELECT id FROM users WHERE full_name LIKE %s AND role = 'doctor' LIMIT 1", (f"%{data['doctor_name']}%",))
        doc_res = cursor.fetchone()
        if doc_res:
            doctor_id = doc_res['id']

    # Default fallback to first doctor in DB if still not found
    if not doctor_id:
        cursor.execute("SELECT id FROM users WHERE role = 'doctor' LIMIT 1")
        first_doc = cursor.fetchone()
        doctor_id = first_doc['id'] if first_doc else 2

    # 2. Insert into appointments table safely
    cursor.execute("""
        INSERT INTO appointments (patient_name, patient_phone, doctor_id, appointment_date, appointment_time, description)
        VALUES (%s, %s, %s, %s, %s, %s)
    """, (
        data.get('patient_name', ''),
        data.get('patient_phone', ''),
        doctor_id,
        data.get('appointment_date', ''),
        data.get('appointment_time', ''),
        data.get('description', '')
    ))
    
    conn.commit()
    cursor.close()
    conn.close()
    return jsonify({'status': 'success', 'message': 'Appointment booked successfully!'})

# --- Staff Authentication APIs ---

@app.route('/api/auth/register', methods=['POST'])
def register_staff():
    data = request.json or {}
    conn = get_db()
    cursor = conn.cursor()
    try:
        cursor.execute("""
            INSERT INTO users (username, password, role, full_name, specialty)
            VALUES (%s, %s, %s, %s, %s)
        """, (
            data.get('username'),
            data.get('password'),
            data.get('role'),
            data.get('full_name'),
            data.get('specialty', None)
        ))
        conn.commit()
        return jsonify({'status': 'success', 'message': 'Account registered successfully!'})
    except mysql.connector.Error as err:
        return jsonify({'status': 'error', 'message': 'Username already exists or database error.'}), 400
    finally:
        cursor.close()
        conn.close()

@app.route('/api/auth/login', methods=['POST'])
def login_staff():
    data = request.json or {}
    conn = get_db()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("""
        SELECT * FROM users WHERE username = %s AND password = %s AND role = %s
    """, (data.get('username'), data.get('password'), data.get('role')))
    user = cursor.fetchone()
    cursor.close()
    conn.close()

    if user:
        session['user_id'] = user['id']
        session['username'] = user['username']
        session['full_name'] = user['full_name']
        session['role'] = user['role']
        session['specialty'] = user.get('specialty', '')
        return jsonify({'status': 'success', 'role': user['role']})
    
    return jsonify({'status': 'error', 'message': 'Invalid credentials or role selection'}), 401

@app.route('/api/auth/logout', methods=['GET', 'POST'])
def logout_staff():
    session.clear()
    if request.method == 'GET' or request.headers.get('Accept', '').find('text/html') != -1:
        return redirect('/staff-portal')
    return jsonify({'status': 'success', 'redirect': '/staff-portal'})

# --- Doctor CRUD APIs ---

@app.route('/api/doctor/appointments', methods=['GET'])
def get_doctor_appointments():
    if session.get('role') != 'doctor':
        return jsonify({'status': 'error', 'message': 'Unauthorized'}), 401
    
    conn = get_db()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("""
        SELECT a.id, a.patient_name, a.patient_phone, u.full_name as doctor_name, 
               DATE_FORMAT(a.appointment_date, '%Y-%m-%d') as appointment_date, 
               TIME_FORMAT(a.appointment_time, '%H:%i') as appointment_time, a.description, a.status 
        FROM appointments a
        JOIN users u ON a.doctor_id = u.id
        WHERE a.doctor_id = %s 
        ORDER BY a.appointment_date ASC, a.appointment_time ASC
    """, (session['user_id'],))
    data = cursor.fetchall()
    cursor.close()
    conn.close()
    return jsonify({'status': 'success', 'data': data})

@app.route('/api/appointments/<int:app_id>', methods=['PUT'])
def update_appointment(app_id):
    if session.get('role') not in ['doctor', 'admin']:
        return jsonify({'status': 'error', 'message': 'Unauthorized'}), 401
    
    data = request.json or {}
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("""
        UPDATE appointments 
        SET appointment_date = %s, appointment_time = %s, status = %s, description = %s
        WHERE id = %s
    """, (data.get('appointment_date'), data.get('appointment_time'), data.get('status'), data.get('description'), app_id))
    conn.commit()
    cursor.close()
    conn.close()
    return jsonify({'status': 'success', 'message': 'Appointment updated!'})

@app.route('/api/appointments/<int:app_id>', methods=['DELETE'])
def delete_appointment(app_id):
    if session.get('role') not in ['doctor', 'admin']:
        return jsonify({'status': 'error', 'message': 'Unauthorized'}), 401
    
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM appointments WHERE id = %s", (app_id,))
    conn.commit()
    cursor.close()
    conn.close()
    return jsonify({'status': 'success', 'message': 'Appointment removed!'})

# --- Admin Monitoring APIs ---

@app.route('/api/admin/metrics', methods=['GET'])
def get_admin_metrics():
    if session.get('role') != 'admin':
        return jsonify({'status': 'error', 'message': 'Unauthorized'}), 401
    
    conn = get_db()
    cursor = conn.cursor(dictionary=True)
    
    cursor.execute("SELECT COUNT(*) as total FROM appointments")
    total_apps = cursor.fetchone()['total']
    
    cursor.execute("SELECT COUNT(*) as total FROM users WHERE role = 'doctor'")
    total_doctors = cursor.fetchone()['total']
    
    cursor.execute("SELECT status, COUNT(*) as count FROM appointments GROUP BY status")
    status_counts = cursor.fetchall()
    
    cursor.execute("""
        SELECT u.full_name as doctor_name, COUNT(a.id) as count 
        FROM users u 
        LEFT JOIN appointments a ON u.id = a.doctor_id 
        WHERE u.role = 'doctor' 
        GROUP BY u.id, u.full_name
    """)
    doctor_counts = cursor.fetchall()

    cursor.execute("""
        SELECT a.id, a.patient_name, a.patient_phone, u.full_name as doctor_name, 
               DATE_FORMAT(a.appointment_date, '%Y-%m-%d') as appointment_date, 
               TIME_FORMAT(a.appointment_time, '%H:%i') as appointment_time, a.status, a.description
        FROM appointments a
        JOIN users u ON a.doctor_id = u.id
        ORDER BY a.id DESC
    """)
    all_appointments = cursor.fetchall()

    cursor.close()
    conn.close()
    
    return jsonify({
        'status': 'success',
        'metrics': {
            'total_appointments': total_apps,
            'total_doctors': total_doctors
        },
        'status_counts': status_counts,
        'doctor_counts': doctor_counts,
        'appointments': all_appointments
    })

import os

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
