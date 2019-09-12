import pytest
from app import create_app
from flask_sqlalchemy import SQLAlchemy
from fileupload.models import FileMetadata

@pytest.fixture(scope='module')
def new_file():
    file = FileMetadata(
        size='123',
        file_name='new_file',
        sha1='asdasd123123',
        md5='asdasd',
        type='unknown/unknown',
    )
    return file

@pytest.fixture(scope='module')
def new_db():
    flask_app = create_app()
    flask_app.add_api("swagger.yml")
    new_db = SQLAlchemy(flask_app.app)
    return new_db

@pytest.fixture(scope='module')
def test_client():
    flask_app = create_app()
    flask_app.add_api("swagger.yml")

    with flask_app.app.test_client() as client:
        with flask_app.app.app_context():
            db = SQLAlchemy(flask_app.app)
            db.create_all()
        yield client