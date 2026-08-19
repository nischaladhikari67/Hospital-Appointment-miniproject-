CREATE DATABASE IF NOT EXISTS hospital_db;
USE hospital_db;
-- Drop existing tables to refresh schema cleanly
DROP TABLE IF EXISTS appointments;
DROP TABLE IF EXISTS users;
-- Users table for Doctors and Admins
CREATE TABLE IF NOT EXISTS users (
    id INT AUTO_INCREMENT PRIMARY KEY,
    username VARCHAR(50) UNIQUE NOT NULL,
    password VARCHAR(255) NOT NULL,
    role ENUM('doctor', 'admin') NOT NULL,
    full_name VARCHAR(100) NOT NULL,
    specialty VARCHAR(100) DEFAULT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
-- Appointments table
CREATE TABLE IF NOT EXISTS appointments (
    id INT AUTO_INCREMENT PRIMARY KEY,
    patient_name VARCHAR(100) NOT NULL,
    patient_phone VARCHAR(20) NOT NULL,
    doctor_id INT NOT NULL,
    appointment_date DATE NOT NULL,
    appointment_time TIME NOT NULL,
    description TEXT,
    status ENUM('Scheduled', 'Completed', 'Cancelled') DEFAULT 'Scheduled',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (doctor_id) REFERENCES users(id) ON DELETE CASCADE
);
-- Optional: Insert sample doctors and admin user
INSERT INTO users (username, password, role, full_name, specialty)
VALUES (
        'admin',
        'admin123',
        'admin',
        'System Administrator',
        NULL
    ),
    (
        'dr_nikhil',
        'doc123',
        'doctor',
        'Dr. Nikhil',
        'Ophthalmologist'
    ),
    (
        'dr_nischal',
        'doc123',
        'doctor',
        'Dr. Nischal',
        'Psychologist'
    ),
    (
        'dr_tarjan',
        'doc123',
        'doctor',
        'Dr. Tarjan',
        'Gynecologist'
    ) ON DUPLICATE KEY
UPDATE username = username;