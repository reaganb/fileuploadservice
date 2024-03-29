"""
The testing functions to be executed sequentially to perform integration testing of the API server request methods
"""

import io
import hashlib
import json


# file_content = b"testingtesting"
# file_content = b"testingtesting1"
# file_content = b"testingtesting2"
# file_content = b"testingtesting3"
# file_content = b"testingtesting4"
# FILE_CONTENT = b"testingtesting5"
# FILE_CONTENT = b"testingtesting6"
# FILE_CONTENT = b"testingtesting7"
FILE_CONTENT = b"testingtesting8"
FILE_HASH = hashlib.md5(FILE_CONTENT).hexdigest()


def test_home_page(test_client):
    """
    Testing the home page
    """
    response = test_client.get('/')
    assert response.status_code == 200


def test_upload(test_client):
    """
    Testing the POST request method
    """
    data = {
        "upfile": (io.BytesIO(FILE_CONTENT), 'testing.jpg')
    }

    response = test_client.post(
        '/service/fileupload',
        data=data
    )

    print(response)

    assert response.status_code == 201


def test_get_files(test_client):
    """
    Testing the GET request method, for sequence type response
    """

    response = test_client.get('/service/fileupload')
    assert response.status_code == 200


def test_get_file(test_client):
    """
    Testing the GET request method, for single object type response
    """

    response = test_client.get(f'/service/fileupload/{FILE_HASH}')
    assert response.status_code == 200


def test_update(test_client):
    """
    Testing the PUT request method
    """

    file = {
            "file_name": "new_file",
            "type": "unknown/unknown"
    }

    response = test_client.put(
        f'/service/fileupload/{FILE_HASH}',
        data=json.dumps(file),
        headers={'content-type' : 'application/json'}
    )

    assert response.status_code == 201


def test_delete(test_client):
    """
    Testing the DEL request method
    """
    response = test_client.delete(
        f'/service/fileupload/{FILE_HASH}',
    )

    assert response.status_code == 201
