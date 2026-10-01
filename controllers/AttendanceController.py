import logging
import re
from datetime import datetime

from flask import render_template, request, jsonify, session, redirect, url_for
from models.AttendanceModel import AttendanceModel

logger = logging.getLogger(__name__)

STATUSES = ('正常', '迟到', '请假', '旷课')
STUDENT_NO_RE = re.compile(r'^[A-Za-z0-9]+$')
DUPLICATE_MSG = '该学生当天已有考勤记录，请到列表中编辑原记录'


def _is_duplicate_error(e: Exception) -> bool:
    """MySQL 唯一约束冲突的错误码是 1062。并发下预检查可能漏过，靠数据库约束兜底。"""
    return bool(getattr(e, 'args', None)) and e.args[0] == 1062


def validate_record(data):
    """校验并清洗表单。返回 (record, errors)：errors 非空时 record 不可用。

    前端表单的 required 只是提示，绕过页面直接调接口也必须被挡住，所以以这里为准。
    """
    def text(key):
        return (data.get(key) or '').strip()

    record = {
        'student_no': text('student_no'),
        'student_name': text('student_name'),
        'date_str': text('date'),
        'status': text('status') or '正常',
        'time': text('time'),
        'remark': text('remark'),
    }
    errors = []

    if not record['student_no']:
        errors.append('学号不能为空')
    elif len(record['student_no']) > 20 or not STUDENT_NO_RE.match(record['student_no']):
        errors.append('学号只能是字母或数字，最多 20 位')

    if not record['student_name']:
        errors.append('姓名不能为空')
    elif len(record['student_name']) > 50:
        errors.append('姓名最多 50 个字')

    if not record['date_str']:
        errors.append('日期不能为空')
    else:
        try:
            # 统一成 YYYY-MM-DD，顺带挡掉 2026-02-30 这种不存在的日期
            record['date_str'] = datetime.strptime(record['date_str'], '%Y-%m-%d').date().isoformat()
        except ValueError:
            errors.append('日期格式不正确，应为 YYYY-MM-DD')

    if record['status'] not in STATUSES:
        errors.append('状态只能是：' + ' / '.join(STATUSES))

    if len(record['time']) > 20:
        errors.append('时间最多 20 个字')
    if len(record['remark']) > 200:
        errors.append('备注最多 200 个字')

    return record, errors


class AttendanceController:
    @staticmethod
    def _check_login():
        if not session.get('teacher_id'):
            return redirect(url_for('web.admin_login_page'))
        return None

    @staticmethod
    def _form_data():
        return request.form if request.form else (request.get_json(silent=True) or {})

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
        except Exception:
            # 具体错误只写日志，不把数据库报错原文返回给页面
            logger.exception('读取考勤列表失败')
            return jsonify({'code': 500, 'msg': '读取数据失败，请稍后重试'})

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

        record, errors = validate_record(AttendanceController._form_data())
        if errors:
            return jsonify({'code': 400, 'msg': '；'.join(errors)})
        if AttendanceModel.exists_on_date(record['student_no'], record['date_str']):
            return jsonify({'code': 409, 'msg': DUPLICATE_MSG})
        try:
            AttendanceModel.add(**record)
            return jsonify({'code': 200, 'msg': '保存成功'})
        except Exception as e:
            if _is_duplicate_error(e):
                return jsonify({'code': 409, 'msg': DUPLICATE_MSG})
            logger.exception('新增考勤失败')
            return jsonify({'code': 500, 'msg': '保存失败，请稍后重试'})

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

        if not AttendanceModel.get_by_id(id):
            return jsonify({'code': 404, 'msg': '记录不存在或已被删除'})
        record, errors = validate_record(AttendanceController._form_data())
        if errors:
            return jsonify({'code': 400, 'msg': '；'.join(errors)})
        if AttendanceModel.exists_on_date(record['student_no'], record['date_str'], exclude_id=id):
            return jsonify({'code': 409, 'msg': DUPLICATE_MSG})
        try:
            AttendanceModel.update(record_id=id, **record)
            return jsonify({'code': 200, 'msg': '修改成功'})
        except Exception as e:
            if _is_duplicate_error(e):
                return jsonify({'code': 409, 'msg': DUPLICATE_MSG})
            logger.exception('修改考勤失败')
            return jsonify({'code': 500, 'msg': '修改失败，请稍后重试'})

    @staticmethod
    def delete_data(id: int):
        login_check = AttendanceController._check_login()
        if login_check:
            return jsonify({'code': 401, 'msg': '未登录'})
        try:
            AttendanceModel.delete(id)
            return jsonify({'code': 200, 'msg': '删除成功'})
        except Exception:
            logger.exception('删除考勤失败')
            return jsonify({'code': 500, 'msg': '删除失败，请稍后重试'})
