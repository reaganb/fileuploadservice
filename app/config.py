"""
The sub module for retrieving the SQLAlchemy object, for ORM DB sessions
and Marshmallow object, for data validation, deserialization, and serialization
"""

from flask_marshmallow import Marshmallow
from flask_sqlalchemy import SQLAlchemy
from app import create_app

connex_app = create_app()
db = SQLAlchemy(connex_app.app)
ma = Marshmallow(connex_app.app)