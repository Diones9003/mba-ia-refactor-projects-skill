"""Configuração da aplicação lida de variáveis de ambiente.

Nenhum segredo mora no código: tudo vem do `.env` (não versionado) ou do ambiente
do processo. O `.env.example` documenta as chaves esperadas.
"""
import os

from dotenv import load_dotenv

load_dotenv()


def _as_bool(value, default=False):
    if value is None:
        return default
    return value.strip().lower() in ('1', 'true', 'yes', 'on')


class Config:
    """Configuração base — compartilhada por todos os perfis."""

    SECRET_KEY = os.getenv('SECRET_KEY', 'dev-only-insecure-key-change-me')
    SQLALCHEMY_DATABASE_URI = os.getenv('DATABASE_URL', 'sqlite:///tasks.db')
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    DEBUG = _as_bool(os.getenv('FLASK_DEBUG'), False)
    HOST = os.getenv('HOST', '127.0.0.1')
    PORT = int(os.getenv('PORT', '5000'))

    # Origens permitidas para CORS. '*' libera tudo (só aceitável em desenvolvimento).
    CORS_ORIGINS = [o.strip() for o in os.getenv('CORS_ORIGINS', '*').split(',') if o.strip()]

    # Autenticação
    JWT_ALGORITHM = os.getenv('JWT_ALGORITHM', 'HS256')
    JWT_EXPIRATION_MINUTES = int(os.getenv('JWT_EXPIRATION_MINUTES', '60'))
    # Quando falso, os endpoints respondem sem exigir token — reproduz o contrato
    # legado para fins de comparação. O padrão é exigir autenticação.
    REQUIRE_AUTH = _as_bool(os.getenv('REQUIRE_AUTH'), True)

    # Regras de entrada configuráveis (ver src/config/constants.py para as fixas)
    MIN_PASSWORD_LENGTH = int(os.getenv('MIN_PASSWORD_LENGTH', '4'))

    # Paginação das coleções
    DEFAULT_PAGE_SIZE = int(os.getenv('DEFAULT_PAGE_SIZE', '50'))
    MAX_PAGE_SIZE = int(os.getenv('MAX_PAGE_SIZE', '200'))

    # Notificações (SMTP)
    SMTP_HOST = os.getenv('SMTP_HOST', 'localhost')
    SMTP_PORT = int(os.getenv('SMTP_PORT', '587'))
    SMTP_USER = os.getenv('SMTP_USER', '')
    SMTP_PASSWORD = os.getenv('SMTP_PASSWORD', '')
    SMTP_USE_TLS = _as_bool(os.getenv('SMTP_USE_TLS'), True)
    NOTIFICATIONS_ENABLED = _as_bool(os.getenv('NOTIFICATIONS_ENABLED'), False)

    LOG_LEVEL = os.getenv('LOG_LEVEL', 'INFO')


class DevelopmentConfig(Config):
    DEBUG = _as_bool(os.getenv('FLASK_DEBUG'), True)


class ProductionConfig(Config):
    DEBUG = False

    def __init__(self):
        if self.SECRET_KEY == 'dev-only-insecure-key-change-me':
            raise RuntimeError(
                'SECRET_KEY não configurada: defina a variável de ambiente antes de '
                'subir em produção.'
            )


class TestingConfig(Config):
    TESTING = True
    DEBUG = False
    SQLALCHEMY_DATABASE_URI = os.getenv('TEST_DATABASE_URL', 'sqlite:///:memory:')
    NOTIFICATIONS_ENABLED = False


_PROFILES = {
    'development': DevelopmentConfig,
    'production': ProductionConfig,
    'testing': TestingConfig,
}


def get_config(profile=None):
    """Devolve a classe de configuração do perfil pedido (ou de `APP_ENV`)."""
    name = (profile or os.getenv('APP_ENV', 'development')).strip().lower()
    if name not in _PROFILES:
        raise ValueError(
            f"Perfil de configuração desconhecido: {name!r}. "
            f"Use um de: {', '.join(sorted(_PROFILES))}."
        )
    return _PROFILES[name]
