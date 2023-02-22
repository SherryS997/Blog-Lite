from flask_restful import Resource, fields, marshal_with, request, reqparse
from application.models import User, Post, Comment, Follow, Token
from application.database import db
from application.validation import BusinessValidationError, NotFoundError, DuplicationError, NotAuthorizedError
from application.controllers import allowed_file_img, allowed_file_txt
from application.config import UPLOAD_FOLDER
from passlib.hash import pbkdf2_sha256 as passhash
import secrets
import os
import datetime as dt


user_fields = {
    "roll": fields.Integer,
    "username": fields.String,
    "img": fields.String
}

class UserAPI(Resource):
 
    @marshal_with(user_fields)
    def get(self, username):
        user = User.query.filter_by(username=username).first()
        if user:
            return user
        else:
            raise NotFoundError(404, "User not found")

    @marshal_with(user_fields)
    def put(self):
        if "Authorization" not in request.headers:
            raise NotAuthorizedError(401, "No Token Provided")
        auth = request.headers["Authorization"].split()[1]
        token_id = Token.query.filter_by(token=auth).first()
        if token_id == None:
            raise NotAuthorizedError(401, "Invalid Token")
        user = User.query.filter_by(roll=token_id.user).first()
        if user == None:
            raise NotFoundError(404, "User not found")
        if "New Username" in request.form:
            if request.form["New Username"]:
                posts = Post.query.filter_by(author = user.username).all()
                comments = Comment.query.filter_by(author = user.username).all()
                user.username = request.form["New Username"]
                for comment in comments:
                    comment.author = request.form["New Username"]
                for post in posts:
                    post.author = request.form["New Username"]
        
        if "New Password" in request.form:
            if request.form["New Password"]:
                if len(request.form["New Password"]) < 4:
                    raise BusinessValidationError(400, "USER002", "Password should be at least 4 characters long")
                user.password = passhash.hash(request.form["New Password"])

        if "New Image" in request.files:
            if request.files["New Image"]:
                file = request.files["New Image"]
                if not allowed_file_img(file.filename):
                    raise BusinessValidationError(400, "USER001", "Invalid file type")
                if int(user.img) == 0:
                    user.img = str(user.roll)
                file.save(os.path.join(UPLOAD_FOLDER+"Users/", user.img +".jpg"))

        db.session.commit()

        return user
    
    def delete(self):
        if "Authorization" not in request.headers:
            raise NotAuthorizedError(401, "No Token Provided")
        auth = request.headers["Authorization"].split()[1]
        token_id = Token.query.filter_by(token=auth).first()
        if token_id == None:
            raise NotAuthorizedError(401, "Invalid Token")
        user = User.query.filter_by(roll=token_id.user).first()
        if user == None:
            raise NotFoundError(404, "User not found")
        posts = Post.query.filter_by(author=user.username).all()
        comments = Comment.query.filter_by(author=user.username).all()
        Token.query.filter_by(user=user.roll).delete()
        Follow.query.filter_by(follower=user.roll).delete()
        Follow.query.filter_by(following=user.roll).delete()
        for comment in comments:
            comment.author = "[deleted]"
        for post in posts:
            post.author = "[deleted]"
        if int(user.img) != 0:
            os.remove(UPLOAD_FOLDER+"Users/" + user.img +".jpg")
        user = User.query.filter_by(username=user.username)
        Token.query.filter_by(user=user.first().roll).delete()
        user.delete()
        db.session.commit()
        return "Successfully Deleted"

    @marshal_with(user_fields)
    def post(self):
        if "Username" not in request.form:
            raise BusinessValidationError(400, "USER003", "Username is required")
        
        if "Password" not in request.form:
            raise BusinessValidationError(400, "USER002", "Password should be at least 4 characters long")
        
        if len(request.form["Password"]) < 4:
            raise BusinessValidationError(400, "USER002", "Password should be at least 4 characters long")

        test = User.query.filter_by(username=request.form["Username"]).first()
        if test != None:
            raise DuplicationError(409, "Username already exists")
        
        user = User(username=request.form["Username"], password=passhash.hash(request.form["Password"]), img=0)
        db.session.add(user)
        db.session.commit()
        db.session.add(Token(user=user.roll, token=secrets.token_urlsafe(32)))
        db.session.commit()

        if "Image" in request.files:
            if request.files["Image"]:
                file = request.files["Image"]
                if not allowed_file_img(file.filename):
                    raise BusinessValidationError(400, "USER001", "Invalid file type")
                user = User.query.filter_by(username=request.form["Username"]).first()
                if int(user.img) == 0:
                    user.img = str(user.roll)
                file.save(os.path.join(UPLOAD_FOLDER+"Users/", user.img +".jpg"))
                db.session.commit()

        return user


