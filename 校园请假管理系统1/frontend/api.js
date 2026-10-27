// api.js
// 前端API调用封装

const API_BASE = 'http://localhost:5000/api';

async function apiRequest(url, method = 'GET', data = null) {
    const options = {
        method,
        headers: { 'Content-Type': 'application/json' },
        credentials: 'include'
    };
    
    if (data && method !== 'GET') {
        options.body = JSON.stringify(data);
    }
    
    try {
        const response = await fetch(API_BASE + url, options);
        return await response.json();
    } catch (error) {
        return { code: 500, msg: '网络错误: ' + error.message };
    }
}

// 登录
async function apiLogin(username, password) {
    return await apiRequest('/login', 'POST', { username, password });
}

// 注册
async function apiRegister(username, password, name, phone, role) {
    return await apiRequest('/register', 'POST', { username, password, name, phone, role });
}

// 退出
async function apiLogout() {
    return await apiRequest('/logout', 'POST');
}

// 学生-提交请假
async function apiSubmitLeave(startTime, endTime, leaveType, reason) {
    return await apiRequest('/student/leave', 'POST', {
        start_time: startTime,
        end_time: endTime,
        leave_type: leaveType,
        reason: reason
    });
}

// 学生-获取请假列表
async function apiGetStudentLeaves() {
    return await apiRequest('/student/leaves');
}

// 学生-撤销请假
async function apiCancelLeave(leaveId) {
    return await apiRequest(`/student/leave/${leaveId}/cancel`, 'POST');
}

// 教师-获取待审批
async function apiGetPending() {
    return await apiRequest('/teacher/pending');
}

// 教师-审批
async function apiAuditLeave(leaveId, action) {
    return await apiRequest(`/teacher/audit/${leaveId}`, 'POST', { action });
}

// 教师-获取已处理
async function apiGetDone() {
    return await apiRequest('/teacher/done');
}

// 管理员-获取用户列表
async function apiGetUsers(role) {
    const query = role ? `?role=${role}` : '';
    return await apiRequest('/admin/users' + query);
}

// 管理员-添加用户
async function apiAddUser(userData) {
    return await apiRequest('/admin/user', 'POST', userData);
}

// 管理员-删除用户
async function apiDeleteUser(userId) {
    return await apiRequest(`/admin/user/${userId}`, 'DELETE');
}

// 管理员-获取统计
async function apiGetStatistics() {
    return await apiRequest('/admin/statistics');
}

// 管理员-获取日志
async function apiGetLogs() {
    return await apiRequest('/admin/logs');
}