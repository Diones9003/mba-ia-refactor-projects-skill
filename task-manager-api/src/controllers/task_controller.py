"""Controller de task — orquestra request → schema → service → serializer."""
from flask import jsonify, request

from src.middlewares.pagination import pagination_params
from src.models.schemas import task_schema
from src.views.serializers import task_serializer

MSG_TASK_DELETED = 'Task deletada com sucesso'


class TaskController:
    def __init__(self, task_service):
        self.task_service = task_service

    def list_tasks(self):
        limit, offset = pagination_params()
        tasks = self.task_service.list_tasks(limit=limit, offset=offset)
        return jsonify([task_serializer.to_list_item(task) for task in tasks]), 200

    def get_task(self, task_id):
        task = self.task_service.get_task(task_id)
        return jsonify(task_serializer.to_detail(task)), 200

    def create_task(self):
        payload = task_schema.load_create(request.get_json())
        task = self.task_service.create_task(payload)
        return jsonify(task_serializer.to_dict(task)), 201

    def update_task(self, task_id):
        # A existência da task é conferida antes da validação do corpo, como no
        # contrato original (404 tem precedência sobre 400).
        self.task_service.get_task(task_id)
        payload = task_schema.load_update(request.get_json())
        task = self.task_service.update_task(task_id, payload)
        return jsonify(task_serializer.to_dict(task)), 200

    def delete_task(self, task_id):
        self.task_service.delete_task(task_id)
        return jsonify({'message': MSG_TASK_DELETED}), 200

    def search_tasks(self):
        filters = task_schema.load_search(request.args)
        limit, offset = pagination_params()
        tasks = self.task_service.search(limit=limit, offset=offset, **filters)
        return jsonify([task_serializer.to_dict(task) for task in tasks]), 200

    def task_stats(self):
        return jsonify(self.task_service.build_stats()), 200
