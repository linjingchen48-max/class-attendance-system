from controllers.AdminController import AdminController
from controllers.HomeController import HomeController
from controllers.AttendanceController import AttendanceController


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
