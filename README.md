# 校园请假管理系统（Flask + MySQL + 原生前端）

> 学生请假、教师审批、管理员管人管班——一个前后端分离但不用框架的课程设计项目。

后端 Flask 提供 19 个 REST 接口，前端是手写的 HTML/CSS/JS（`fetch` 调接口，没有 Vue/React），
数据库 MySQL 五张表。代码结构清晰，适合当"第一个完整的 Web 项目"来读。

## 功能特性

**学生（stu）**

- 提交请假申请（起止时间、事由、类型）
- 查看自己的请假记录与审批状态
- 撤销待审批的申请
- 修改个人资料

**教师（tea）**

- 查看本班待审批列表
- 通过 / 驳回（可写审批意见）
- 查看已处理记录、本班学生名单

**管理员（admin）**

- 全部请假记录查询
- 用户增删改查（学生 / 教师 / 管理员）
- 学院、班级数据维护
- 统计报表（按状态、按班级）
- 系统操作日志

**其他**

- 登录 / 登出 / 注册，基于 session 的登录态与角色装饰器 `@role_required`
- 所有写操作记入 `system_log`（含 IP）
- 附带 ER 图与功能结构图页面（`er-diagram.html` / `function-diagram.html`）

## 技术栈

| 层 | 选型 |
| --- | --- |
| 后端 | Python 3 + Flask 3 + flask-cors |
| 数据库 | MySQL 8（PyMySQL 驱动，`DictCursor`） |
| 前端 | 原生 HTML5 + CSS3 + JavaScript（fetch API） |
| 认证 | Flask session + 角色装饰器 |

## 目录结构

```
leave-management-system/
├── 校园请假管理系统1/
│   ├── backend/
│   │   ├── app.py            # 全部路由与业务逻辑（约 730 行）
│   │   ├── config.py         # 数据库连接与密钥配置
│   │   ├── init_db.sql       # 建库建表 + 演示数据
│   │   └── requirements.txt
│   └── frontend/
│       ├── login.html        # 登录 / 注册
│       ├── student.html      # 学生端
│       ├── teacher.html      # 教师端
│       ├── admin.html        # 管理端
│       ├── api.js            # 统一的接口封装
│       ├── er-diagram.html   # 数据库 ER 图
│       └── function-diagram.html
└── 校园请假管理系统代码详解.md   # 逐段讲解后端与前端代码
```

## 数据库设计（5 张表）

| 表 | 说明 |
| --- | --- |
| `college` | 学院（名称、院长、电话） |
| `class` | 班级（名称、所属学院、专业、年级） |
| `user` | 用户（学号/工号、密码、姓名、角色 stu/tea/admin、班级） |
| `leave_record` | 请假单（申请人、起止时间、事由、状态、审批人、意见） |
| `system_log` | 操作日志（用户、动作、IP、时间） |

## 运行前必须自己准备

| 要准备什么 | 填在哪 | 说明 |
| --- | --- | --- |
| **MySQL 数据库** | `mysql -u root -p < backend/init_db.sql` | MySQL 5.7+/8.0；脚本会建库 `campus_leave_system`、建 5 张表并插入演示数据 |
| **数据库账号密码** | `backend/config.py` → `DB_CONFIG` | 本副本里是 `your_db_password` 占位，改成你自己的 |
| **Flask 会话密钥** | `backend/config.py` → `APP_CONFIG['secret_key']`；实际生效的是 `app.py` 里的 `app.secret_key` | 两处都要改：`app.py` 现在是 `dev-only-change-me-in-production`，`config.py` 是 `your-secret-key-change-this-in-production` |
| **后端地址** | `frontend/api.js` → `const API_BASE = 'http://localhost:5000/api'` | 后端换端口、部署到服务器、用手机访问时**必须改**，否则前端所有请求都发不出去 |
| 演示账号 | 不用填 | 数据库脚本自带 `stu001` / `tea001` / `admin`，密码都是 `123456`，登录后请自行修改 |

> 前端是纯静态页面，用浏览器直接打开 `frontend/login.html` 即可；但它是跨源请求后端，
> 所以后端的 CORS 必须放行（代码里已 `supports_credentials=True`），换域名时要一起改。

## 快速开始

```bash
# 1) 建库建表（会顺带插入演示数据）
mysql -u root -p < backend/init_db.sql

# 2) 改数据库密码
#    backend/config.py → DB_CONFIG['password']

# 3) 装依赖并启动
pip install -r backend/requirements.txt
python backend/app.py          # http://127.0.0.1:5000
```

浏览器打开 `frontend/login.html` 即可使用（也可用任意静态服务器托管 frontend）。

**演示账号**（密码均为 `123456`）：

| 角色 | 账号 |
| --- | --- |
| 学生 | `stu001` / `stu002` |
| 教师 | `tea001` / `tea002` |
| 管理员 | `admin` |

## 主要接口

```
POST /api/login                             登录
POST /api/register                          注册
POST /api/logout                            登出
GET  /api/classes                           班级列表
POST /api/student/leave                     提交请假
GET  /api/student/leaves                    我的请假
POST /api/student/leave/<id>/cancel         撤销
GET  /api/teacher/pending                   待审批列表
POST /api/teacher/audit/<id>                审批
GET  /api/teacher/done         /students    已处理 / 学生名单
GET  /api/admin/all-leaves     /users       全量查询
POST /api/admin/user  PUT/DELETE /api/admin/user/<id>
GET  /api/admin/statistics     /logs        统计 / 日志
PUT  /api/user/profile                      改资料
```

## 关于本副本

- 已移除 `.idea/`、`__pycache__/` 与两份重复的源码压缩包；
- `backend/config.py` 中的数据库密码已替换为 `your_db_password`，运行前请改成自己的；
- `app.secret_key` 也改成了占位值。

## 已知问题与改进方向（重要）

代码检查时发现的安全问题，如果你要把它当作品展示，建议先修：

1. **密码是明文存储和明文比对的**。`app.py` 里定义了 `hash_password()`（SHA-256），但登录、注册、
   改密三处都没调用它，SQL 直接拿明文比较。建议改成 `werkzeug.security.generate_password_hash` /
   `check_password_hash`（带盐、慢哈希），老数据登录时静默升级。
2. `app.secret_key` 硬编码在源码里，且是弱口令，部署前必须换成环境变量注入的随机值。
3. CORS 开了 `supports_credentials=True` 且后端监听 `0.0.0.0`，线上应改为白名单来源。
4. 注册接口允许自助选择 `role=tea`，无需审核就能拿到教师审批权限，应改为"注册后由管理员审核/指派角色"。
5. 缺少分页，`/api/admin/all-leaves` 数据量大时全量返回。

## License

课程设计作品，仅供学习交流。
