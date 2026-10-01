import logging
import re
from datetime import date

from flask import render_template, request, jsonify, redirect, url_for
from models.AttendanceModel import AttendanceModel, STATUSES
from models.StudentModel import StudentModel
from controllers.AttendanceController import login_required

logger = logging.getLogger(__name__)
STUDENT_NO_RE = re.compile(r'^[A-Za-z0-9]+$')


def validate_student(data):
    def text(key):
        return (data.get(key) or '').strip()

    s = {'student_no': text('student_no'), 'student_name': text('student_name'), 'class_name': text('class_name')}
    errors = []
    if not s['student_no']:
        errors.append('学号不能为空')
    elif len(s['student_no']) > 20 or not STUDENT_NO_RE.match(s['student_no']):
        errors.append('学号只能是字母或数字，最多 20 位')
    if not s['student_name']:
        errors.append('姓名不能为空')
    elif len(s['student_name']) > 50:
        errors.append('姓名最多 50 个字')
    if len(s['class_name']) > 50:
        errors.append('班级最多 50 个字')
    return s, errors


def parse_month(value: str):
    """YYYY-MM → 当月 1 号；不合法时返回本月 1 号。"""
    try:
        y, m = (value or '').split('-')
        return date(int(y), int(m), 1)
    except (ValueError, TypeError):
        return date.today().replace(day=1)


class StudentController:
    @staticmethod
    def _form_data():
        return request.form if request.form else (request.get_json(silent=True) or {})

    @staticmethod
    @login_required()
    def student_list():
        return render_template('back/student_list.html')

    @staticmethod
    @login_required(api=True)
    def get_student_list():
        try:
            return jsonify({'code': 200, 'msg': 'success', 'data': StudentModel.list_all()})
        except Exception:
            logger.exception('读取名册失败')
            return jsonify({'code': 500, 'msg': '读取数据失败，请稍后重试'})

    @staticmethod
    @login_required(api=True)
    def add_student():
        s, errors = validate_student(StudentController._form_data())
        if errors:
            return jsonify({'code': 400, 'msg': '；'.join(errors)})
        if StudentModel.no_taken(s['student_no']):
            return jsonify({'code': 409, 'msg': f'学号 {s["student_no"]} 已存在'})
        try:
            StudentModel.add(**s)
            return jsonify({'code': 200, 'msg': '已添加'})
        except Exception:
            logger.exception('添加学生失败')
            return jsonify({'code': 500, 'msg': '保存失败，请稍后重试'})

    @staticmethod
    @login_required(api=True)
    def update_student(id: int):
        if not StudentModel.get_by_id(id):
            return jsonify({'code': 404, 'msg': '学生不存在或已被删除'})
        s, errors = validate_student(StudentController._form_data())
        if errors:
            return jsonify({'code': 400, 'msg': '；'.join(errors)})
        if StudentModel.no_taken(s['student_no'], exclude_id=id):
            return jsonify({'code': 409, 'msg': f'学号 {s["student_no"]} 已被其他学生使用'})
        try:
            StudentModel.update(id, **s)
            return jsonify({'code': 200, 'msg': '已保存'})
        except Exception:
            logger.exception('修改学生失败')
            return jsonify({'code': 500, 'msg': '保存失败，请稍后重试'})

    @staticmethod
    @login_required(api=True)
    def delete_student(id: int):
        stu = StudentModel.get_by_id(id)
        if not stu:
            return jsonify({'code': 404, 'msg': '学生不存在或已被删除'})
        n = StudentModel.record_count(stu['student_no'])
        if n:
            return jsonify({'code': 409, 'msg': f'{stu["student_name"]} 已有 {n} 条考勤记录，不能删除（避免历史数据丢失）'})
        try:
            StudentModel.delete(id)
            return jsonify({'code': 200, 'msg': '已删除'})
        except Exception:
            logger.exception('删除学生失败')
            return jsonify({'code': 500, 'msg': '删除失败，请稍后重试'})

    # ---------------- 个人考勤统计 ----------------
    @staticmethod
    @login_required()
    def student_detail(student_no: str):
        stu = StudentModel.get_by_no(student_no)
        if not stu:
            return redirect(url_for('web.student_list'))
        month = parse_month(request.args.get('month'))
        summary = AttendanceModel.student_month(student_no, month)
        return render_template('back/student_detail.html', student=stu, summary=summary,
                               statuses=STATUSES, month=month.strftime('%Y-%m'))
