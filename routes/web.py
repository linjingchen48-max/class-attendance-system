from controllers.AdminController import AdminController
from controllers.HomeController import HomeController
from controllers.AttendanceController import AttendanceController
from controllers.StudentController import StudentController


def register_routes(app):
    # 前台
    app.add_url_rule('/front/', view_func=HomeController.index, methods=['GET'], endpoint='web.home_index')
    app.add_url_rule('/front/api/stats', view_func=HomeController.get_attendance_stats, methods=['GET'], endpoint='web.home_stats')

    # 后台登录/退出
    app.add_url_rule('/back/login', view_func=AdminController.login_page, methods=['GET'], endpoint='web.admin_login_page')
    app.add_url_rule('/back/login', view_func=AdminController.login, methods=['POST'], endpoint='web.admin_login')
    app.add_url_rule('/back/logout', view_func=AdminController.logout, methods=['GET'], endpoint='web.admin_logout')

    # 考勤管理
    app.add_url_rule('/back/attendance/list', view_func=AttendanceController.data_list, methods=['GET'], endpoint='web.attendance_list')
    app.add_url_rule('/back/attendance/api/list', view_func=AttendanceController.get_data_list, methods=['GET'], endpoint='web.attendance_api_list')
    app.add_url_rule('/back/attendance/add', view_func=AttendanceController.data_add, methods=['GET'], endpoint='web.attendance_add_page')
    app.add_url_rule('/back/attendance/api/add', view_func=AttendanceController.add_data, methods=['POST'], endpoint='web.attendance_api_add')
    app.add_url_rule('/back/attendance/edit/<int:id>', view_func=AttendanceController.data_edit, methods=['GET'], endpoint='web.attendance_edit_page')
    app.add_url_rule('/back/attendance/api/update/<int:id>', view_func=AttendanceController.update_data, methods=['POST'], endpoint='web.attendance_api_update')
    app.add_url_rule('/back/attendance/api/delete/<int:id>', view_func=AttendanceController.delete_data, methods=['POST'], endpoint='web.attendance_api_delete')
    app.add_url_rule('/back/attendance/export', view_func=AttendanceController.export_excel, methods=['GET'], endpoint='web.attendance_export')

    # 批量点名
    app.add_url_rule('/back/attendance/roll-call', view_func=AttendanceController.roll_call, methods=['GET'], endpoint='web.roll_call')
    app.add_url_rule('/back/attendance/api/roll-call', view_func=AttendanceController.get_roll_call, methods=['GET'], endpoint='web.roll_call_api')
    app.add_url_rule('/back/attendance/api/roll-call', view_func=AttendanceController.save_roll_call, methods=['POST'], endpoint='web.roll_call_save')

    # 学生名册与个人统计
    app.add_url_rule('/back/student/list', view_func=StudentController.student_list, methods=['GET'], endpoint='web.student_list')
    app.add_url_rule('/back/student/api/list', view_func=StudentController.get_student_list, methods=['GET'], endpoint='web.student_api_list')
    app.add_url_rule('/back/student/api/add', view_func=StudentController.add_student, methods=['POST'], endpoint='web.student_api_add')
    app.add_url_rule('/back/student/api/update/<int:id>', view_func=StudentController.update_student, methods=['POST'], endpoint='web.student_api_update')
    app.add_url_rule('/back/student/api/delete/<int:id>', view_func=StudentController.delete_student, methods=['POST'], endpoint='web.student_api_delete')
    app.add_url_rule('/back/student/<student_no>', view_func=StudentController.student_detail, methods=['GET'], endpoint='web.student_detail')

    # 访问 /back/ 或根路径时跳到合适的页面
    from flask import redirect, url_for
    app.add_url_rule('/', view_func=lambda: redirect(url_for('web.home_index')), endpoint='web.root')
    app.add_url_rule('/back/', view_func=lambda: redirect(url_for('web.attendance_list')), endpoint='web.back_root')
