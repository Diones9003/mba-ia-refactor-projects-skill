"""Envio de notificações por e-mail.

Diferenças em relação ao original: as credenciais SMTP são **injetadas** (antes
estavam hardcoded no `__init__`, incluindo `email_password = 'senha123'`), o envio
é desligado por padrão via configuração, e falhas são registradas no logger em vez
de `print`.
"""
import logging
import smtplib
from email.message import EmailMessage

from src.utils.datetime_utils import utcnow

logger = logging.getLogger(__name__)


class NotificationService:
    def __init__(self, host, port, user, password, use_tls=True, enabled=False,
                 sender=None):
        self.host = host
        self.port = port
        self.user = user
        self.password = password
        self.use_tls = use_tls
        self.enabled = enabled
        self.sender = sender or user
        self.notifications = []

    def send_email(self, to, subject, body):
        """Envia um e-mail; devolve `False` (sem propagar) se o envio falhar."""
        if not self.enabled:
            logger.debug('Notificações desabilitadas; e-mail para %s não enviado.', to)
            return False

        message = EmailMessage()
        message['From'] = self.sender
        message['To'] = to
        message['Subject'] = subject
        message.set_content(body)

        try:
            with smtplib.SMTP(self.host, self.port, timeout=10) as server:
                if self.use_tls:
                    server.starttls()
                if self.user:
                    server.login(self.user, self.password)
                server.send_message(message)
        except (smtplib.SMTPException, OSError):
            # Notificação é efeito secundário: falhar aqui não pode derrubar a
            # operação de negócio que a disparou.
            logger.exception('Falha ao enviar e-mail para %s', to)
            return False

        logger.info('E-mail enviado para %s', to)
        return True

    def notify_task_assigned(self, user, task):
        subject = f'Nova task atribuída: {task.title}'
        body = (
            f'Olá {user.name},\n\n'
            f"A task '{task.title}' foi atribuída a você.\n\n"
            f'Prioridade: {task.priority}\n'
            f'Status: {task.status}'
        )
        sent = self.send_email(user.email, subject, body)
        self._record('task_assigned', user.id, task.id, sent)
        return sent

    def notify_task_overdue(self, user, task):
        subject = f'Task atrasada: {task.title}'
        body = (
            f'Olá {user.name},\n\n'
            f"A task '{task.title}' está atrasada!\n\n"
            f'Data limite: {task.due_date}'
        )
        sent = self.send_email(user.email, subject, body)
        self._record('task_overdue', user.id, task.id, sent)
        return sent

    def get_notifications(self, user_id):
        return [n for n in self.notifications if n['user_id'] == user_id]

    def _record(self, kind, user_id, task_id, sent):
        self.notifications.append({
            'type': kind,
            'user_id': user_id,
            'task_id': task_id,
            'sent': sent,
            'timestamp': utcnow(),
        })
