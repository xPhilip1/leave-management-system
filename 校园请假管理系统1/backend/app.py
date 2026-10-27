# app.py
# 校园请假管理系统 - Flask后端主程序

from flask import Flask, request, jsonify, session
from flask_cors import CORS
from datetime import datetime
import pymysql
import hashlib
from functools import wraps

# 导入配置
from config import DB_CONFIG, SERVER_CONFIG

app = Flask(__name__)
app.secret_key = 'dev-only-change-me-in-production'
CORS(app, supports_credentials=True)


# ========== 请求日志 ==========
@app.before_request
def log_request():
    """记录每个请求"""
    print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] {request.method} {request.path}")
    if request.method == 'POST' and request.is_json:
        data = request.get_json()
        if data:
            safe_data = {k: ('***' if 'password' in k.lower() else v) for k, v in data.items()}
            print(f"  请求数据: {safe_data}")


@app.after_request
def log_response(response):
    """记录响应状态"""
    print(f"  响应状态: {response.status_code}")
    return response


# ========== 数据库操作 ==========

def get_db():
    """获取数据库连接"""
    return pymysql.connect(
        host=DB_CONFIG['host'],
        port=DB_CONFIG['port'],
        user=DB_CONFIG['user'],
        password=DB_CONFIG['password'],
        database=DB_CONFIG['database'],
        charset=DB_CONFIG['charset'],
        cursorclass=pymysql.cursors.DictCursor
    )


def hash_password(password):
    """密码哈希加密"""
    return hashlib.sha256(password.encode()).hexdigest()


# ========== 装饰器 ==========

def login_required(f):
    """登录验证装饰器"""

    @wraps(f)
    def decorated(*args, **kwargs):
        if 'user_id' not in session:
            return jsonify({'code': 401, 'msg': '请先登录'}), 401
        return f(*args, **kwargs)

    return decorated


def role_required(roles):
    """角色验证装饰器"""

    def decorator(f):
        @wraps(f)
        def decorated(*args, **kwargs):
            if 'user_id' not in session:
                return jsonify({'code': 401, 'msg': '请先登录'}), 401
            if session.get('role') not in roles:
                return jsonify({'code': 403, 'msg': '权限不足'}), 403
            return f(*args, **kwargs)

        return decorated

    return decorator


def add_log(user_id, username, action):
    """记录系统日志"""
    try:
        db = get_db()
        cursor = db.cursor()
        cursor.execute(
            "INSERT INTO system_log (user_id, username, action, ip_address) VALUES (%s, %s, %s, %s)",
            (user_id, username, action, request.remote_addr)
        )
        db.commit()
    except Exception as e:
        print(f"日志记录失败: {e}")
    finally:
        cursor.close()
        db.close()


# ========== 登录注册 ==========

@app.route('/api/login', methods=['POST'])
def login():
    """用户登录"""
    data = request.get_json()
    username = data.get('username', '').strip()
    password = data.get('password', '').strip()

    if not username or not password:
        return jsonify({'code': 400, 'msg': '账号和密码不能为空'})

    try:
        db = get_db()
        cursor = db.cursor()
        cursor.execute("SELECT * FROM user WHERE username = %s AND password = %s",
                       (username, password))
        user = cursor.fetchone()

        if user:
            session['user_id'] = user['user_id']
            session['username'] = user['username']
            session['role'] = user['role']
            session['name'] = user['name']

            add_log(user['user_id'], user['username'], '用户登录')

            return jsonify({
                'code': 200, 'msg': '登录成功',
                'data': {
                    'user_id': user['user_id'],
                    'username': user['username'],
                    'name': user['name'],
                    'role': user['role'],
                    'phone': user['phone'],
                    'class_id': user['class_id']
                }
            })
        return jsonify({'code': 401, 'msg': '账号或密码错误'})
    except Exception as e:
        return jsonify({'code': 500, 'msg': f'服务器错误: {str(e)}'})
    finally:
        cursor.close()
        db.close()


