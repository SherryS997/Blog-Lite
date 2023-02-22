from flask import Flask
from application.database import db
from flask_restful import Api
from flask_cors import CORS
from application.config import UPLOAD_FOLDER, KEY, DB

def create_app(UPLOAD_FOLDER, KEY, DB):
    app = Flask(__name__)
    CORS(app)
    app.config['SQLALCHEMY_DATABASE_URI'] = DB
    app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
    app.config['CORS_HEADERS'] = 'Content-Type'
    with open(KEY) as f:
        key = f.readline()
        app.secret_key = bytes(key, 'utf-8')
    db.init_app(app)
    app.app_context().push()
    return app

app = create_app(UPLOAD_FOLDER, KEY, DB)

from application.controllers import *

from application.api import UserAPI, PostAPI, CommentAPI, FollowerAPI, FollowingAPI

api = Api(app)
app.app_context().push()
api.add_resource(UserAPI, "/api/user/<username>", "/api/user")
api.add_resource(PostAPI, "/api/post/<int:post_id>", "/api/post", "/api/post/<username>")
api.add_resource(CommentAPI, "/api/post/<int:post_id>/comment")
api.add_resource(FollowerAPI, "/api/user/<username>/followers")
api.add_resource(FollowingAPI, "/api/user/<username>/follows")


if __name__ == "__main__":
    app.run(host='0.0.0.0', port=2345)
