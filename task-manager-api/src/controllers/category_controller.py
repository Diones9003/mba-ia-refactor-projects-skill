"""Controller de categoria."""
from flask import jsonify, request

from src.middlewares.pagination import pagination_params
from src.models.schemas import category_schema
from src.views.serializers import category_serializer

MSG_CATEGORY_DELETED = 'Categoria deletada'


class CategoryController:
    def __init__(self, category_service):
        self.category_service = category_service

    def list_categories(self):
        limit, offset = pagination_params()
        rows = self.category_service.list_with_task_counts(limit=limit, offset=offset)
        return jsonify([
            category_serializer.to_list_item(category, task_count)
            for category, task_count in rows
        ]), 200

    def create_category(self):
        payload = category_schema.load_create(request.get_json())
        category = self.category_service.create_category(payload)
        return jsonify(category_serializer.to_dict(category)), 201

    def update_category(self, category_id):
        self.category_service.get_category(category_id)
        payload = category_schema.load_update(request.get_json())
        category = self.category_service.update_category(category_id, payload)
        return jsonify(category_serializer.to_dict(category)), 200

    def delete_category(self, category_id):
        self.category_service.delete_category(category_id)
        return jsonify({'message': MSG_CATEGORY_DELETED}), 200
