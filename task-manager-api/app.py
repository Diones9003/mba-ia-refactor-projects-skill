"""Ponto de entrada da aplicação.

Toda a montagem vive em `src/app.py:create_app()`. Este arquivo só resolve a
configuração e sobe o servidor — `debug` e `host` agora vêm do ambiente, em vez
do `app.run(debug=True, host='0.0.0.0')` fixo no código.
"""
from src.app import create_app, init_database

app = create_app()

if __name__ == '__main__':
    init_database(app)
    app.run(
        debug=app.config['DEBUG'],
        host=app.config['HOST'],
        port=app.config['PORT'],
    )
