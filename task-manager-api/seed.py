"""Popula o banco com dados iniciais.

Usa a factory `create_app()` em vez de importar um `app` global, e monta as
entidades por construtor em vez de atribuir atributo por atributo.
"""
from datetime import timedelta

from src.app import create_app, init_database
from src.extensions import db
from src.models import Category, Task, User
from src.utils.datetime_utils import utcnow

USERS = [
    {'name': 'João Silva', 'email': 'joao@email.com', 'password': '1234', 'role': 'admin'},
    {'name': 'Maria Santos', 'email': 'maria@email.com', 'password': 'abcd', 'role': 'user'},
    {'name': 'Pedro Oliveira', 'email': 'pedro@email.com', 'password': 'pass', 'role': 'manager'},
]

CATEGORIES = [
    {'name': 'Backend', 'description': 'Tarefas de backend', 'color': '#3498db'},
    {'name': 'Frontend', 'description': 'Tarefas de frontend', 'color': '#2ecc71'},
    {'name': 'DevOps', 'description': 'Tarefas de infraestrutura', 'color': '#e74c3c'},
    {'name': 'Bug', 'description': 'Correção de bugs', 'color': '#e67e22'},
]

#: `user` e `category` são índices em USERS/CATEGORIES; `due_offset` é em dias
#: relativos a agora (negativo = atrasada).
TASKS = [
    {'title': 'Implementar autenticação JWT', 'description': 'Adicionar autenticação real com JWT',
     'status': 'pending', 'priority': 1, 'user': 0, 'category': 0, 'due_offset': -3},
    {'title': 'Criar tela de login', 'description': 'Tela de login responsiva',
     'status': 'in_progress', 'priority': 2, 'user': 1, 'category': 1, 'due_offset': 5},
    {'title': 'Configurar CI/CD', 'description': 'Pipeline com GitHub Actions',
     'status': 'done', 'priority': 2, 'user': 2, 'category': 2, 'tags': 'devops,ci,github'},
    {'title': 'Corrigir bug no filtro de busca',
     'description': 'Filtro não funciona com caracteres especiais',
     'status': 'pending', 'priority': 1, 'user': 0, 'category': 3, 'due_offset': -1},
    {'title': 'Adicionar paginação na API', 'description': 'Endpoints retornam todos os registros',
     'status': 'pending', 'priority': 3, 'user': 0, 'category': 0, 'due_offset': 10},
    {'title': 'Escrever testes unitários', 'description': 'Cobertura mínima de 80%',
     'status': 'pending', 'priority': 2, 'user': 1, 'category': 0},
    {'title': 'Documentar API com Swagger', 'description': 'Gerar documentação automática',
     'status': 'cancelled', 'priority': 4, 'user': 2, 'category': 0},
    {'title': 'Refatorar models', 'description': 'Melhorar organização dos models',
     'status': 'in_progress', 'priority': 3, 'user': 1, 'category': 0,
     'tags': 'refactor,tech-debt'},
    {'title': 'Configurar monitoramento', 'description': 'Prometheus + Grafana',
     'status': 'pending', 'priority': 4, 'user': 2, 'category': 2, 'due_offset': 20},
    {'title': 'Melhorar validações de input', 'description': 'Usar marshmallow ou pydantic',
     'status': 'pending', 'priority': 3, 'user': 0, 'category': 0,
     'tags': 'improvement,validation'},
]


def seed_data(app):
    with app.app_context():
        Task.query.delete()
        User.query.delete()
        Category.query.delete()
        db.session.commit()

        users = []
        for spec in USERS:
            user = User(name=spec['name'], email=spec['email'], role=spec['role'])
            user.set_password(spec['password'])
            db.session.add(user)
            users.append(user)

        categories = [Category(**spec) for spec in CATEGORIES]
        db.session.add_all(categories)
        db.session.commit()

        now = utcnow()
        for spec in TASKS:
            task = Task(
                title=spec['title'],
                description=spec['description'],
                status=spec['status'],
                priority=spec['priority'],
                user_id=users[spec['user']].id,
                category_id=categories[spec['category']].id,
                tags=spec.get('tags'),
            )
            if 'due_offset' in spec:
                task.due_date = now + timedelta(days=spec['due_offset'])
            db.session.add(task)

        db.session.commit()

        print('Seed concluído com sucesso!')
        print(f'  {User.count()} usuários')
        print(f'  {Category.count()} categorias')
        print(f'  {Task.count()} tasks')


if __name__ == '__main__':
    application = create_app()
    init_database(application)
    seed_data(application)
