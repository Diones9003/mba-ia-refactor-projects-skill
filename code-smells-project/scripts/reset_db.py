"""Reset do banco de dados.

Substitui o endpoint `POST /admin/reset-db`, que apagava todas as tabelas sem
qualquer autenticação. Como script CLI, a operação exige acesso ao servidor e
confirmação explícita.

Uso:
    python -m scripts.reset_db            # pede confirmação
    python -m scripts.reset_db --sim      # sem confirmação (CI/dev)
"""

import argparse
import sys

from src.config import config
from src.database import create_connection
from src.database import schema

TABELAS = ["itens_pedido", "pedidos", "produtos", "usuarios"]


def resetar(connection, seed=True):
    with connection:
        for tabela in TABELAS:
            connection.execute(f"DELETE FROM {tabela}")
    if seed:
        schema.seed_if_empty(connection)


def main():
    parser = argparse.ArgumentParser(description="Apaga e repopula o banco.")
    parser.add_argument(
        "--sim", action="store_true", help="não pedir confirmação interativa"
    )
    parser.add_argument(
        "--sem-seed", action="store_true", help="não repopular com dados de exemplo"
    )
    argumentos = parser.parse_args()

    print(f"Banco alvo: {config.DATABASE_PATH}")
    if not argumentos.sim:
        resposta = input("Apagar TODOS os dados? [s/N] ").strip().lower()
        if resposta != "s":
            print("Cancelado.")
            return 1

    connection = create_connection(config.DATABASE_PATH)
    try:
        schema.create_schema(connection)
        resetar(connection, seed=not argumentos.sem_seed)
    finally:
        connection.close()

    print("Banco de dados resetado.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
