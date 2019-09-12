"""
The testing for the Model unit
"""

from fileupload.models import FileMetadata


def test_new_file(new_file):
    assert isinstance(new_file.size, str)
    assert isinstance(new_file.file_name, str)
    assert isinstance(new_file.sha1, str)
    assert isinstance(new_file.md5, str)
    assert isinstance(new_file.type, str)

