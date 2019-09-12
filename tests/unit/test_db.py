"""
Testing for database unit
"""

from app import create_db


def test_db():
    """
    Testing the DB engine existence
    """
    assert create_db() != None