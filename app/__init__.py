""""
The main app module.

This is where the main flask/connexion instance can be retrieved through a function.

A function for the creation of the ORM database is also here.
"""

import connexion
from sqlalchemy.schema import CreateSchema
from sqlalchemy import create_engine
from sqlalchemy_utils import database_exists, create_database
import os
import shutil

MOD_PATH = os.path.join(os.path.dirname(__file__))

DB_PORT = os.environ['DB_PORT']
DB_TYPE = os.environ['DB_TYPE']
DB_USER = os.environ['DB_USER']
DB_HOST = os.environ['DB_HOST']
DB_PASSWORD = os.environ['DB_PASSWORD']
DB_NAME = os.environ['DB_NAME']

ROOT_DIR = os.environ['ROOT_DIR']
LOG_DIR = os.environ['LOG_DIR']
DATA_DIR = os.environ['DATA_DIR']

DB_URI = f"{DB_TYPE}://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"

DB_SCHEMAS = ["filemetadata"]


def create_app():
    """
    The function to call in order to get the flask/connexion object.
    it will also specify some of the flask-sqlalchemy configurations.
    """

    connex = connexion.FlaskApp(__name__, specification_dir="./")
    connex.app.config['SQLALCHEMY_DATABASE_URI'] = DB_URI
    connex.app.config["SQLALCHEMY_ECHO"] = False
    connex.app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

    return connex


def create_db():
    """
    This will create the database, table, and schema.

    return -- The database engine connection from sqlalchemy
    """

    if os.path.exists(DATA_DIR):
        shutil.rmtree(DATA_DIR)
        os.mkdir(DATA_DIR)
    else:
        os.mkdir(DATA_DIR)

    if database_exists(DB_URI):
        engine = create_engine(DB_URI)
        conn = engine.connect()
        for schema in DB_SCHEMAS:
            if not conn.dialect.has_schema(conn, schema=schema):
                engine.execute(CreateSchema(schema))
        conn.close()

        return engine

    else:
        create_database(DB_URI)
        engine = create_engine(DB_URI)
        conn = engine.connect()
        for schema in DB_SCHEMAS:
            if not conn.dialect.has_schema(conn, schema=schema):
                engine.execute(CreateSchema(schema))
        conn.close()

        return engine
