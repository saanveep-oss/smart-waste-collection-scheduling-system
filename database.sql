CREATE DATABASE IF NOT EXISTS smart_waste;

USE smart_waste;

CREATE TABLE areas (
    area_id INT PRIMARY KEY AUTO_INCREMENT,
    area_name VARCHAR(100) NOT NULL
);

CREATE TABLE users (
    user_id INT PRIMARY KEY AUTO_INCREMENT,
    name VARCHAR(100),
    email VARCHAR(100) UNIQUE,
    password VARCHAR(100),
    phone VARCHAR(15),
    area_id INT,
    participation_score INT DEFAULT 0,
    FOREIGN KEY(area_id) REFERENCES areas(area_id)
);

CREATE TABLE schedules (
    schedule_id INT PRIMARY KEY AUTO_INCREMENT,
    area_id INT,
    collection_day VARCHAR(20),
    time_slot VARCHAR(30),
    FOREIGN KEY(area_id) REFERENCES areas(area_id)
);

CREATE TABLE collections (
    collection_id INT PRIMARY KEY AUTO_INCREMENT,
    user_id INT,
    schedule_id INT,
    status VARCHAR(20),
    collection_date DATE,
    FOREIGN KEY(user_id) REFERENCES users(user_id),
    FOREIGN KEY(schedule_id) REFERENCES schedules(schedule_id)
);

CREATE TABLE pickup_requests (
    request_id INT PRIMARY KEY AUTO_INCREMENT,
    user_id INT,
    request_date DATE,
    waste_type VARCHAR(50),
    priority_status VARCHAR(20),
    status VARCHAR(20),
    FOREIGN KEY(user_id) REFERENCES users(user_id)
);