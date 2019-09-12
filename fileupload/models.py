"""
The Database tables are described here by using a Model together
with its Model schema.
"""

from app.config import ma, db

class FileMetadata(db.Model):
    """
    The FileMetaData table
    """

    __tablename__ = "filemetadata"
    __table_args__ = {"schema": "filemetadata"}

    id = db.Column(db.Integer, primary_key=True)
    size = db.Column(db.String)
    file_name = db.Column(db.String)
    sha1 = db.Column(db.String, unique=True)
    md5 = db.Column(db.String, unique=True)
    type = db.Column(db.String, default="unknown/unknown")

class FileMetadataSchema(ma.ModelSchema):
    """
    The schema for the FileMetadata table
    """

    class Meta:
        model = FileMetadata
        sqla_session = db.session


