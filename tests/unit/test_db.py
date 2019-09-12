from app import create_db

def test_db():
    assert create_db() != None