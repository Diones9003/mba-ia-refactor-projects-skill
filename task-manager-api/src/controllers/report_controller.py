"""Controller de relatórios."""
from flask import jsonify


class ReportController:
    def __init__(self, report_service, user_service):
        self.report_service = report_service
        self.user_service = user_service

    def summary(self):
        return jsonify(self.report_service.build_summary()), 200

    def user_report(self, user_id):
        user = self.user_service.get_user(user_id)
        return jsonify(self.report_service.build_user_report(user)), 200
