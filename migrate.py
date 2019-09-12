from flask_migrate import MigrateCommand, Migrate
from flask_script import Manager
from app import create_app, create_db
from app.config import db
from fileupload.models import FileMetadata


app_db = create_app().app

create_db()

migrate = Migrate(app_db, db)
manager = Manager(app_db)
manager.add_command('db', MigrateCommand)

if __name__ == "__main__":
    manager.run()