@app.route('/api/register', methods=['POST'])
def register():
    """用户注册"""
    data = request.get_json()
    username = data.get('username', '').strip()
    password = data.get('password', '').strip()
    name = data.get('name', '').strip()
    phone = data.get('phone', '').strip()
    role = data.get('role', 'stu')
    class_id = data.get('class_id', None)

    if not username or not password:
        return jsonify({'code': 400, 'msg': '账号和密码不能为空'})

    if not name:
        return jsonify({'code': 400, 'msg': '姓名不能为空'})

    if not phone or not phone.isdigit() or len(phone) != 11:
        return jsonify({'code': 400, 'msg': '请输入正确的11位手机号'})

    if role not in ['stu', 'tea']:
        return jsonify({'code': 400, 'msg': '无效的角色'})

    if role == 'stu' and not class_id:
        return jsonify({'code': 400, 'msg': '学生请选择所属班级'})

    try:
        db = get_db()
        cursor = db.cursor()

        cursor.execute("SELECT user_id FROM user WHERE username = %s", (username,))
        if cursor.fetchone():
            return jsonify({'code': 400, 'msg': '该账号已被注册'})

        prefix = {'stu': 'stu', 'tea': 'tea'}
        cursor.execute("SELECT MAX(user_id) as max_id FROM user WHERE user_id LIKE %s",
                       (prefix[role] + '%',))
        result = cursor.fetchone()
        num = int(result['max_id'][len(prefix[role]):]) + 1 if result['max_id'] else 1
        user_id = f"{prefix[role]}{num:03d}"

        cursor.execute(
            "INSERT INTO user (user_id, username, password, name, phone, role, class_id) VALUES (%s, %s, %s, %s, %s, %s, %s)",
            (user_id, username, password, name, phone, role, class_id if role == 'stu' else None)
        )
        db.commit()

        add_log(user_id, username, '注册新账号')

        return jsonify({'code': 200, 'msg': '注册成功', 'data': {'user_id': user_id}})
    except Exception as e:
        db.rollback()
        return jsonify({'code': 500, 'msg': f'注册失败: {str(e)}'})
    finally:
        cursor.close()
        db.close()


@app.route('/api/classes', methods=['GET'])
def get_classes():
    """获取班级列表（注册时使用）"""
    try:
        db = get_db()
        cursor = db.cursor()
        cursor.execute("SELECT class_id, class_name FROM class ORDER BY class_id")
        classes = cursor.fetchall()
        return jsonify({'code': 200, 'data': classes})
    except Exception as e:
        return jsonify({'code': 500, 'msg': str(e)})
    finally:
        cursor.close()
        db.close()

@app.route('/api/logout', methods=['POST'])
def logout():
    """退出登录"""
    if 'user_id' in session:
        add_log(session['user_id'], session.get('username', ''), '退出登录')
    session.clear()
    return jsonify({'code': 200, 'msg': '已退出登录'})


# ========== 学生端 ==========

@app.route('/api/student/leave', methods=['POST'])
@login_required
@role_required(['stu'])
def submit_leave():
    """提交请假申请"""
    data = request.get_json()
    stu_id = session['user_id']
    start_time = data.get('start_time')
    end_time = data.get('end_time')
    leave_type = data.get('leave_type')
    reason = data.get('reason', '')

    if not all([start_time, end_time, leave_type]):
        return jsonify({'code': 400, 'msg': '请填写完整的请假信息'})

    try:
        db = get_db()
        cursor = db.cursor()
        cursor.execute(
            "INSERT INTO leave_record (stu_id, start_time, end_time, leave_type, reason) VALUES (%s, %s, %s, %s, %s)",
            (stu_id, start_time, end_time, leave_type, reason)
        )
        db.commit()

        add_log(stu_id, session['username'], f'提交请假申请')

        return jsonify({'code': 200, 'msg': '请假申请提交成功'})
    except Exception as e:
        db.rollback()
        return jsonify({'code': 500, 'msg': f'提交失败: {str(e)}'})
    finally:
        cursor.close()
        db.close()


@app.route('/api/student/leaves', methods=['GET'])
@login_required
@role_required(['stu'])
def get_student_leaves():
    """获取学生请假记录"""
    try:
        db = get_db()
        cursor = db.cursor()
        cursor.execute(
            "SELECT * FROM leave_record WHERE stu_id = %s ORDER BY create_time DESC",
            (session['user_id'],)
        )
        records = cursor.fetchall()

        for r in records:
            for key in ['start_time', 'end_time', 'audit_time', 'create_time']:
                if r.get(key):
                    r[key] = r[key].strftime('%Y-%m-%d %H:%M:%S')

        return jsonify({'code': 200, 'data': records})
    except Exception as e:
        return jsonify({'code': 500, 'msg': str(e)})
    finally:
        cursor.close()
        db.close()


