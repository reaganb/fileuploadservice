"""
Configurations for the testing framework.
"""

import pytest
from app import create_app
from flask_sqlalchemy import SQLAlchemy
from fileupload.models import FileMetadata


@pytest.fixture(scope='module')
def new_file():
    """
    Fixture for creating a new FileMetadata model object
    """
    file = FileMetadata(
        size='123',
        file_name='new_file',
        sha1='asdasd123123',
        md5='asdasd',
        type='unknown/unknown',
    )
    return file

@pytest.fixture(scope='module')
def test_client():
    """
    Fixture for creating a new Flask test_client object
    """
    flask_app = create_app()
    flask_app.add_api("swagger.yml")

    with flask_app.app.test_client() as client:
        with flask_app.app.app_context():
            db = SQLAlchemy(flask_app.app)
            db.create_all()
        yield client