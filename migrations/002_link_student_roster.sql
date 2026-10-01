-- 迁移：考勤记录与学生名册建立外键关联
-- 用法：mysql --default-character-set=utf8mb4 -uroot -p dgcsxy < migrations/002_link_student_roster.sql
-- 前提：已执行 001_unique_student_date.sql。新导入 schema.sql 的库不需要执行本文件。
--
-- 第一步：把考勤里出现、名册里没有的学号补进名册（姓名取考勤里最近一次录入的），
-- 否则加外键会失败。补进来的学生班级为空，可以之后到后台"学生名册"里修改。
INSERT INTO student(student_no, student_name)
SELECT a.student_no, a.student_name
FROM attendance_record a
LEFT JOIN student s ON s.student_no = a.student_no
WHERE s.id IS NULL
  AND a.id = (SELECT MAX(id) FROM attendance_record WHERE student_no = a.student_no);

-- 第二步：加外键
ALTER TABLE attendance_record
  ADD CONSTRAINT fk_attendance_student FOREIGN KEY (student_no)
    REFERENCES student(student_no) ON UPDATE CASCADE ON DELETE RESTRICT;