post_fields = {
    "title": fields.String,
    "text": fields.String,
    "author": fields.String,
    "date": fields.String,
    "img": fields.String,
    "views": fields.Integer
}

class PostAPI(Resource):
    @marshal_with(post_fields)
    def get(self, post_id):
        post = Post.query.filter_by(roll=post_id).first()
        post.views += 1
        db.session.commit()
        if post:
            return post
        else:
            raise NotFoundError(404, "Post not found")

    @marshal_with(post_fields)
    def get(self, username):
        user = User.query.filter_by(username=username).first()
        if not user:
            raise NotFoundError(404, "User not found")
        posts = Post.query.filter_by(author=username).all()
        return [post for post in posts]

    @marshal_with(post_fields)
    def put(self, post_id):
        if "Authorization" not in request.headers:
            raise NotAuthorizedError(401, "No Token Provided")
        auth = request.headers["Authorization"].split()[1]
        token_id = Token.query.filter_by(token=auth).first()
        if token_id == None:
            raise NotAuthorizedError(401, "Invalid Token")
        user = User.query.filter_by(roll=token_id.user).first()
        if user == None:
            raise NotFoundError(404, "User not found")
        post = Post.query.filter_by(roll=post_id).first()
        if post == None:
            raise NotFoundError(404, "Post not found")
        if "Title" in request.form and request.form["Title"].strip():
            post.title = request.form["Title"]

        if "Text" in request.files and request.files["Text"]:
            out = request.files["Text"].read().decode('utf8')
            post.text = out

        if "New Image" in request.files and request.files["New Image"]:
            if not allowed_file_img(request.files["New Image"].filename):
                raise BusinessValidationError(400, "POST001", "Invalid file type")
            request.files["New Image"].save(os.path.join(UPLOAD_FOLDER +"Posts/", post.img +".jpg"))

        db.session.commit()

        return post
    
    def delete(self, post_id):
        if "Authorization" not in request.headers:
            raise NotAuthorizedError(401, "No Token Provided")
        auth = request.headers["Authorization"].split()[1]
        token_id = Token.query.filter_by(token=auth).first()
        if token_id == None:
            raise NotAuthorizedError(401, "Invalid Token")
        user = User.query.filter_by(roll=token_id.user).first()
        if user:
            post = Post.query.filter_by(roll=post_id).first()
            if not post:
                raise NotFoundError(404, "Post not found")
            if post.author != user.username:
                raise NotAuthorizedError(401, "Invalid Token")
            os.remove(UPLOAD_FOLDER +"Posts/" + post.img +".jpg")
            post = Post.query.filter_by(roll=post_id)
            Comment.query.filter_by(post=post_id).delete()
            post.delete()
            db.session.commit()
            return "Successfully Deleted"
        else:
            raise NotFoundError(404, "User not found")

    @marshal_with(post_fields)
    def post(self):
        if "Authorization" not in request.headers:
            raise NotAuthorizedError(401, "No Token Provided")
        auth = request.headers["Authorization"].split()[1]
        token_id = Token.query.filter_by(token=auth).first()
        if token_id == None:
            raise NotAuthorizedError(401, "Invalid Token")
        user = User.query.filter_by(roll=token_id.user).first()
        username = user.username
        if user:
            last_post = Post.query.order_by(Post.roll.desc()).first()
            day = str(dt.datetime.now().day) if len(str(dt.datetime.now().day)) > 1 else "0" + str(dt.datetime.now().day)
            month = str(dt.datetime.now().month) if len(str(dt.datetime.now().month)) > 1 else "0" + str(dt.datetime.now().month)
            date = str(dt.datetime.now().year)+"-"+month+"-"+day
            filename = str(last_post.roll + 1)
            file = request.files["Image"]
            title = request.form["Title"]
            content = request.files["Text"]
            if allowed_file_txt(content.filename):
                content = request.files["Text"].read().decode('utf8')
                if not allowed_file_img(file.filename):
                    raise BusinessValidationError(400, "POST001", "Invalid file type")
                post = Post(author=username, img=filename, text=content, date=date, title=title, views=0)
                file.save(os.path.join(UPLOAD_FOLDER+"Posts/", filename+".jpg"))
                db.session.add(post)
                db.session.commit()

                return post
            else:
                raise BusinessValidationError(400, "POST001", "Invalid file type")
        else:
            raise NotFoundError(404, "User not found")

