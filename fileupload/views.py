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
        self.setup_logging()
        self.logger = logging.getLogger("fileupload")

    def setup_logging(self, default_path='logging.yml', default_level=logging.INFO):
        path = op.join(MOD_PATH, default_path)
        handlers = [("info_file_handler", "info.log"),
                    ("error_file_handler", "error.log"),
                    ("debug_file_handler", "debug.log"),
                    ("critical_file_handler", "critical.log"),
                    ("warn_file_handler", "warn.log")]

        if op.exists(path):
            with open(path, 'rt') as f:
                try:
                    config = yaml.safe_load(f.read())
                    for handler, fname in handlers:
                        config['handlers'][handler]['filename'] = f'{LOG_DIR}/{fname}'
                    logging.config.dictConfig(config)
                except Exception as e:
                    logging.basicConfig(level=default_level)
        else:
            logging.basicConfig(level=default_level)
            logging.warning('Failed to load configuration file. Using default configs')

    #
    def load_index(self):
        return "<h4>File Upload service by Reagan Balongcas, GRID Trainee</h4>"

    #
    def upload_file(self, upfile):
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
        except DataError as e:
            db.session.rollback()
            db.session.commit()

            self.logger.error(f"File exist! {' / '.join([ f'{k}: {e}' for k,e in metadata.items() ])}")
            return abort(403, "File already exist!")
        except IntegrityError as e:
            db.session.rollback()
            db.session.commit()

            self.logger.error(f"File exist! {' / '.join([f'{k}: {e}' for k, e in metadata.items()])}")
            return abort(403, "File already exist!")

    #
    def read_files(self, ):

            all_files = (
                FileMetadata.query.all()
            )

            schema = FileMetadataSchema()

            def remove_id(dct):
                d = schema.dump(dct)
                d.pop('id')
                return d

            data = [remove_id(af) for af in all_files]

            return data

    def read_file(self, hash):
        file = FileMetadata.query.filter(or_(FileMetadata.md5 == hash, FileMetadata.sha1 == hash)).one_or_none()

        if file:
            schema = FileMetadataSchema()
            data = schema.dump(file)

            data.pop('id')

            return data
        else:
            abort(
                404,
                "File not found!"
            )

    def update_file(self, hash, file):

        update_file = FileMetadata.query.filter(or_(FileMetadata.md5 == hash, FileMetadata.sha1 == hash)).one_or_none()

        if update_file:
            if file['file_name']:
                self.rename_file_in_host(update_file.id, update_file.file_name, file['file_name'])

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

                    return jsonify(data), 201
                except ValidationError:
                    if file['file_name']:
                        self.logger.error(f"Invalid schema provided!")
                        self.rename_file_in_host(update_file.id, update_file.file_name, file['file_name'],post=True)
                        return abort(
                            403,
                            "Invalid schema provided!"
                        )
            else:
                return abort(
                    403,
                    "Invalid properties provided!"
                )
        else:
            abort(
                404,
                "File not found!"
            )

    def delete_file(self, hash):

        file = FileMetadata.query.filter(or_(FileMetadata.md5 == hash, FileMetadata.sha1 == hash)).one_or_none()

        if file:
            db.session.delete(file)
            db.session.commit()
            self.delete_file_in_host(file.id)
            self.logger.warning(f"File {file.file_name} deleted!")

            return jsonify(f"File {file.file_name} deleted!"), 201
        else:
            abort(
                404,
                "File not found!"
            )

    def save_to_host(self, file_id, file):
        if op.exists(DATA_DIR):
            dir_path = op.join(DATA_DIR, str(file_id))
            os.mkdir(dir_path)
            file_path = op.join(dir_path, file.filename)
            file.save(file_path)
            self.logger.info(f"File saved in {file_path}")

    def delete_file_in_host(self, id):
        delete_id = str(id)
        dir_path = op.join(DATA_DIR, delete_id)

        if op.isdir(dir_path):
            shutil.rmtree(dir_path)
            self.logger.warning(f"File in {dir_path} deleted!")

    def rename_file_in_host(self, id, old_fname, new_fname, post=False):
        rename_id = str(id)
        dir_path = op.join(DATA_DIR, rename_id)
        file_path_old = op.join(dir_path, old_fname)
        file_path_new = op.join(dir_path, new_fname)
        if post:
            if op.isdir(dir_path) and op.isfile(file_path_new):
                os.remove(file_path_new)
        else:
            if op.isdir(dir_path) and op.isfile(file_path_old):
                try:
                    shutil.copy2(file_path_old, file_path_new)
                    self.logger.info(f"File renamed from {old_fname} to {new_fname}")
                except shutil.SameFileError:
                    self.logger.error(f"File {old_fname} and {new_fname} are of the same file name")

    def extract_meta(self, upfile):
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
        try:
            return f.from_file(file)
        except MagicException:
            return "unknown/unknown"


    def hash_file(self, file, algorithm='sha1'):
        """The method for computing the checksum hashing of the file depending on the algorithm provided

        Keyword arguments:
        file -- the directory path for recursive listing
        algorithm -- the algorithm to use (default 'md5')
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
    return fileupload.load_index()


def upload_file(upfile):
    return fileupload.upload_file(upfile)


def read_files():
    return fileupload.read_files()


def read_file(hash):
    return fileupload.read_file(hash)


def update_file(hash, file):
    return fileupload.update_file(hash, file)


def delete_file(hash):
    return fileupload.delete_file(hash)









