from flask import render_template, jsonify
from models.AttendanceModel import AttendanceModel


class HomeController:
    @staticmethod
    def index():
        return render_template('front/index.html')

    @staticmethod
    def get_attendance_stats():
        try:
            stats = AttendanceModel.stats()
            return jsonify({'code': 200, 'msg': 'success', 'data': stats})
        except Exception as e:
            return jsonify({'code': 500, 'msg': f'获取统计失败：{e}', 'data': {
                'total_students': 0,
                'today_attendance': {'present': 0, 'absent': 0, 'late': 0, 'leave': 0, 'attended': 0},
                'today_rate': 0,
                'weekly_rate': [None] * 7,
                'abnormal_list': []
            }})
