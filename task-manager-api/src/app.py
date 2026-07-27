"""Application factory — composition root da aplicação.

Aqui, e só aqui, o grafo de dependências é montado: config → extensões → models →
services → controllers → blueprints. Nenhum módulo instancia as próprias
dependências, o que permite criar uma aplicação isolada por teste.

O módulo original criava `app`, `config` e `db` em nível de módulo e chamava
`db.create_all()` **no import** — importar `app` tinha o efeito colateral de criar
o arquivo de banco.
"""
import logging

from flask import Flask

from src.config import get_config
from src.controllers import (
    AuthController,
    CategoryController,
    MetaController,
    ReportController,
    TaskController,
    UserController,
)
from src.extensions import cors, db
from src.middlewares.auth import load_current_user, register_auth
from src.middlewares.error_handler import register_error_handlers
from src.models import Category, Task, User
from src.services import (
    AuthService,
    CategoryService,
    NotificationService,
    ReportService,
    TaskService,
    UserService,
)
from src.views import (
    create_auth_blueprint,
    create_category_blueprint,
    create_meta_blueprint,
    create_report_blueprint,
    create_task_blueprint,
    create_user_blueprint,
)


def create_app(profile=None, config_object=None):
    """Cria e configura uma instância da aplicação.

    Args:
        profile: nome do perfil (`development`, `production`, `testing`).
            Ignorado quando `config_object` é passado.
        config_object: classe/objeto de configuração pronto — útil em testes.
    """
    app = Flask(__name__)

    config = config_object or get_config(profile)
    app.config.from_object(config)

    _configure_logging(app)

    db.init_app(app)
    cors.init_app(app, origins=app.config['CORS_ORIGINS'])

    services = _build_services(app)
    _register_blueprints(app, services)

    register_auth(app, services['auth'])
    app.before_request(load_current_user)
    register_error_handlers(app, db)

    return app


def _configure_logging(app):
    level = getattr(logging, str(app.config.get('LOG_LEVEL', 'INFO')).upper(), logging.INFO)
    logging.basicConfig(
        level=level,
        format='%(asctime)s %(levelname)-8s %(name)s: %(message)s',
    )
    app.logger.setLevel(level)


def _build_services(app):
    """Instancia os services com as dependências injetadas."""
    session = db.session

    notifier = NotificationService(
        host=app.config['SMTP_HOST'],
        port=app.config['SMTP_PORT'],
        user=app.config['SMTP_USER'],
        password=app.config['SMTP_PASSWORD'],
        use_tls=app.config['SMTP_USE_TLS'],
        enabled=app.config['NOTIFICATIONS_ENABLED'],
    )

    return {
        'task': TaskService(session, Task, User, Category, notifier=notifier),
        'user': UserService(
            session, User, Task,
            enforce_authorization=app.config['REQUIRE_AUTH'],
        ),
        'category': CategoryService(session, Category, Task),
        'report': ReportService(session, Task, User, Category),
        'auth': AuthService(
            session, User,
            secret_key=app.config['SECRET_KEY'],
            algorithm=app.config['JWT_ALGORITHM'],
            expiration_minutes=app.config['JWT_EXPIRATION_MINUTES'],
        ),
        'notifier': notifier,
    }


def _register_blueprints(app, services):
    """Monta os controllers e registra os blueprints."""
    task_controller = TaskController(services['task'])
    user_controller = UserController(services['user'], services['task'])
    category_controller = CategoryController(services['category'])
    report_controller = ReportController(services['report'], services['user'])
    auth_controller = AuthController(services['auth'])
    meta_controller = MetaController()

    app.register_blueprint(create_task_blueprint(task_controller))
    app.register_blueprint(create_user_blueprint(user_controller))
    app.register_blueprint(create_category_blueprint(category_controller))
    app.register_blueprint(create_report_blueprint(report_controller))
    app.register_blueprint(create_auth_blueprint(auth_controller))
    app.register_blueprint(create_meta_blueprint(meta_controller))


def init_database(app):
    """Cria o schema. Chamado explicitamente, nunca como efeito de import."""
    with app.app_context():
        db.create_all()