@app.route('/api/student/leave/<int:leave_id>/cancel', methods=['POST'])
@login_required
@role_required(['stu'])
def cancel_leave(leave_id):
    """撤销请假"""
    try:
        db = get_db()
        cursor = db.cursor()
        cursor.execute(
            "DELETE FROM leave_record WHERE leave_id = %s AND stu_id = %s AND status = '待审批'",
            (leave_id, session['user_id'])
        )
        if cursor.rowcount == 0:
            return jsonify({'code': 400, 'msg': '无法撤销'})
        db.commit()
        return jsonify({'code': 200, 'msg': '撤销成功'})
    except Exception as e:
        db.rollback()
        return jsonify({'code': 500, 'msg': str(e)})
    finally:
        cursor.close()
        db.close()


# ========== 教师端 ==========

@app.route('/api/teacher/pending', methods=['GET'])
@login_required
@role_required(['tea'])
def get_pending():
    """获取待审批列表"""
    try:
        db = get_db()
        cursor = db.cursor()
        cursor.execute("SELECT class_id FROM user WHERE user_id = %s", (session['user_id'],))
        teacher = cursor.fetchone()

        if not teacher or not teacher['class_id']:
            return jsonify({'code': 200, 'data': []})

        cursor.execute("""
                       SELECT lr.*, u.name as student_name
                       FROM leave_record lr
                                JOIN user u ON lr.stu_id = u.user_id
                       WHERE u.class_id = %s
                         AND lr.status = '待审批'
                       ORDER BY lr.create_time DESC
                       """, (teacher['class_id'],))
        records = cursor.fetchall()

        for r in records:
            for key in ['start_time', 'end_time', 'create_time']:
                if r.get(key):
                    r[key] = r[key].strftime('%Y-%m-%d %H:%M:%S')

        return jsonify({'code': 200, 'data': records})
    except Exception as e:
        return jsonify({'code': 500, 'msg': str(e)})
    finally:
        cursor.close()
        db.close()


@app.route('/api/teacher/audit/<int:leave_id>', methods=['POST'])
@login_required
@role_required(['tea'])
def audit_leave(leave_id):
    """审批请假"""
    data = request.get_json()
    action = data.get('action')

    if action not in ['pass', 'refuse']:
        return jsonify({'code': 400, 'msg': '无效操作'})

    status = '已通过' if action == 'pass' else '已驳回'

    try:
        db = get_db()
        cursor = db.cursor()
        cursor.execute(
            "UPDATE leave_record SET status=%s, audit_tea_id=%s, audit_time=NOW() WHERE leave_id=%s AND status='待审批'",
            (status, session['user_id'], leave_id)
        )
        if cursor.rowcount == 0:
            return jsonify({'code': 400, 'msg': '该记录不存在或已处理'})
        db.commit()

        add_log(session['user_id'], session['username'], f'{status}请假 ID:{leave_id}')

        return jsonify({'code': 200, 'msg': f'已{status}'})
    except Exception as e:
        db.rollback()
        return jsonify({'code': 500, 'msg': str(e)})
    finally:
        cursor.close()
        db.close()


@app.route('/api/teacher/done', methods=['GET'])
@login_required
@role_required(['tea'])
def get_done():
    """获取已处理记录"""
    try:
        db = get_db()
        cursor = db.cursor()
        cursor.execute("""
                       SELECT lr.*, u.name as student_name
                       FROM leave_record lr
                                JOIN user u ON lr.stu_id = u.user_id
                       WHERE lr.audit_tea_id = %s
                       ORDER BY lr.audit_time DESC
                       """, (session['user_id'],))
        records = cursor.fetchall()

        for r in records:
            for key in ['start_time', 'end_time', 'audit_time', 'create_time']:
                if r.get(key):
                    r[key] = r[key].strftime('%Y-%m-%d %H:%M:%S')

        return jsonify({'code': 200, 'data': records})
    except Exception as e:
        return jsonify({'code': 500, 'msg': str(e)})
    finally:
        cursor.close()
        db.close()


@app.route('/api/teacher/students', methods=['GET'])
@login_required
@role_required(['tea'])
def get_class_students():
    """获取班级学生名单"""
    try:
        db = get_db()
        cursor = db.cursor()

        cursor.execute("SELECT class_id FROM user WHERE user_id=%s", (session['user_id'],))
        teacher = cursor.fetchone()

        if not teacher or not teacher['class_id']:
            return jsonify({'code': 200, 'data': []})

        cursor.execute(
            "SELECT user_id, name, phone, class_id FROM user WHERE class_id=%s AND role='stu' ORDER BY user_id",
            (teacher['class_id'],)
        )
        students = cursor.fetchall()

        return jsonify({'code': 200, 'data': students})
    except Exception as e:
        return jsonify({'code': 500, 'msg': str(e)})
    finally:
        cursor.close()
        db.close()


