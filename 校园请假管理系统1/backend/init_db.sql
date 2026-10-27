-- init_db.sql
-- 校园请假管理系统数据库初始化脚本

-- 创建数据库
CREATE DATABASE IF NOT EXISTS campus_leave_system DEFAULT CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
USE campus_leave_system;

-- 学院表
CREATE TABLE IF NOT EXISTS college (
    college_id VARCHAR(20) PRIMARY KEY,
    college_name VARCHAR(100) NOT NULL,
    dean VARCHAR(50),
    phone VARCHAR(20),
    create_time DATETIME DEFAULT CURRENT_TIMESTAMP
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- 班级表
CREATE TABLE IF NOT EXISTS class (
    class_id VARCHAR(20) PRIMARY KEY,
    class_name VARCHAR(100) NOT NULL,
    college_id VARCHAR(20) NOT NULL,
    major VARCHAR(100),
    grade VARCHAR(10),
    create_time DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (college_id) REFERENCES college(college_id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- 用户表
CREATE TABLE IF NOT EXISTS user (
    user_id VARCHAR(20) PRIMARY KEY,
    username VARCHAR(50) NOT NULL UNIQUE,
    password VARCHAR(255) NOT NULL,
    name VARCHAR(50) NOT NULL,
    phone VARCHAR(20),
    role ENUM('stu', 'tea', 'admin') NOT NULL,
    class_id VARCHAR(20),
    create_time DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (class_id) REFERENCES class(class_id) ON DELETE SET NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- 请假记录表
CREATE TABLE IF NOT EXISTS leave_record (
    leave_id INT AUTO_INCREMENT PRIMARY KEY,
    stu_id VARCHAR(20) NOT NULL,
    start_time DATETIME NOT NULL,
    end_time DATETIME NOT NULL,
    leave_type ENUM('病假', '事假', '其他') NOT NULL,
    reason TEXT,
    status ENUM('待审批', '已通过', '已驳回') DEFAULT '待审批',
    audit_tea_id VARCHAR(20),
    audit_time DATETIME,
    audit_comment TEXT,
    create_time DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (stu_id) REFERENCES user(user_id) ON DELETE CASCADE,
    FOREIGN KEY (audit_tea_id) REFERENCES user(user_id) ON DELETE SET NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- 系统日志表
CREATE TABLE IF NOT EXISTS system_log (
    log_id INT AUTO_INCREMENT PRIMARY KEY,
    user_id VARCHAR(20),
    username VARCHAR(50),
    action VARCHAR(255) NOT NULL,
    ip_address VARCHAR(50),
    create_time DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES user(user_id) ON DELETE SET NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- ========== 插入默认数据 ==========

-- 学院数据
INSERT INTO college (college_id, college_name, dean, phone) VALUES 
('COL01', '信息工程学院', '张院长', '13800000001'),
('COL02', '经济管理学院', '李院长', '13800000002')
ON DUPLICATE KEY UPDATE college_name=VALUES(college_name);

-- 班级数据
INSERT INTO class (class_id, class_name, college_id, major, grade) VALUES 
('C001', '计算机科学1班', 'COL01', '计算机科学与技术', '2025'),
('C002', '软件工程2班', 'COL01', '软件工程', '2025'),
('C003', '工商管理1班', 'COL02', '工商管理', '2025')
ON DUPLICATE KEY UPDATE class_name=VALUES(class_name);

-- 用户数据（密码为123456）
INSERT INTO user (user_id, username, password, name, phone, role, class_id) VALUES 
('stu001', 'stu001', '123456', '张三', '13911112222', 'stu', 'C001'),
('stu002', 'stu002', '123456', '李四', '13922223333', 'stu', 'C001'),
('tea001', 'tea001', '123456', '王老师', '13611223344', 'tea', 'C001'),
('tea002', 'tea002', '123456', '李老师', '13622334455', 'tea', 'C002'),
('admin', 'admin', '123456', '系统管理员', '13900000000', 'admin', NULL)
ON DUPLICATE KEY UPDATE username=VALUES(username);