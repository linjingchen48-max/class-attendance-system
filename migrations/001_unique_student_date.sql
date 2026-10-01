-- 迁移：给已有数据库的 attendance_record 加上"学号+日期"唯一约束
-- 用法：mysql --default-character-set=utf8mb4 -uroot -p dgcsxy < migrations/001_unique_student_date.sql
--
-- 新导入 schema.sql 的库已经带有该约束，不需要执行本文件。
--
-- 如果执行时报 Duplicate entry，说明库里已经有重复记录，先用下面的查询找出来，
-- 在后台手动删掉多余的那条，再重新执行：
--   SELECT student_no, `date`, COUNT(*) AS n, GROUP_CONCAT(id) AS ids
--   FROM attendance_record GROUP BY student_no, `date` HAVING n > 1;

ALTER TABLE attendance_record
  ADD UNIQUE KEY uk_student_date (student_no, `date`);

-- 唯一索引以 student_no 开头，可以替代原来的单列索引
ALTER TABLE attendance_record
  DROP INDEX idx_student_no;
