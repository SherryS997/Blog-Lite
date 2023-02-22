from flask_sqlalchemy import SQLAlchemy
from application.database import db

class User(db.Model):
    __tablename__ = 'user'
    roll = db.Column(db.Integer, primary_key=True, autoincrement=True)
    username = db.Column(db.String, unique=True, nullable=False)
    password = db.Column(db.String, nullable=False)
    img = db.Column(db.String)

class Post(db.Model):
    __tablename__ = 'post'
    roll = db.Column(db.Integer, primary_key=True, autoincrement=True)
    author = db.Column(db.String, db.ForeignKey("user.username"), nullable=False)
    img = db.Column(db.String)
    text = db.Column(db.String, nullable=False)
    date = db.Column(db.String)
    title = db.Column(db.String, nullable=False)
    views = db.Column(db.Integer, nullable=False)

class Comment(db.Model):
    __tablename__ = 'comment'
    roll = db.Column(db.Integer, primary_key=True, autoincrement=True)
    author = db.Column(db.String, nullable=False)
    post = db.Column(db.Integer, nullable=False)
    comment = db.Column(db.String, nullable=False)

class Follow(db.Model):
    __tablename__ = 'follow'
    roll = db.Column(db.Integer, primary_key=True, autoincrement=True)
    following = db.Column(db.Integer, db.ForeignKey("user.roll"), nullable=False)
    follower = db.Column(db.Integer, db.ForeignKey("user.roll"), nullable=False)

class Token(db.Model):
    __tablename__ = 'token'
    user = db.Column(db.Integer, db.ForeignKey("user.roll"), primary_key=True, nullable=False)
    token = db.Column(db.String, nullable=False, unique=True)
