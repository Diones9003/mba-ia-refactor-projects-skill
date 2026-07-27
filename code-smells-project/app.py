"""Ponto de entrada da aplicação.

A construção do app vive em `src/app.py` (factory `create_app`); aqui ficam
apenas o wiring com a configuração de ambiente e o servidor de desenvolvimento.
"""

import logging

from src.app import create_app
from src.config import config

app = create_app(config)

if __name__ == "__main__":
    logging.getLogger(__name__).info(
        "Servidor iniciado em http://%s:%s (ambiente=%s, debug=%s)",
        config.HOST,
        config.PORT,
        config.ENVIRONMENT,
        config.DEBUG,
    )
    app.run(host=config.HOST, port=config.PORT, debug=config.DEBUG)
