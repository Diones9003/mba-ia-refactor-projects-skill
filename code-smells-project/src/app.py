import logging

from flask import Flask
from flask_cors import CORS

from src.config import config as config_padrao
from src.database import ConnectionProvider
from src.database import schema
from src.controllers import (
    OrderController,
    ProductController,
    SystemController,
    UserController,
)
from src.middlewares import register_error_handlers, register_request_logger
from src.models import OrderModel, ProductModel, ReportModel, UserModel
from src.services import NotificationService, OrderService, ReportService
from src.views import (
    create_order_blueprint,
    create_product_blueprint,
    create_system_blueprint,
    create_user_blueprint,
)

logger = logging.getLogger(__name__)


def configure_logging(config):
    logging.basicConfig(
        level=getattr(logging, config.LOG_LEVEL.upper(), logging.INFO),
        format="%(asctime)s %(levelname)s %(name)s: %(message)s",
    )


def create_app(config=None, connection_provider=None, initialize_database=True):
    """Composition root: monta o grafo de dependências e devolve o app.

    Todas as dependências são parametrizáveis — um teste pode passar um
    `connection_provider` apontando para `:memory:` sem tocar em nenhuma camada.
    """
    config = config or config_padrao
    configure_logging(config)

    app = Flask(__name__)
    app.config["SECRET_KEY"] = config.secret_key
    app.config["DEBUG"] = config.DEBUG
    CORS(app, origins=config.ALLOWED_ORIGINS)

    provider = connection_provider or ConnectionProvider(config.DATABASE_PATH)
    if isinstance(provider, ConnectionProvider):
        app.teardown_appcontext(provider.close)

    if initialize_database:
        schema.initialize(provider(), seed=config.SEED_DATABASE)

    # Models (recebem a conexão injetada)
    product_model = ProductModel(provider)
    user_model = UserModel(provider)
    order_model = OrderModel(provider, product_model)
    report_model = ReportModel(provider)

    # Services (regra de negócio)
    notification_service = NotificationService()
    order_service = OrderService(order_model, notification_service)
    report_service = ReportService(report_model)

    # Controllers (orquestração)
    product_controller = ProductController(product_model)
    user_controller = UserController(user_model)
    order_controller = OrderController(order_service)
    system_controller = SystemController(
        config,
        report_service,
        report_model,
        contadores={
            "produtos": product_model.count,
            "usuarios": user_model.count,
            "pedidos": order_model.count,
        },
    )

    # Views (roteamento + serialização)
    app.register_blueprint(create_product_blueprint(product_controller))
    app.register_blueprint(create_user_blueprint(user_controller))
    app.register_blueprint(create_order_blueprint(order_controller))
    app.register_blueprint(create_system_blueprint(system_controller))

    # Middlewares transversais
    register_request_logger(app)
    register_error_handlers(app)

    return app
