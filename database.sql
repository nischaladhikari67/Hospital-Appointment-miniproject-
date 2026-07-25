CREATE DATABASE IF NOT EXISTS hospital_db;
USE hospital_db;

CREATE TABLE IF NOT EXISTS appointments (
    id INT AUTO_INCREMENT PRIMARY KEY,
    patient_name VARCHAR(100) NOT NULL,
    doctor_name VARCHAR(100) NOT NULL,
    appointment_date DATE NOT NULL,
    appointment_time TIME NOT NULL,
    status VARCHAR(20) DEFAULT 'Scheduled',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Sample Data
INSERT INTO appointments (patient_name, doctor_name, appointment_date, appointment_time) 
VALUES 
('Sarah Jenkins', 'Dr. Smith (Cardiology)', '2026-07-28', '10:30:00'),
('David Lee', 'Dr. Patel (Dermatology)', '2026-07-29', '14:00:00');