# ========== 管理员端 ==========

@app.route('/api/admin/all-leaves', methods=['GET'])
@login_required
@role_required(['admin'])
def get_all_leaves():
    """获取全系统请假记录"""
    try:
        db = get_db()
        cursor = db.cursor()
        cursor.execute("""
                       SELECT lr.*,
                              u1.name as student_name,
                              u2.name as teacher_name
                       FROM leave_record lr
                                LEFT JOIN user u1 ON lr.stu_id = u1.user_id
                                LEFT JOIN user u2 ON lr.audit_tea_id = u2.user_id
                       ORDER BY lr.create_time DESC LIMIT 200
                       """)
        records = cursor.fetchall()

        for r in records:
            for key in ['start_time', 'end_time', 'audit_time', 'create_time']:
                if r.get(key):
                    r[key] = r[key].strftime('%Y-%m-%d %H:%M:%S')

        return jsonify({'code': 200, 'data': records})
    except Exception as e:
        return jsonify({'code': 500, 'msg': str(e)})
    finally:
        cursor.close()
        db.close()

@app.route('/api/admin/users', methods=['GET'])
@login_required
@role_required(['admin'])
def get_users():
    """获取用户列表"""
    role = request.args.get('role', '')
    try:
        db = get_db()
        cursor = db.cursor()
        if role:
            cursor.execute("SELECT * FROM user WHERE role=%s ORDER BY create_time DESC", (role,))
        else:
            cursor.execute("SELECT * FROM user ORDER BY create_time DESC")
        return jsonify({'code': 200, 'data': cursor.fetchall()})
    except Exception as e:
        return jsonify({'code': 500, 'msg': str(e)})
    finally:
        cursor.close()
        db.close()


@app.route('/api/admin/user', methods=['POST'])
@login_required
@role_required(['admin'])
def add_user():
    """添加用户"""
    data = request.get_json()
    role = data.get('role', 'stu')

    try:
        db = get_db()
        cursor = db.cursor()

        prefix = {'stu': 'stu', 'tea': 'tea', 'admin': 'admin'}
        cursor.execute("SELECT MAX(user_id) as max_id FROM user WHERE user_id LIKE %s", (prefix[role] + '%',))
        result = cursor.fetchone()
        num = int(result['max_id'][len(prefix[role]):]) + 1 if result['max_id'] else 1
        user_id = f"{prefix[role]}{num:03d}"

        cursor.execute(
            "INSERT INTO user (user_id, username, password, name, phone, role, class_id) VALUES (%s,%s,%s,%s,%s,%s,%s)",
            (user_id, data.get('username'), data.get('password', '123456'), data.get('name'), data.get('phone', ''),
             role, data.get('class_id'))
        )
        db.commit()

        add_log(session['user_id'], session['username'], f'添加用户:{user_id}')

        return jsonify({'code': 200, 'msg': '添加成功'})
    except Exception as e:
        db.rollback()
        return jsonify({'code': 500, 'msg': str(e)})
    finally:
        cursor.close()
        db.close()


@app.route('/api/admin/user/<user_id>', methods=['PUT'])
@login_required
@role_required(['admin'])
def update_user(user_id):
    """修改用户信息"""
    data = request.get_json()

    try:
        db = get_db()
        cursor = db.cursor()

        cursor.execute("SELECT * FROM user WHERE user_id=%s", (user_id,))
        if not cursor.fetchone():
            return jsonify({'code': 404, 'msg': '用户不存在'})

        update_fields = []
        values = []

        if 'name' in data:
            update_fields.append("name=%s")
            values.append(data['name'])
        if 'phone' in data:
            update_fields.append("phone=%s")
            values.append(data['phone'])
        if 'class_id' in data:
            update_fields.append("class_id=%s")
            values.append(data['class_id'])

        if not update_fields:
            return jsonify({'code': 400, 'msg': '没有需要更新的字段'})

        values.append(user_id)
        sql = f"UPDATE user SET {', '.join(update_fields)} WHERE user_id=%s"
        cursor.execute(sql, values)
        db.commit()

        add_log(session['user_id'], session['username'], f'修改用户:{user_id}')

        return jsonify({'code': 200, 'msg': '修改成功'})
    except Exception as e:
        db.rollback()
        return jsonify({'code': 500, 'msg': str(e)})
    finally:
        cursor.close()
        db.close()


