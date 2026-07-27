"""Exceções de domínio.

Models e services lançam estas exceções em vez de formatar respostas HTTP; o
mapeamento para status code acontece em um único lugar
(`src/middlewares/error_handler.py`).
"""


class AppError(Exception):
    status_code = 500
    mensagem_padrao = "Erro interno"

    def __init__(self, mensagem=None):
        self.mensagem = mensagem or self.mensagem_padrao
        super().__init__(self.mensagem)


class ValidationError(AppError):
    """Entrada malformada ou fora das regras de validação."""

    status_code = 400
    mensagem_padrao = "Dados inválidos"


class BusinessRuleError(AppError):
    """Regra de negócio violada (estoque insuficiente, produto inexistente em pedido)."""

    status_code = 400
    mensagem_padrao = "Operação não permitida"


class NotFoundError(AppError):
    status_code = 404
    mensagem_padrao = "Recurso não encontrado"


class UnauthorizedError(AppError):
    status_code = 401
    mensagem_padrao = "Não autorizado"