comment_fields = {
    "author": fields.String,
    "post": fields.Integer,
    "comment": fields.String
}

comparse = reqparse.RequestParser()
comparse.add_argument("Comment")

class CommentAPI(Resource):
    @marshal_with(comment_fields)
    def get(self, post_id):
        post = Post.query.filter_by(roll=post_id).first()
        if not post:
            raise NotFoundError(404, "Post not found")
        comments = Comment.query.filter_by(post=post_id).order_by(Comment.roll.asc()).all()

        return [comment for comment in comments]

    @marshal_with(comment_fields)
    def post(self, post_id):
        if "Authorization" not in request.headers:
            raise NotAuthorizedError(401, "No Token Provided")
        auth = request.headers["Authorization"].split()[1]
        token_id = Token.query.filter_by(token=auth).first()
        if token_id == None:
            raise NotAuthorizedError(401, "Invalid Token")
        user = User.query.filter_by(roll=token_id.user).first()
        username = user.username
        post = Post.query.filter_by(roll=post_id).first()
        if not post:
            raise NotFoundError(404, "Post not found")
        comment = comparse.parse_args().get("Comment", None)
        user = User.query.filter_by(username=username).first()
        if not user:
            raise BusinessValidationError(400, "COMMENT001", "Invalid Username")
        if not comment:
            raise BusinessValidationError(400, "COMMENT002", "No Comment Provided")

        comment = Comment(author=user.username, post=post_id, comment=comment)
        db.session.add(comment)
        db.session.commit()

        return [comment]

follow_fields = {
    "following": fields.Integer,
    "follower": fields.Integer
}

class FollowerAPI(Resource):
    @marshal_with(follow_fields)
    def get(self, username):
        user = User.query.filter_by(username = username).first()
        if not user:
            raise NotFoundError(404, "User not found")
        following = Follow.query.filter_by(following=user.roll).all()

        return [follow for follow in following]

class FollowingAPI(Resource):
    @marshal_with(follow_fields)
    def get(self, username):
        user = User.query.filter_by(username = username).first()
        if not user:
            raise NotFoundError(404, "User not found")
        follows = Follow.query.filter_by(follower=user.roll).all()

        return [follow for follow in follows]

    @marshal_with(follow_fields)
    def post(self, username):
        user = User.query.filter_by(username = username).first()
        if not user:
            raise BusinessValidationError(400, "COMMENT001", "Invalid Username")
        password = request.form["Password"]
        follow = request.form["Follow"]
        follow = User.query.filter_by(username=follow).first()
        if not passhash.verify(password, user.password):
            raise NotAuthorizedError(401, "Invalid Password")
        if not follow:
            raise NotFoundError(404, "User not found")

        test = Follow.query.filter_by(follower=user.roll, following=follow.roll).first()
        if test:
            raise DuplicationError(409, "Follow already exists")

        follow = Follow(follower=user.roll, following=follow.roll)
        db.session.add(follow)
        db.session.commit()

        return [follow]

    def delete(self, username):
        user = User.query.filter_by(username = username).first()
        if not user:
            raise BusinessValidationError(400, "COMMENT001", "Invalid Username")
        password = request.form["Password"]
        follow = request.form["Follow"]
        follow = User.query.filter_by(username=follow).first()
        if not passhash.verify(password, user.password):
            raise NotAuthorizedError(401, "Invalid Password")
        if not follow:
            raise NotFoundError(404, "User not found")

        test = Follow.query.filter_by(follower=user.roll, following=follow.roll).first()
        if not test:
            raise NotFoundError(404, "Follow not found")

        Follow.query.filter_by(follower=user.roll, following=follow.roll).delete()
        db.session.commit()

        return "Successfully deleted"

