"""Extensões Flask instanciadas sem aplicação.

Cada extensão é criada aqui de forma "solta" e ligada a uma aplicação concreta
dentro de `create_app()` — o que permite criar várias aplicações (ex.: uma por teste)
sem estado global compartilhado.
"""
from flask_cors import CORS
from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()
cors = CORS()
