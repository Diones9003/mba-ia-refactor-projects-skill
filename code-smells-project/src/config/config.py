import os

from dotenv import load_dotenv

load_dotenv()


def _env_bool(name, default="false"):
    return os.getenv(name, default).strip().lower() in ("1", "true", "yes", "on")


def _env_list(name, default=""):
    raw = os.getenv(name, default)
    return [item.strip() for item in raw.split(",") if item.strip()]


class Config:
    ENVIRONMENT = os.getenv("ENVIRONMENT", "development")
    DEBUG = _env_bool("DEBUG")
    HOST = os.getenv("HOST", "127.0.0.1")
    PORT = int(os.getenv("PORT", "5000"))

    DATABASE_PATH = os.getenv("DATABASE_PATH", "loja.db")
    SEED_DATABASE = _env_bool("SEED_DATABASE", "true")

    ALLOWED_ORIGINS = _env_list("ALLOWED_ORIGINS", "http://localhost:3000")

    API_VERSION = "1.0.0"

    LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")

    @property
    def secret_key(self):
        """SECRET_KEY nunca tem valor default em produção.

        Em desenvolvimento, cai para uma chave explicitamente insegura para não
        travar o boot local; fora dele, a ausência da variável é um erro fatal.
        """
        secret = os.getenv("SECRET_KEY")
        if secret:
            return secret
        if self.DEBUG:
            return "dev-insecure-key-nao-use-em-producao"
        raise RuntimeError(
            "SECRET_KEY não definida. Configure a variável de ambiente "
            "(ver .env.example) antes de iniciar a aplicação."
        )


config = Config()
