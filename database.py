from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin


db=SQLAlchemy()
def CreateDBApp(app):
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///project.sqlite3'
    db.init_app(app)
    with app.app_context():
        db.create_all()
    return db
# Need to define tables
class Category(db.Model):
    __tablename__='category'
    id=db.Column(db.Integer, primary_key=True, autoincrement=True)
    name=db.Column(db.String, nullable=False)
    # one to many mapping between category and product
    products=db.relationship('Product', backref='category', lazy=True)

class Product(db.Model):
    __tablename__='product'
    id=db.Column(db.Integer, primary_key=True, autoincrement=True)
    quantity=db.Column(db.Integer, nullable=False)
    name=db.Column(db.String, nullable=False)
    manufacture=db.Column(db.DateTime, nullable=False)
    expiry=db.Column(db.DateTime, nullable=False)
    rpu=db.Column(db.Float, nullable=False)
    unit = db.Column(db.String, nullable=False)
    image=db.Column(db.String, nullable=False)
    category_id=db.Column(db.Integer, db.ForeignKey('category.id'))
    owner_id=db.Column(db.Integer, db.ForeignKey('user.id'))

class User(UserMixin,db.Model):
    __tablename__='user'
    id=db.Column(db.Integer, primary_key=True, autoincrement=True)
    email = db.Column(db.String(100), unique=True)
    password = db.Column(db.String(100))
    name = db.Column(db.String(1000))
    role=db.Column(db.String)
    # one to many mapping between user and product
    purchased=db.relationship('Product', backref='product', lazy=True)
    