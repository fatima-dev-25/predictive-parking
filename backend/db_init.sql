CREATE DATABASE IF NOT EXISTS parking_db;
USE parking_db;

-- Users
CREATE TABLE IF NOT EXISTS users (
  id INT AUTO_INCREMENT PRIMARY KEY,
  name VARCHAR(100),
  email VARCHAR(100) UNIQUE,
  password_hash VARCHAR(255),
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
) ENGINE=InnoDB;

-- Parking lots
CREATE TABLE IF NOT EXISTS parking_lots (
  id INT AUTO_INCREMENT PRIMARY KEY,
  name VARCHAR(255),
  address VARCHAR(255),
  latitude DOUBLE,
  longitude DOUBLE,
  total_slots INT,
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
) ENGINE=InnoDB;

-- Parking slots (individual slots)
CREATE TABLE IF NOT EXISTS parking_slots (
  id INT AUTO_INCREMENT PRIMARY KEY,
  parking_lot_id INT,
  slot_number VARCHAR(50),
  slot_type VARCHAR(50),
  is_occupied BOOLEAN DEFAULT FALSE,
  updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  FOREIGN KEY (parking_lot_id) REFERENCES parking_lots(id) ON DELETE CASCADE
) ENGINE=InnoDB;

-- Bookings
CREATE TABLE IF NOT EXISTS bookings (
  id INT AUTO_INCREMENT PRIMARY KEY,
  user_id INT,
  slot_id INT,
  parking_lot_id INT,
  start_time DATETIME,
  end_time DATETIME,
  status VARCHAR(50), -- reserved / active / completed / cancelled
  payment_status VARCHAR(50) DEFAULT 'pending',
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  FOREIGN KEY (slot_id) REFERENCES parking_slots(id),
  FOREIGN KEY (parking_lot_id) REFERENCES parking_lots(id)
) ENGINE=InnoDB;

-- Occupancy history (for predictions)
CREATE TABLE IF NOT EXISTS occupancy_history (
  id INT AUTO_INCREMENT PRIMARY KEY,
  parking_lot_id INT,
  timestamp DATETIME,
  occupied_count INT,
  free_count INT,
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  INDEX (parking_lot_id),
  FOREIGN KEY (parking_lot_id) REFERENCES parking_lots(id)
) ENGINE=InnoDB;

-- Seed 3 parking lots (change coords to local ones if you want)
INSERT INTO parking_lots (name, address, latitude, longitude, total_slots)
VALUES
('Central Mall Parking', 'Central Mall, City', 12.9716, 77.5946, 30),
('Station Plaza Parking', 'Near Main Station', 12.9750, 77.5938, 20),
('Office Complex Parking', 'Tech Park', 12.9666, 77.5800, 25);

-- Create slots per lot
-- For simplicity create numbered slots
INSERT INTO parking_slots (parking_lot_id, slot_number, slot_type) 
SELECT l.id, CONCAT('S', n), 'car' FROM parking_lots l
JOIN (
  SELECT 1 AS n UNION ALL SELECT 2 UNION ALL SELECT 3 UNION ALL SELECT 4 UNION ALL SELECT 5
  UNION ALL SELECT 6 UNION ALL SELECT 7 UNION ALL SELECT 8 UNION ALL SELECT 9 UNION ALL SELECT 10
  UNION ALL SELECT 11 UNION ALL SELECT 12 UNION ALL SELECT 13 UNION ALL SELECT 14 UNION ALL SELECT 15
  UNION ALL SELECT 16 UNION ALL SELECT 17 UNION ALL SELECT 18 UNION ALL SELECT 19 UNION ALL SELECT 20
  UNION ALL SELECT 21 UNION ALL SELECT 22 UNION ALL SELECT 23 UNION ALL SELECT 24 UNION ALL SELECT 25
  UNION ALL SELECT 26 UNION ALL SELECT 27 UNION ALL SELECT 28 UNION ALL SELECT 29 UNION ALL SELECT 30
) nums
WHERE nums.n <= l.total_slots;

