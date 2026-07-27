"""Criação de schema e seed.

No código original isso acontecia como efeito colateral do primeiro `get_db()`,
ou seja, dentro do caminho de leitura de qualquer request. Aqui é uma operação
explícita, chamada uma única vez na inicialização.
"""

import logging

from werkzeug.security import generate_password_hash

from src.config.constants import TIPO_USUARIO_ADMIN, TIPO_USUARIO_CLIENTE

logger = logging.getLogger(__name__)

DDL = [
    """
    CREATE TABLE IF NOT EXISTS produtos (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        nome TEXT NOT NULL,
        descricao TEXT,
        preco REAL NOT NULL,
        estoque INTEGER NOT NULL,
        categoria TEXT,
        ativo INTEGER DEFAULT 1,
        criado_em TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS usuarios (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        nome TEXT NOT NULL,
        email TEXT NOT NULL UNIQUE,
        senha TEXT NOT NULL,
        tipo TEXT DEFAULT 'cliente',
        criado_em TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS pedidos (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        usuario_id INTEGER NOT NULL,
        status TEXT DEFAULT 'pendente',
        total REAL,
        criado_em TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS itens_pedido (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        pedido_id INTEGER NOT NULL,
        produto_id INTEGER NOT NULL,
        quantidade INTEGER NOT NULL,
        preco_unitario REAL NOT NULL,
        FOREIGN KEY (pedido_id) REFERENCES pedidos (id),
        FOREIGN KEY (produto_id) REFERENCES produtos (id)
    )
    """,
]

PRODUTOS_SEED = [
    ("Notebook Gamer", "Notebook potente para jogos", 5999.99, 10, "informatica"),
    ("Mouse Wireless", "Mouse sem fio ergonômico", 89.90, 50, "informatica"),
    ("Teclado Mecânico", "Teclado mecânico RGB", 299.90, 30, "informatica"),
    ("Monitor 27''", "Monitor 27 polegadas 144hz", 1899.90, 15, "informatica"),
    ("Headset Gamer", "Headset com microfone", 199.90, 25, "informatica"),
    ("Cadeira Gamer", "Cadeira ergonômica", 1299.90, 8, "moveis"),
    ("Webcam HD", "Webcam 1080p", 249.90, 20, "informatica"),
    ("Hub USB", "Hub USB 3.0 7 portas", 79.90, 40, "informatica"),
    ("SSD 1TB", "SSD NVMe 1TB", 449.90, 35, "informatica"),
    ("Camiseta Dev", "Camiseta estampa código", 59.90, 100, "vestuario"),
]

# Credenciais de demonstração — gravadas com hash, nunca em texto puro.
USUARIOS_SEED = [
    ("Admin", "admin@loja.com", "admin123", TIPO_USUARIO_ADMIN),
    ("João Silva", "joao@email.com", "123456", TIPO_USUARIO_CLIENTE),
    ("Maria Santos", "maria@email.com", "senha123", TIPO_USUARIO_CLIENTE),
]


def create_schema(connection):
    with connection:
        for comando in DDL:
            connection.execute(comando)


def seed_if_empty(connection):
    """Popula dados de exemplo apenas se a tabela de produtos estiver vazia."""
    ja_populado = connection.execute("SELECT COUNT(*) FROM produtos").fetchone()[0] > 0
    if ja_populado:
        return False

    with connection:
        connection.executemany(
            "INSERT INTO produtos (nome, descricao, preco, estoque, categoria) "
            "VALUES (?, ?, ?, ?, ?)",
            PRODUTOS_SEED,
        )
        connection.executemany(
            "INSERT INTO usuarios (nome, email, senha, tipo) VALUES (?, ?, ?, ?)",
            [
                (nome, email, generate_password_hash(senha), tipo)
                for nome, email, senha, tipo in USUARIOS_SEED
            ],
        )
    logger.info("Banco populado com dados de exemplo")
    return True


def initialize(connection, seed=True):
    create_schema(connection)
    if seed:
        seed_if_empty(connection)
