"""
The module that the flask/connexion will lookout for to perform the functionalities for the request methods
of the API server.
"""

import tempfile
import hashlib
import os.path as op
import os
import shutil
from sqlalchemy import or_
from magic import Magic, MagicException
from flask import abort, jsonify
from sqlalchemy.exc import DataError, IntegrityError
from fileupload.models import FileMetadata, FileMetadataSchema, db
import logging.config
import logging
import yaml
from app import MOD_PATH
from marshmallow.exceptions import ValidationError

f = Magic(mime=True)

ROOT_DIR = os.environ['ROOT_DIR']
LOG_DIR = os.environ['LOG_DIR']
DATA_DIR = os.environ['DATA_DIR']


class FileUpload:

    def __init__(self):
        """
        The file upload service functions encapsulated in a class
        """

        self.setup_logging()
        self.logger = logging.getLogger("fileupload")

    @staticmethod
    def setup_logging(default_path='logging.yml', default_level=logging.INFO):
        """
        A method to setup the logging configurations.

        Arguments:
            default_path -- The yaml logging specification file
            default_level -- The default level for the logging configuration
        """
        path = op.join(MOD_PATH, default_path)
        handlers = [("info_file_handler", "info.log"),
                    ("error_file_handler", "error.log"),
                    ("debug_file_handler", "debug.log"),
                    ("critical_file_handler", "critical.log"),
                    ("warn_file_handler", "warn.log")]

        if op.exists(path):
            if not op.exists(LOG_DIR):
                os.mkdir(LOG_DIR)
            with open(path, 'rt') as file:
                try:
                    config = yaml.safe_load(file.read())
                    for handler, fname in handlers:
                        config['handlers'][handler]['filename'] = f'{LOG_DIR}/{fname}'
                    logging.config.dictConfig(config)
                except Exception:
                    logging.basicConfig(level=default_level)
        else:
            logging.basicConfig(level=default_level)
            logging.warning('Failed to load configuration file. Using default configs')

    def load_index(self):
        """
        A method that will return a string object for a basic request method

        response -- API server description
        """

        return "File Upload service by Reagan Balongcas, GRID Trainee"

    def upload_file(self, upfile):
        """
        The method for a POST request to upload a file.
        It will extract the metadata of the file argument and add
        those information in the database.

        Arguments:
            upfile - The file object sent to the server\

        responses:
            201 -- The uploaded file metadata information
            403 -- File already exist
        """

        self.logger.info(f"Filetype: {type(upfile)}")

        metadata = self.extract_meta(upfile)

        schema = FileMetadataSchema()
        new_file = FileMetadata(
            size=metadata['file_size'],
            file_name=metadata['file_name'],
            sha1=metadata['file_sha1'],
            md5=metadata['file_md5'],
            type=metadata['file_type'],
        )

        try:
            db.session.add(new_file)
            db.session.commit()
            data = schema.dump(new_file)
            data.pop('id')

            self.logger.info(f"File uploaded! {' / '.join([ f'{k}: {e}' for k,e in data.items() ])}")

            self.save_to_host(new_file.id, upfile)

            return jsonify(data), 201
        except DataError:
            db.session.rollback()
            db.session.commit()

            self.logger.error(f"File exist! {' / '.join([ f'{k}: {e}' for k,e in metadata.items() ])}")
            return abort(403, "File already exist!")
        except IntegrityError:
            db.session.rollback()
            db.session.commit()

            self.logger.error(f"File exist! {' / '.join([f'{k}: {e}' for k, e in metadata.items()])}")
            return abort(403, "File already exist!")

    def read_files(self):
        """
        The method for a GET request of retrieving all the uploaded files in the database.
        Metadata information for each file are the response to be expected.


        response:
            200 - List of metadata objects
        """

        all_files = (
            FileMetadata.query.all()
        )

        schema = FileMetadataSchema()

        def remove_id(dct):
            d = schema.dump(dct)
            d.pop('id')
            return d

        data = [remove_id(af) for af in all_files]

        return jsonify(data), 200

    def read_file(self, file_hash):
        """
        Another method for a GET request but for retrieving a single file only

        Argument:
            file_hash -- Hash string format in md5 or sha1

        response:
            200 - The metadata object for the file with given hash
        """
        file = FileMetadata.query.filter(or_(FileMetadata.md5 == file_hash, FileMetadata.sha1 == file_hash)).one_or_none()

        if file:
            schema = FileMetadataSchema()
            data = schema.dump(file)

            data.pop('id')

            return jsonify(data), 200
        else:
            abort(
                404,
                "File not found!"
            )

    def update_file(self, file_hash, file):
        """
        A PUT request dedicated method. It accepts both the hash for a file and the object containing
        the information to be updated

        Argument:
            file_hash -- The hash for a specific file uploaded in the server
            file -- The metadata objects to be updated (file type or filename)

        responses:
            201 - The metadata for the file with the updated fields
            403 - Invalid schema or properties provided
            404 - File not found
        """

        update_file = FileMetadata.query.filter(or_(FileMetadata.md5 == file_hash, FileMetadata.sha1 == file_hash)).one_or_none()

        if update_file:
            old_fname = update_file.file_name[:]

            if len(file) <= 2 and ('file_name' in file or 'type' in file):
                try:
                    schema = FileMetadataSchema()
                    update = schema.load(file, session=db.session, instance=update_file)

                    update.id = update_file.id
                    db.session.merge(update)
                    db.session.commit()
                    data = schema.dump(update)
                    data.pop('id')

                    self.logger.info(f"File updated! {' / '.join([f'{k}: {e}' for k, e in data.items()])}")

                    if 'file_name' in  file:
                        self.rename_file_in_host(update_file.id, old_fname, file['file_name'])

                    return jsonify(data), 201
                except ValidationError:
                    self.logger.error(f"Invalid schema provided!")
                    return abort(
                        403,
                        "Invalid schema provided!"
                    )
            else:
                self.logger.error(f"Invalid properties provided!")
                return abort(
                    403,
                    "Invalid properties provided!"
                )
        else:
            self.logger.error(f"File with hash {file_hash} not found!")
            abort(
                404,
                f"File with {file_hash} not found!"
            )

    def save_to_host(self, file_id, file):
        """
        This method will save the file sent by the request.

        Arguments:
            file_id -- The database id of the uploaded file
            file -- The actual file object
        """
        if op.exists(DATA_DIR):
            dir_path = op.join(DATA_DIR, str(file_id))
            os.mkdir(dir_path)
            file_path = op.join(dir_path, file.filename)
            file.save(file_path)
            self.logger.info(f"File saved in {file_path}")

    def rename_file_in_host(self, id_, old_fname, new_fname):
        """
        An essential method to call under the PUT request method.
        It will rename the existing file stored in the local storage.

        Arguments:
            id_ -- The id of the updated file
            old_fname -- the previous file name
            new_fname -- the new file name
        """
        rename_id = str(id_)
        dir_path = op.join(DATA_DIR, rename_id)
        file_path_old = op.join(dir_path, old_fname)
        file_path_new = op.join(dir_path, new_fname)
        print(file_path_old)
        print(file_path_new)

        if op.isdir(dir_path) and op.isfile(file_path_old):
            os.rename(file_path_old, file_path_new)
            self.logger.info(f"File renamed from {old_fname} to {new_fname}")

    def delete_file(self, file_hash):
        """
        The method dedicated for the DEL request. It will delete the file metadata in the database
        and the file object in the storage based from the given hash.

        Argument:
            file_hash -- md5 or sha1 hash of a specific file

        responses:
            201 - File deletion success
            404 - File not found
        """
        file = FileMetadata.query.filter(or_(FileMetadata.md5 == file_hash, FileMetadata.sha1 == file_hash)).one_or_none()

        if file:
            db.session.delete(file)
            db.session.commit()
            self.delete_file_in_host(file.id)
            self.logger.warning(f"File {file.file_name} deleted!")

            return jsonify(f"File {file.file_name} deleted!"), 201
        else:
            self.logger.error(f"File with hash {file_hash} not found!")
            abort(
                404,
                "File not found!"
            )

    def delete_file_in_host(self, id_):
        """
        The method for deleting the actual file in the storage

        Argument:
            id_ -- The id of the file
        """

        delete_id = str(id_)
        dir_path = op.join(DATA_DIR, delete_id)

        if op.isdir(dir_path):
            shutil.rmtree(dir_path)
            self.logger.warning(f"File in {dir_path} deleted!")

    def extract_meta(self, upfile):
        """
        This will extract the metadata information of the given file

        Argument:
            upfile -- The file object
        """
        with tempfile.TemporaryDirectory() as tmp:
            file_name = upfile.filename

            temp_file = op.join(tmp, file_name)
            upfile.save(temp_file)

            file_size = op.getsize(temp_file)
            file_type = self.extract_file_type(temp_file)
            file_md5 = self.hash_file(temp_file, algorithm="md5")
            file_sha1 = self.hash_file(temp_file)

            return {
                "file_size": file_size,
                "file_name": file_name,
                "file_sha1": file_sha1,
                "file_md5": file_md5,
                "file_type": file_type
            }

    def extract_file_type(self, file):
        """
        Method for extracting the file type of the given file

        Argument:
            file -- The file object
        """
        try:
            return f.from_file(file)
        except MagicException:
            self.logger.error(f"File type for {file.file_name} not found!")
            return "unknown/unknown"

    def hash_file(self, file, algorithm='sha1'):
        """
        Computes the hash of the given file.

        Argument:
            algorithm -- sha1(default) or md5
        """

        block_size = 65536
        if algorithm == 'sha1':
            hasher = hashlib.sha1()
        else:
            hasher = hashlib.md5()

        with open(file, 'rb') as hash_file:
            buf = hash_file.read(block_size)
            while len(buf) > 0:
                hasher.update(buf)
                buf = hash_file.read(block_size)

        return hasher.hexdigest()


fileupload = FileUpload()


def load_index():
    """
    Abstract function to call the method of the
    fileupload object load_index()
    """

    return fileupload.load_index()


def upload_file(upfile):
    """
    Abstract function to call the method of the
    fileupload object upload_file()
    """

    return fileupload.upload_file(upfile)


def read_files():
    """
    Abstract function to call the method of the
    fileupload object read_files()
    """

    return fileupload.read_files()


def read_file(file_hash):
    """
    Abstract function to call the method of the
    fileupload object read_file()
    """

    return fileupload.read_file(file_hash)


def update_file(file_hash, file):
    """
    Abstract function to call the method of the
    fileupload object update_file()
    """

    return fileupload.update_file(file_hash, file)


def delete_file(file_hash):
    """
    Abstract function to call the method of the
    fileupload object delete_file()
    """

    return fileupload.delete_file(file_hash)









