"""Validação de entrada reutilizável.

No código original a validação estava duplicada entre `criar_produto` e
`atualizar_produto` — e já havia divergido (o update não checava tamanho de nome
nem categoria). Aqui existe uma única definição, usada pelos dois endpoints.
"""

from flask import request

from src.config.constants import (
    CATEGORIA_PADRAO,
    CATEGORIAS_VALIDAS,
    NOME_PRODUTO_TAMANHO_MAXIMO,
    NOME_PRODUTO_TAMANHO_MINIMO,
)
from src.errors import ValidationError


def obter_json_obrigatorio():
    """Devolve o corpo JSON ou 400 — nunca 500 por content-type ausente."""
    dados = request.get_json(silent=True)
    if not isinstance(dados, dict) or not dados:
        raise ValidationError("Dados inválidos")
    return dados


def _validar_numero(valor, mensagem_tipo, mensagem_negativo, inteiro=False):
    if isinstance(valor, bool) or not isinstance(valor, (int, float)):
        raise ValidationError(mensagem_tipo)
    if inteiro and not float(valor).is_integer():
        raise ValidationError(mensagem_tipo)
    if valor < 0:
        raise ValidationError(mensagem_negativo)
    return int(valor) if inteiro else valor


def validar_payload_produto(dados):
    """Valida e normaliza o corpo de criação/atualização de produto."""
    for campo, mensagem in (
        ("nome", "Nome é obrigatório"),
        ("preco", "Preço é obrigatório"),
        ("estoque", "Estoque é obrigatório"),
    ):
        if campo not in dados:
            raise ValidationError(mensagem)

    nome = dados["nome"]
    if not isinstance(nome, str):
        raise ValidationError("Nome deve ser um texto")

    preco = _validar_numero(
        dados["preco"],
        "Preço deve ser um número",
        "Preço não pode ser negativo",
    )
    estoque = _validar_numero(
        dados["estoque"],
        "Estoque deve ser um número inteiro",
        "Estoque não pode ser negativo",
        inteiro=True,
    )

    nome = nome.strip()
    if len(nome) < NOME_PRODUTO_TAMANHO_MINIMO:
        raise ValidationError("Nome muito curto")
    if len(nome) > NOME_PRODUTO_TAMANHO_MAXIMO:
        raise ValidationError("Nome muito longo")

    categoria = dados.get("categoria", CATEGORIA_PADRAO)
    if categoria not in CATEGORIAS_VALIDAS:
        raise ValidationError("Categoria inválida. Válidas: " + str(CATEGORIAS_VALIDAS))

    descricao = dados.get("descricao", "")
    if not isinstance(descricao, str):
        raise ValidationError("Descrição deve ser um texto")

    return {
        "nome": nome,
        "descricao": descricao,
        "preco": preco,
        "estoque": estoque,
        "categoria": categoria,
    }


def validar_payload_usuario(dados):
    nome = dados.get("nome", "")
    email = dados.get("email", "")
    senha = dados.get("senha", "")

    if not nome or not email or not senha:
        raise ValidationError("Nome, email e senha são obrigatórios")
    if not all(isinstance(campo, str) for campo in (nome, email, senha)):
        raise ValidationError("Nome, email e senha devem ser textos")
    if "@" not in email or "." not in email.split("@")[-1]:
        raise ValidationError("E-mail inválido")

    return {"nome": nome.strip(), "email": email.strip().lower(), "senha": senha}


def validar_credenciais(dados):
    email = dados.get("email", "")
    senha = dados.get("senha", "")
    if not email or not senha:
        raise ValidationError("Email e senha são obrigatórios")
    return {"email": str(email).strip().lower(), "senha": str(senha)}


def validar_itens_pedido(itens):
    """Garante que cada item tenha produto_id e quantidade utilizáveis."""
    if not isinstance(itens, list) or len(itens) == 0:
        raise ValidationError("Pedido deve ter pelo menos 1 item")

    itens_validados = []
    for item in itens:
        if not isinstance(item, dict):
            raise ValidationError("Item de pedido inválido")
        if "produto_id" not in item or "quantidade" not in item:
            raise ValidationError("Cada item precisa de produto_id e quantidade")

        produto_id = _validar_numero(
            item["produto_id"],
            "produto_id deve ser um número inteiro",
            "produto_id inválido",
            inteiro=True,
        )
        quantidade = _validar_numero(
            item["quantidade"],
            "quantidade deve ser um número inteiro",
            "quantidade inválida",
            inteiro=True,
        )
        if quantidade < 1:
            raise ValidationError("quantidade deve ser maior que zero")

        itens_validados.append({"produto_id": produto_id, "quantidade": quantidade})
    return itens_validados


def validar_preco_opcional(valor, campo):
    """Converte filtros de preço da query string, respondendo 400 se inválidos."""
    if valor is None or valor == "":
        return None
    try:
        return float(valor)
    except (TypeError, ValueError):
        raise ValidationError(f"{campo} deve ser um número") from None
