-- Database: dgcsxy
CREATE DATABASE IF NOT EXISTS dgcsxy DEFAULT CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci;
USE dgcsxy;

-- Teacher (班主任) table
CREATE TABLE IF NOT EXISTS teacher (
  id INT PRIMARY KEY AUTO_INCREMENT,
  username VARCHAR(50) NOT NULL UNIQUE,
  password VARCHAR(255) NOT NULL COMMENT 'PBKDF2 摘要，非明文',
  name VARCHAR(50) DEFAULT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- Student table (可选，用于统计总人数)
CREATE TABLE IF NOT EXISTS student (
  id INT PRIMARY KEY AUTO_INCREMENT,
  student_no VARCHAR(20) NOT NULL UNIQUE,
  student_name VARCHAR(50) NOT NULL,
  class_name VARCHAR(50) DEFAULT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- Attendance record table
CREATE TABLE IF NOT EXISTS attendance_record (
  id INT PRIMARY KEY AUTO_INCREMENT,
  student_no VARCHAR(20) NOT NULL,
  student_name VARCHAR(50) NOT NULL,
  `date` DATE NOT NULL,
  status VARCHAR(10) NOT NULL DEFAULT '正常',
  time VARCHAR(20) DEFAULT '',
  remark VARCHAR(200) DEFAULT '',
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  INDEX idx_date (`date`),
  INDEX idx_status (status),
  INDEX idx_student_no (student_no)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- Demo data
-- 演示账号 admin / admin123（此处存的是 PBKDF2 摘要，不是明文口令）
INSERT IGNORE INTO teacher(username, password, name) VALUES
  ('admin','pbkdf2:sha256:600000$sUmOlDAszVFkctRf$6db31d31d560e2b5495339d1f3aa01f11b80c8e16d7d012e7eb523483bea8c4a','班主任');

INSERT IGNORE INTO student(student_no, student_name, class_name) VALUES
('20250001','李雷','一(1)班'),
('20250002','韩梅梅','一(1)班'),
('20250003','张伟','一(1)班'),
('20250004','王芳','一(1)班'),
('20250005','赵敏','一(1)班');

-- Last 7 days demo attendance (partial)
INSERT INTO attendance_record(student_no, student_name, `date`, status, time, remark) VALUES
('20250001','李雷', CURDATE(), '迟到', '08:05', '堵车'),
('20250002','韩梅梅', CURDATE(), '请假', '全天', '病假'),
('20250003','张伟', CURDATE(), '正常', '07:55', ''),
('20250004','王芳', CURDATE(), '旷课', '--', '未说明'),
('20250005','赵敏', CURDATE(), '正常', '07:50', ''),
('20250001','李雷', DATE_SUB(CURDATE(), INTERVAL 1 DAY), '正常', '07:55', ''),
('20250002','韩梅梅', DATE_SUB(CURDATE(), INTERVAL 1 DAY), '正常', '07:58', ''),
('20250003','张伟', DATE_SUB(CURDATE(), INTERVAL 1 DAY), '迟到', '08:02', ''),
('20250004','王芳', DATE_SUB(CURDATE(), INTERVAL 1 DAY), '正常', '07:56', ''),
('20250005','赵敏', DATE_SUB(CURDATE(), INTERVAL 1 DAY), '请假', '全天', '事假'),
('20250001','李雷', DATE_SUB(CURDATE(), INTERVAL 2 DAY), '正常', '07:54', ''),
('20250002','韩梅梅', DATE_SUB(CURDATE(), INTERVAL 2 DAY), '正常', '07:57', ''),
('20250003','张伟', DATE_SUB(CURDATE(), INTERVAL 2 DAY), '正常', '07:55', ''),
('20250004','王芳', DATE_SUB(CURDATE(), INTERVAL 2 DAY), '旷课', '--', ''),
('20250005','赵敏', DATE_SUB(CURDATE(), INTERVAL 2 DAY), '正常', '07:52', '');