@app.route('/api/admin/user/<user_id>', methods=['DELETE'])
@login_required
@role_required(['admin'])
def delete_user(user_id):
    """删除用户"""
    try:
        db = get_db()
        cursor = db.cursor()
        cursor.execute("DELETE FROM user WHERE user_id=%s", (user_id,))
        db.commit()
        add_log(session['user_id'], session['username'], f'删除用户:{user_id}')
        return jsonify({'code': 200, 'msg': '删除成功'})
    except Exception as e:
        db.rollback()
        return jsonify({'code': 500, 'msg': str(e)})
    finally:
        cursor.close()
        db.close()


@app.route('/api/admin/statistics', methods=['GET'])
@login_required
@role_required(['admin'])
def get_statistics():
    """统计数据"""
    try:
        db = get_db()
        cursor = db.cursor()
        cursor.execute("""
            SELECT COUNT(*) as total,
                   SUM(CASE WHEN status='已通过' THEN 1 ELSE 0 END) as approved,
                   SUM(CASE WHEN status='已驳回' THEN 1 ELSE 0 END) as rejected,
                   SUM(CASE WHEN status='待审批' THEN 1 ELSE 0 END) as pending,
                   SUM(CASE WHEN leave_type='病假' THEN 1 ELSE 0 END) as sick_leave,
                   SUM(CASE WHEN leave_type='事假' THEN 1 ELSE 0 END) as personal_leave,
                   SUM(CASE WHEN leave_type='其他' THEN 1 ELSE 0 END) as other_leave
            FROM leave_record
        """)
        return jsonify({'code': 200, 'data': cursor.fetchone()})
    except Exception as e:
        return jsonify({'code': 500, 'msg': str(e)})
    finally:
        cursor.close()
        db.close()


@app.route('/api/admin/logs', methods=['GET'])
@login_required
@role_required(['admin'])
def get_logs():
    """系统日志"""
    try:
        db = get_db()
        cursor = db.cursor()
        cursor.execute("SELECT * FROM system_log ORDER BY create_time DESC LIMIT 100")
        logs = cursor.fetchall()
        for log in logs:
            if log.get('create_time'):
                log['create_time'] = log['create_time'].strftime('%Y-%m-%d %H:%M:%S')
        return jsonify({'code': 200, 'data': logs})
    except Exception as e:
        return jsonify({'code': 500, 'msg': str(e)})
    finally:
        cursor.close()
        db.close()


# ========== 个人信息修改 ==========

@app.route('/api/user/profile', methods=['PUT'])
@login_required
def update_profile():
    """修改个人信息"""
    data = request.get_json()
    user_id = session['user_id']

    try:
        db = get_db()
        cursor = db.cursor()

        # 修改密码需要验证原密码
        if 'new_password' in data:
            old_password = data.get('old_password', '')
            cursor.execute("SELECT password FROM user WHERE user_id=%s", (user_id,))
            user = cursor.fetchone()

            if not user or user['password'] != old_password:
                return jsonify({'code': 400, 'msg': '原密码错误'})

            new_password = data['new_password']
            if len(new_password) < 4:
                return jsonify({'code': 400, 'msg': '密码长度至少4位'})

            cursor.execute("UPDATE user SET password=%s WHERE user_id=%s", (new_password, user_id))
            db.commit()
            add_log(user_id, session['username'], '修改密码')

        # 修改姓名
        elif 'name' in data:
            cursor.execute("UPDATE user SET name=%s WHERE user_id=%s", (data['name'], user_id))
            db.commit()
            session['name'] = data['name']
            add_log(user_id, session['username'], '修改姓名')

        # 修改手机号
        elif 'phone' in data:
            old_password = data.get('old_password', '')
            if old_password:
                cursor.execute("SELECT password FROM user WHERE user_id=%s", (user_id,))
                user = cursor.fetchone()
                if not user or user['password'] != old_password:
                    return jsonify({'code': 400, 'msg': '原密码错误'})
            cursor.execute("UPDATE user SET phone=%s WHERE user_id=%s", (data['phone'], user_id))
            db.commit()
            add_log(user_id, session['username'], '修改手机号')
        else:
            db.commit()

        return jsonify({'code': 200, 'msg': '修改成功'})
    except Exception as e:
        db.rollback()
        return jsonify({'code': 500, 'msg': str(e)})
    finally:
        cursor.close()
        db.close()


# ========== 启动 ==========
if __name__ == '__main__':
    print("=" * 50)
    print("  校园请假管理系统后端服务")
    print(f"  地址: http://localhost:{SERVER_CONFIG['port']}")
    print("=" * 50)
    app.run(
        host=SERVER_CONFIG['host'],
        port=SERVER_CONFIG['port'],
        debug=SERVER_CONFIG['debug']
    )