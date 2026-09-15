from flask import render_template, request, jsonify, session, redirect, url_for
from models.AttendanceModel import AttendanceModel


class AttendanceController:
    @staticmethod
    def _check_login():
        if not session.get('teacher_id'):
            return redirect(url_for('web.admin_login_page'))
        return None

    @staticmethod
    def data_list():
        login_check = AttendanceController._check_login()
        if login_check:
            return login_check
        return render_template('back/data_list.html')

    @staticmethod
    def get_data_list():
        login_check = AttendanceController._check_login()
        if login_check:
            return jsonify({'code': 401, 'msg': '未登录'})
        try:
            data = AttendanceModel.list_all()
            return jsonify({'code': 200, 'msg': 'success', 'data': data})
        except Exception as e:
            return jsonify({'code': 500, 'msg': f'读取数据失败：{e}'})

    @staticmethod
    def data_add():
        login_check = AttendanceController._check_login()
        if login_check:
            return login_check
        return render_template('back/data_add.html')

    @staticmethod
    def add_data():
        login_check = AttendanceController._check_login()
        if login_check:
            return jsonify({'code': 401, 'msg': '未登录'})

        data = request.form if request.form else (request.get_json(silent=True) or {})
        try:
            AttendanceModel.add(
                student_no=(data.get('student_no') or '').strip(),
                student_name=(data.get('student_name') or '').strip(),
                date_str=(data.get('date') or '').strip(),
                status=(data.get('status') or '正常').strip(),
                time=(data.get('time') or '').strip(),
                remark=(data.get('remark') or '').strip(),
            )
            return jsonify({'code': 200, 'msg': '保存成功'})
        except Exception as e:
            return jsonify({'code': 500, 'msg': f'保存失败：{e}'})

    @staticmethod
    def data_edit(id: int):
        login_check = AttendanceController._check_login()
        if login_check:
            return login_check
        record = AttendanceModel.get_by_id(id)
        if not record:
            return redirect(url_for('web.attendance_list'))
        return render_template('back/data_edit.html', record=record)

    @staticmethod
    def update_data(id: int):
        login_check = AttendanceController._check_login()
        if login_check:
            return jsonify({'code': 401, 'msg': '未登录'})

        data = request.form if request.form else (request.get_json(silent=True) or {})
        try:
            AttendanceModel.update(
                record_id=id,
                student_no=(data.get('student_no') or '').strip(),
                student_name=(data.get('student_name') or '').strip(),
                date_str=(data.get('date') or '').strip(),
                status=(data.get('status') or '正常').strip(),
                time=(data.get('time') or '').strip(),
                remark=(data.get('remark') or '').strip(),
            )
            return jsonify({'code': 200, 'msg': '修改成功'})
        except Exception as e:
            return jsonify({'code': 500, 'msg': f'修改失败：{e}'})

    @staticmethod
    def delete_data(id: int):
        login_check = AttendanceController._check_login()
        if login_check:
            return jsonify({'code': 401, 'msg': '未登录'})
        try:
            AttendanceModel.delete(id)
            return jsonify({'code': 200, 'msg': '删除成功'})
        except Exception as e:
            return jsonify({'code': 500, 'msg': f'删除失败：{e}'})
