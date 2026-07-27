"""Serialização das respostas — o "V" do MVC numa API REST.

Centraliza o envelope JSON (`dados`/`sucesso`/`mensagem`) que no código original
era remontado à mão em cada um dos 15 handlers.
"""

from flask import jsonify


def resposta_dados(dados, status=200, **extras):
    corpo = {"dados": dados, "sucesso": True}
    corpo.update(extras)
    return jsonify(corpo), status


def resposta_mensagem(mensagem, status=200):
    return jsonify({"sucesso": True, "mensagem": mensagem}), status


def resposta_bruta(corpo, status=200):
    """Para payloads que não usam o envelope (índice e health check)."""
    return jsonify(corpo), status
