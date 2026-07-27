"""Exceções de domínio.

Services e models lançam estas exceções em vez de montar respostas HTTP. O
`error_handler` central traduz cada uma no status code e corpo JSON corretos —
é o que permite remover os `try/except` genéricos que existiam em cada handler.
"""


class AppError(Exception):
    """Erro de aplicação com status HTTP associado."""

    status_code = 500
    message = 'Erro interno'

    def __init__(self, message=None, status_code=None):
        super().__init__(message or self.message)
        if message is not None:
            self.message = message
        if status_code is not None:
            self.status_code = status_code

    def to_payload(self):
        return {'error': self.message}


class ValidationError(AppError):
    """Entrada inválida — 400."""

    status_code = 400
    message = 'Dados inválidos'


class NotFoundError(AppError):
    """Recurso inexistente — 404."""

    status_code = 404
    message = 'Recurso não encontrado'


class ConflictError(AppError):
    """Violação de unicidade ou estado conflitante — 409."""

    status_code = 409
    message = 'Conflito de dados'


class UnauthorizedError(AppError):
    """Credencial ausente ou inválida — 401."""

    status_code = 401
    message = 'Credenciais inválidas'


class ForbiddenError(AppError):
    """Autenticado, mas sem permissão — 403."""

    status_code = 403
    message = 'Acesso negado'
