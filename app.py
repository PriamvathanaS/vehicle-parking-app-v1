from flask import Flask
from controller.database import db
import os
 
app = None

def create_app():
    app = Flask(__name__, instance_relative_config=True)
    app.debug = True
    db_path = os.path.join(app.instance_path, "parking.db")
    app.config["SQLALCHEMY_DATABASE_URI"] = f"sqlite:///{db_path}"
    db.init_app(app)
    app.app_context().push()
    return app

app = create_app()
from controller.model import *

# Create all database tables
db.create_all()

if __name__ == "__main__":
    app.run()