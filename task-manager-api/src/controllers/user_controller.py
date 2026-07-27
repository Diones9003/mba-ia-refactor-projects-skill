"""Controller de usuário."""
from flask import current_app, jsonify, request

from src.middlewares.auth import current_user
from src.middlewares.pagination import pagination_params
from src.models.schemas import user_schema
from src.views.serializers import task_serializer, user_serializer

MSG_USER_DELETED = 'Usuário deletado com sucesso'


class UserController:
    def __init__(self, user_service, task_service):
        self.user_service = user_service
        self.task_service = task_service

    def _min_password_length(self):
        return current_app.config['MIN_PASSWORD_LENGTH']

    def list_users(self):
        limit, offset = pagination_params()
        rows = self.user_service.list_users(limit=limit, offset=offset)
        return jsonify([
            user_serializer.to_list_item(user, task_count) for user, task_count in rows
        ]), 200

    def get_user(self, user_id):
        user, tasks = self.user_service.get_user_with_tasks(user_id)
        return jsonify(user_serializer.to_detail(user, tasks)), 200

    def create_user(self):
        payload = user_schema.load_create(
            request.get_json(), self._min_password_length()
        )
        user = self.user_service.create_user(payload, requester=current_user())
        return jsonify(user_serializer.to_public_dict(user)), 201

    def update_user(self, user_id):
        self.user_service.get_user(user_id)
        payload = user_schema.load_update(
            request.get_json(), self._min_password_length()
        )
        user = self.user_service.update_user(
            user_id, payload, requester=current_user()
        )
        return jsonify(user_serializer.to_public_dict(user)), 200

    def delete_user(self, user_id):
        self.user_service.delete_user(user_id)
        return jsonify({'message': MSG_USER_DELETED}), 200

    def list_user_tasks(self, user_id):
        limit, offset = pagination_params()
        tasks = self.task_service.list_by_user(user_id, limit=limit, offset=offset)
        return jsonify([
            task_serializer.to_user_task_item(task) for task in tasks
        ]), 200
