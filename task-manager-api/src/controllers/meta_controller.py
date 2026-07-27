"""Controller dos endpoints de metadados e healthcheck."""
from flask import jsonify

from src.config.constants import API_NAME, API_VERSION
from src.utils.datetime_utils import to_iso, utcnow


class MetaController:
    def index(self):
        return jsonify({'message': API_NAME, 'version': API_VERSION}), 200

    def health(self):
        return jsonify({'status': 'ok', 'timestamp': to_iso(utcnow())}), 200
