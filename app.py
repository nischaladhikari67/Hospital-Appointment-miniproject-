from flask import Flask, render_template, request, jsonify, session, redirect, url_for
import mysql.connector

app = Flask(__name__)
app.secret_key = 'ntn_healthcare_super_secret_key'

DB_CONFIG = {
    'host': 'localhost',
    'user': 'root',
    'password': 'strongpassword@#',  # Update with your MySQL password
    'database': 'hospital_db'
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

# --- Patient Public Booking API ---

@app.route('/api/patient/book', methods=['POST'])
def public_book_appointment():
    data = request.json
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO appointments (patient_name, patient_phone, doctor_name, appointment_date, appointment_time, description)
        VALUES (%s, %s, %s, %s, %s, %s)
    """, (
        data['patient_name'],
        data.get('patient_phone', ''),
        data['doctor_name'],
        data['appointment_date'],
        data['appointment_time'],
        data.get('description', '')
    ))
    conn.commit()
    cursor.close()
    conn.close()
    return jsonify({'status': 'success', 'message': 'Appointment booked successfully!'})

# --- Staff Authentication APIs ---

@app.route('/api/auth/register', methods=['POST'])
def register_staff():
    data = request.json
    conn = get_db()
    cursor = conn.cursor()
    try:
        cursor.execute("""
            INSERT INTO users (username, password, role, full_name, specialty)
            VALUES (%s, %s, %s, %s, %s)
        """, (
            data['username'],
            data['password'],
            data['role'],
            data['full_name'],
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
    data = request.json
    conn = get_db()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("""
        SELECT * FROM users WHERE username = %s AND password = %s AND role = %s
    """, (data['username'], data['password'], data['role']))
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

@app.route('/api/auth/logout', methods=['POST'])
def logout_staff():
    session.clear()
    return jsonify({'status': 'success'})

# --- Doctor CRUD APIs ---

@app.route('/api/doctor/appointments', methods=['GET'])
def get_doctor_appointments():
    if session.get('role') != 'doctor':
        return jsonify({'status': 'error', 'message': 'Unauthorized'}), 401
    
    doc_filter = f"%{session['full_name']}%"
    conn = get_db()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("""
        SELECT id, patient_name, patient_phone, doctor_name, 
               DATE_FORMAT(appointment_date, '%Y-%m-%d') as appointment_date, 
               TIME_FORMAT(appointment_time, '%H:%i') as appointment_time, description, status 
        FROM appointments WHERE doctor_name LIKE %s ORDER BY appointment_date ASC, appointment_time ASC
    """, (doc_filter,))
    data = cursor.fetchall()
    cursor.close()
    conn.close()
    return jsonify({'status': 'success', 'data': data})

@app.route('/api/appointments/<int:app_id>', methods=['PUT'])
def update_appointment(app_id):
    if session.get('role') not in ['doctor', 'admin']:
        return jsonify({'status': 'error', 'message': 'Unauthorized'}), 401
    
    data = request.json
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("""
        UPDATE appointments 
        SET appointment_date = %s, appointment_time = %s, status = %s, description = %s
        WHERE id = %s
    """, (data['appointment_date'], data['appointment_time'], data['status'], data['description'], app_id))
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
    
    cursor.execute("SELECT doctor_name, COUNT(*) as count FROM appointments GROUP BY doctor_name")
    doctor_counts = cursor.fetchall()

    cursor.execute("""
        SELECT id, patient_name, patient_phone, doctor_name, 
               DATE_FORMAT(appointment_date, '%Y-%m-%d') as appointment_date, 
               TIME_FORMAT(appointment_time, '%H:%i') as appointment_time, status, description
        FROM appointments ORDER BY id DESC
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

if __name__ == '__main__':
    app.run(debug=True, port=5000)