"""Controller de autenticação."""
from flask import jsonify, request

from src.models.schemas import user_schema
from src.views.serializers import user_serializer

MSG_LOGIN_OK = 'Login realizado com sucesso'


class AuthController:
    def __init__(self, auth_service):
        self.auth_service = auth_service

    def login(self):
        credentials = user_schema.load_login(request.get_json())
        user, token = self.auth_service.authenticate(
            credentials['email'], credentials['password']
        )
        return jsonify({
            'message': MSG_LOGIN_OK,
            'user': user_serializer.to_public_dict(user),
            'token': token,
        }), 200
