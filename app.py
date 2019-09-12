from flask_migrate import Migrate
from app.config import db, connex_app

migrate = Migrate(connex_app.app, db)

connex_app.add_api("swagger.yml")

if __name__ == "__main__":
    connex_app.run(debug=True)
    