from flask import Flask
from config import Config
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
import warnings
from sqlalchemy.exc import SAWarning
warnings.filterwarnings('ignore',
 r"^Dialect sqlite\+pysqlite does \*not\* support Decimal objects natively\, "
 "and SQLAlchemy must convert from floating point - rounding errors and other "
 "issues may occur\. Please consider storing Decimal numbers as strings or "
 "integers on this platform for lossless storage\.$",
 SAWarning, r'^sqlalchemy\.sql\.type_api$')

app = Flask(__name__)
app.config.from_object(Config)
db = SQLAlchemy(app)
migrate = Migrate(app, db)

from app import routes, models
