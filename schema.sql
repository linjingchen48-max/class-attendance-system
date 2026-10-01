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

-- Student table 学生名册：应到人数、考勤录入选人都以它为准
CREATE TABLE IF NOT EXISTS student (
  id INT PRIMARY KEY AUTO_INCREMENT,
  student_no VARCHAR(20) NOT NULL UNIQUE,
  student_name VARCHAR(50) NOT NULL,
  class_name VARCHAR(50) DEFAULT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- Attendance record table
-- student_name 是录入当时从名册带出的快照；页面显示一律以名册里的姓名为准（JOIN student）
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
  -- 同一学生同一天只能有一条考勤记录，防止重复录入导致出勤率超过 100%
  UNIQUE KEY uk_student_date (student_no, `date`),
  INDEX idx_date (`date`),
  INDEX idx_status (status),
  -- 只能给名册里的学生录考勤；名册改学号时考勤跟着改，有考勤的学生不能直接删
  CONSTRAINT fk_attendance_student FOREIGN KEY (student_no)
    REFERENCES student(student_no) ON UPDATE CASCADE ON DELETE RESTRICT
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
('20250005','赵敏','一(1)班'),
('20250006','刘洋','一(1)班');

-- 近 7 天演示考勤（刘洋今天故意没登记，用来演示"未登记"统计）
INSERT IGNORE INTO attendance_record(student_no, student_name, `date`, status, time, remark) VALUES
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
('20250006','刘洋', DATE_SUB(CURDATE(), INTERVAL 1 DAY), '正常', '07:49', ''),
('20250001','李雷', DATE_SUB(CURDATE(), INTERVAL 2 DAY), '正常', '07:54', ''),
('20250002','韩梅梅', DATE_SUB(CURDATE(), INTERVAL 2 DAY), '正常', '07:57', ''),
('20250003','张伟', DATE_SUB(CURDATE(), INTERVAL 2 DAY), '正常', '07:55', ''),
('20250004','王芳', DATE_SUB(CURDATE(), INTERVAL 2 DAY), '旷课', '--', ''),
('20250005','赵敏', DATE_SUB(CURDATE(), INTERVAL 2 DAY), '正常', '07:52', ''),
('20250006','刘洋', DATE_SUB(CURDATE(), INTERVAL 2 DAY), '正常', '07:51', ''),
('20250001','李雷', DATE_SUB(CURDATE(), INTERVAL 3 DAY), '正常', '07:53', ''),
('20250002','韩梅梅', DATE_SUB(CURDATE(), INTERVAL 3 DAY), '正常', '07:56', ''),
('20250003','张伟', DATE_SUB(CURDATE(), INTERVAL 3 DAY), '正常', '07:50', ''),
('20250004','王芳', DATE_SUB(CURDATE(), INTERVAL 3 DAY), '正常', '07:58', ''),
('20250005','赵敏', DATE_SUB(CURDATE(), INTERVAL 3 DAY), '正常', '07:47', ''),
('20250006','刘洋', DATE_SUB(CURDATE(), INTERVAL 3 DAY), '正常', '07:52', ''),
('20250001','李雷', DATE_SUB(CURDATE(), INTERVAL 4 DAY), '正常', '07:55', ''),
('20250002','韩梅梅', DATE_SUB(CURDATE(), INTERVAL 4 DAY), '迟到', '08:10', '睡过头'),
('20250003','张伟', DATE_SUB(CURDATE(), INTERVAL 4 DAY), '正常', '07:52', ''),
('20250004','王芳', DATE_SUB(CURDATE(), INTERVAL 4 DAY), '正常', '07:59', ''),
('20250005','赵敏', DATE_SUB(CURDATE(), INTERVAL 4 DAY), '正常', '07:48', ''),
('20250006','刘洋', DATE_SUB(CURDATE(), INTERVAL 4 DAY), '请假', '全天', '病假'),
('20250001','李雷', DATE_SUB(CURDATE(), INTERVAL 5 DAY), '正常', '07:51', ''),
('20250002','韩梅梅', DATE_SUB(CURDATE(), INTERVAL 5 DAY), '正常', '07:55', ''),
('20250003','张伟', DATE_SUB(CURDATE(), INTERVAL 5 DAY), '正常', '07:57', ''),
('20250004','王芳', DATE_SUB(CURDATE(), INTERVAL 5 DAY), '迟到', '08:06', ''),
('20250005','赵敏', DATE_SUB(CURDATE(), INTERVAL 5 DAY), '正常', '07:50', ''),
('20250006','刘洋', DATE_SUB(CURDATE(), INTERVAL 5 DAY), '正常', '07:54', ''),
('20250001','李雷', DATE_SUB(CURDATE(), INTERVAL 6 DAY), '正常', '07:56', ''),
('20250002','韩梅梅', DATE_SUB(CURDATE(), INTERVAL 6 DAY), '正常', '07:53', ''),
('20250003','张伟', DATE_SUB(CURDATE(), INTERVAL 6 DAY), '正常', '07:49', ''),
('20250004','王芳', DATE_SUB(CURDATE(), INTERVAL 6 DAY), '正常', '07:58', ''),
('20250005','赵敏', DATE_SUB(CURDATE(), INTERVAL 6 DAY), '正常', '07:52', ''),
('20250006','刘洋', DATE_SUB(CURDATE(), INTERVAL 6 DAY), '正常', '07:55', '');
