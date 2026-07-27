"""Constantes de domínio — fonte única das regras que antes eram literais espalhados.

Substitui as listas e números mágicos que estavam repetidos em routes/ e as constantes
órfãs de utils/helpers.py (que não eram importadas por ninguém).
"""

# --- Status de task ---
STATUS_PENDING = 'pending'
STATUS_IN_PROGRESS = 'in_progress'
STATUS_DONE = 'done'
STATUS_CANCELLED = 'cancelled'

VALID_STATUSES = (STATUS_PENDING, STATUS_IN_PROGRESS, STATUS_DONE, STATUS_CANCELLED)

#: Status em que uma task não pode mais estar "atrasada".
TERMINAL_STATUSES = (STATUS_DONE, STATUS_CANCELLED)

DEFAULT_STATUS = STATUS_PENDING

# --- Prioridade ---
MIN_PRIORITY = 1
MAX_PRIORITY = 5
DEFAULT_PRIORITY = 3

#: Rótulos usados no relatório de resumo (antes eram as variáveis p1..p5).
PRIORITY_LABELS = {
    1: 'critical',
    2: 'high',
    3: 'medium',
    4: 'low',
    5: 'minimal',
}

#: Limite (inclusivo) a partir do qual uma task conta como "alta prioridade".
HIGH_PRIORITY_THRESHOLD = 2

# --- Task ---
MIN_TITLE_LENGTH = 3
MAX_TITLE_LENGTH = 200
MAX_TAGS_LENGTH = 500
TAG_SEPARATOR = ','

#: Único formato de data aceito na entrada da API — o mesmo que o código original
#: exigia. (O `utils/helpers.parse_date` legado também aceitava `%d/%m/%Y`, mas era
#: código morto: nenhuma rota o chamava.)
DATE_INPUT_FORMATS = ('%Y-%m-%d',)
DATE_INPUT_FORMAT_HINT = 'YYYY-MM-DD'

# --- Usuário ---
ROLE_USER = 'user'
ROLE_ADMIN = 'admin'
ROLE_MANAGER = 'manager'

VALID_ROLES = (ROLE_USER, ROLE_ADMIN, ROLE_MANAGER)
DEFAULT_ROLE = ROLE_USER

MAX_NAME_LENGTH = 100
MAX_EMAIL_LENGTH = 150

#: Mesmo padrão que estava duplicado em user_routes.py (linhas 61 e 106).
EMAIL_PATTERN = r'^[a-zA-Z0-9+_.-]+@[a-zA-Z0-9.-]+$'

# --- Categoria ---
MAX_CATEGORY_NAME_LENGTH = 100
MAX_CATEGORY_DESCRIPTION_LENGTH = 300
DEFAULT_COLOR = '#000000'
COLOR_PATTERN = r'^#[0-9a-fA-F]{6}$'

# --- Relatórios ---
RECENT_ACTIVITY_DAYS = 7

# --- API ---
API_VERSION = '1.0'
API_NAME = 'Task Manager API'
