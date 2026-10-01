from flask import render_template, request, jsonify, session, redirect, url_for
from models.TeacherModel import TeacherModel


class AdminController:
    @staticmethod
    def login_page():
        if session.get("teacher_id"):
            return redirect(url_for('web.attendance_list'))
        return render_template('back/login.html')

    @staticmethod
    def login():
        data = request.form if request.form else (request.get_json(silent=True) or {})
        username = (data.get('username') or '').strip()
        password = (data.get('password') or '').strip()

        if not username or not password:
            return jsonify({'code': 400, 'msg': '请输入账号和密码'})

        teacher = TeacherModel.get_by_login(username, password)
        if teacher:
            session.clear()          # 登录前清空旧 session，防止会话固定
            session.permanent = True  # 有效期 8 小时（见 app.py）
            session['teacher_id'] = teacher['id']
            session['teacher_name'] = teacher.get('name') or teacher.get('username')
            return jsonify({'code': 200, 'msg': '登录成功', 'redirect': url_for('web.attendance_list')})
        return jsonify({'code': 401, 'msg': '账号或密码错误'})

    @staticmethod
    def logout():
        session.clear()
        return redirect(url_for('web.admin_login_page'))
