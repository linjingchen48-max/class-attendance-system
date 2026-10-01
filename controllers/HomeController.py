import logging

from flask import render_template, jsonify
from models.AttendanceModel import AttendanceModel
from models.StudentModel import StudentModel


class HomeController:
    @staticmethod
    def index():
        try:
            class_name = StudentModel.class_label()
        except Exception:
            logging.getLogger(__name__).exception('读取班级名失败')
            class_name = ''
        return render_template('front/index.html', class_name=class_name)

    @staticmethod
    def get_attendance_stats():
        try:
            stats = AttendanceModel.stats()
            return jsonify({'code': 200, 'msg': 'success', 'data': stats})
        except Exception:
            logging.getLogger(__name__).exception('获取大屏统计失败')
            return jsonify({'code': 500, 'msg': '获取统计失败', 'data': {
                'total_students': 0,
                'class_name': '',
                'today_attendance': {'present': 0, 'absent': 0, 'late': 0, 'leave': 0, 'attended': 0, 'unregistered': 0},
                'today_rate': 0,
                'weekly_rate': [None] * 7,
                'abnormal_list': []
            }})
