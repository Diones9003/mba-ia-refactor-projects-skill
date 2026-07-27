"""Constantes de domínio — substituem os magic numbers/strings do código original."""

CATEGORIAS_VALIDAS = [
    "informatica",
    "moveis",
    "vestuario",
    "geral",
    "eletronicos",
    "livros",
]
CATEGORIA_PADRAO = "geral"

STATUS_PEDIDO_PENDENTE = "pendente"
STATUS_PEDIDO_APROVADO = "aprovado"
STATUS_PEDIDO_ENVIADO = "enviado"
STATUS_PEDIDO_ENTREGUE = "entregue"
STATUS_PEDIDO_CANCELADO = "cancelado"

STATUS_PEDIDO_VALIDOS = [
    STATUS_PEDIDO_PENDENTE,
    STATUS_PEDIDO_APROVADO,
    STATUS_PEDIDO_ENVIADO,
    STATUS_PEDIDO_ENTREGUE,
    STATUS_PEDIDO_CANCELADO,
]

TIPO_USUARIO_CLIENTE = "cliente"
TIPO_USUARIO_ADMIN = "admin"

NOME_PRODUTO_TAMANHO_MINIMO = 2
NOME_PRODUTO_TAMANHO_MAXIMO = 200

# Faixas de desconto sobre o faturamento bruto: (faturamento_minimo, percentual).
# Avaliadas da maior para a menor faixa; a primeira que casar é aplicada.
FAIXAS_DESCONTO = [
    (10000, 0.10),
    (5000, 0.05),
    (1000, 0.02),
]
