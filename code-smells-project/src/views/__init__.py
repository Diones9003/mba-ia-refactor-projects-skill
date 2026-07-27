from src.views.order_routes import create_order_blueprint
from src.views.product_routes import create_product_blueprint
from src.views.system_routes import create_system_blueprint
from src.views.user_routes import create_user_blueprint

__all__ = [
    "create_order_blueprint",
    "create_product_blueprint",
    "create_system_blueprint",
    "create_user_blueprint",
]
