from flask import request, redirect, render_template, url_for, session, send_from_directory
from flask import current_app as app
from passlib.hash import pbkdf2_sha256 as passhash
from application.models import db, User, Post, Comment, Follow, Token
from application.config import ALLOWED_EXTENSIONS_IMG, ALLOWED_EXTENSIONS_TXT
import csv
import secrets
import matplotlib.pyplot as plt
import datetime as dt
import os

def allowed_file_img(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS_IMG

def allowed_file_txt(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS_TXT

@app.route('/', methods=["GET", "POST"])
def home():
    if "user" in session:
        return redirect("/user=" + session["user"])
    contents = db.session.query(Post, User).filter(Post.author==User.username).order_by(Post.roll.desc()).limit(6)
    return render_template("discover.html", contents=contents)

@app.route('/discover', methods=["GET", "POST"])
def discover():
    if "user" in session:
        user = User.query.filter_by(username=session["user"]).first()
        contents = db.session.query(Post, User).filter(Post.author==User.username).order_by(Post.roll.desc()).limit(6)
        if request.method == "GET":
            follows = Follow.query.filter_by(follower=user.roll).all()
            follows = [follow.following for follow in follows]
            return render_template("discover.html", contents=contents, state=True, username=user.username, img=user.img, follows=follows)
        elif request.method == "POST":
            if "search" in request.form:
                return redirect("/search=" + request.form["search"])
            else:
                if "unfollow" in request.form:
                    following = User.query.filter_by(username=request.form["unfollow"]).first()
                    follow = Follow.query.filter_by(follower=user.roll, following=following.roll)
                    follow.delete()
                else:
                    following = User.query.filter_by(username=request.form["follow"]).first()
                    follow = Follow(follower=user.roll, following=following.roll)
                    db.session.add(follow)
                db.session.commit()
                return redirect("/discover")
    else:
        return redirect("/")

@app.route('/user=<username>', methods=["GET", "POST"])
def user_home(username):
    if "user" in session and username==session["user"]:
        user = User.query.filter_by(username=username).first()
        follows = Follow.query.filter_by(follower=user.roll).all()
        follows = [follow.following for follow in follows]
        follows = [User.query.filter_by(roll=follow).first().username for follow in follows]
        contents = db.session.query(Post, User).filter(Post.author==User.username, Post.author.in_(follows)).order_by(Post.roll.desc()).limit(6)
        if request.method == "GET":
            follows = Follow.query.filter_by(follower=user.roll).all()
            follows = [follow.following for follow in follows]
            return render_template("home.html", contents=contents, state=True, username=user.username, img=user.img, follows=follows)
        elif request.method == "POST":
            if "search" in request.form:
                return redirect("/search=" + request.form["search"])
            elif "unfollow" in request.form:
                following = User.query.filter_by(username=request.form["unfollow"]).first()
                follow = Follow.query.filter_by(follower=user.roll, following=following.roll)
                follow.delete()
            else:
                following = User.query.filter_by(username=request.form["follow"]).first()
                follow = Follow(follower=user.roll, following=following.roll)
                db.session.add(follow)
            db.session.commit()
            return redirect("/")
    else:
        return redirect("/")

@app.route('/login', methods=["GET", "POST"])
def login():
    if request.method == "GET":
        return render_template("login.html")
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]
        out = User.query.filter_by(username=username).first()
        if out is None:
            return render_template("login.html", username_error=True)
        if not passhash.verify(password, out.password):
            return render_template("login.html", pwd_error=True)
        session["user"] = username
        return redirect("/user="+username)

@app.route('/signup', methods=["GET", "POST"])
def signup():
    if request.method == "GET":
        return render_template("signup.html")
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]
        password2 = request.form["password2"]
        if password != password2:
            return render_template("signup.html", pwd_error=True)
        user = User.query.filter_by(username=username).first()
        if user is not None:
            return render_template("signup.html", username_error=True)
        password = passhash.hash(password)
        user = User(username=username, password=password, img=0)
        db.session.add(user)
        db.session.commit()
        db.session.add(Token(user=user.roll, token=secrets.token_urlsafe(32)))
        db.session.commit()
        session["user"] = username
        return redirect("/user="+username)

@app.route('/user=<username>/account', methods = ["GET", "POST"])
def account(username):
    user = User.query.filter_by(username=username).first()
    if username == "[deleted]" or user == None:
        return redirect(url_for("home"))
    posts = Post.query.filter_by(author=username).order_by(Post.roll.desc()).all()
    following = len(Follow.query.filter_by(following=user.roll).order_by(Follow.follower).all())
    follower = len(Follow.query.filter_by(follower=user.roll).order_by(Follow.following).all())
    if "user" in session :
        if request.method == "GET":
            cur_user = User.query.filter_by(username=session["user"]).first()
            followed = Follow.query.filter_by(following=user.roll, follower=cur_user.roll).first()
            if username==session["user"]:
                return render_template("account.html", user = user, posts = posts, cur=True, following=following, follower=follower)
            else:
                return render_template("account.html", user = user, posts = posts, followed = followed, following=following, follower=follower, signed=True)
        elif request.method == "POST":
            if "unfollow" in request.form:
                follower = User.query.filter_by(username=session["user"]).first()
                follow = Follow.query.filter_by(follower=follower.roll, following=user.roll)
                follow.delete()
            else:
                follower = User.query.filter_by(username=session["user"]).first()
                follow = Follow(follower=follower.roll, following=user.roll)
                db.session.add(follow)
            db.session.commit()
            return redirect("/user=" + user.username + "/account")
    else:
        return render_template("account.html", user = user, posts = posts, following=following, follower=follower)

@app.route('/user=<username>/account/edit', methods = ["GET", "POST"])
def edit_acc(username):
    if "user" in session and username==session["user"]:
        user = User.query.filter_by(username=username).first()
        posts = Post.query.filter_by(author=username).all()
        comments = Comment.query.filter_by(author=user.username).all()
        if request.method == "GET":
            return render_template("edit_user.html", user=user)
        if request.method == "POST":
            if request.files["file"]:
                if not allowed_file_img(request.files["file"].filename):
                    return render_template("edit_user.html", user=user, pic_error=True)
                if int(user.img) == 0:
                    user.img = str(user.roll)
                request.files["file"].save(os.path.join(app.config['UPLOAD_FOLDER']+"Users/", user.img +".jpg"))
            name = request.form["username"]
            if name != user.username and User.query.filter_by(username=name).first():
                return render_template("edit_user.html", user=user, username_error=True)
            user.username = name
            for comment in comments:
                comment.author=name
            for post in posts:
                post.author = name
            session["user"] = name
            db.session.commit()
            return redirect("/user=" + user.username + "/account")
    else:
        return redirect(url_for("home"))

@app.route('/logout', methods = ["GET"])
def logout():
    if "user" in session:
        session.pop("user", None)
    return redirect(url_for("home"))

@app.route('/post/<post_id>', methods = ["GET", "POST"])
def post(post_id):
    post = db.session.query(Post, User).filter(Post.author==User.username).filter(Post.roll==post_id).first()
    comments = Comment.query.filter_by(post=post_id).order_by(Comment.roll.asc()).all()
    if request.method == "GET":
        post.Post.views += 1
        db.session.commit()
        return render_template("post.html", post = post, comments=comments, user=(session["user"] if "user" in session else None))
    elif request.method == "POST":
        comment = request.form["comment"]
        comment = Comment(post=post_id, author=session["user"], comment=comment)
        db.session.add(comment)
        db.session.commit()
        comments = Comment.query.filter_by(post=post_id).all()
        return render_template("post.html", post = post, comments=comments, user=(session["user"] if "user" in session else None))

@app.route('/user=<username>/upload_blog', methods=["GET", "POST"])
def upload_blog(username):
    if "user" in session and session["user"] == username:
        if request.method == "GET":
            return render_template("upload.html", error=False)
        elif request.method == "POST":
            last_post = Post.query.order_by(Post.roll.desc()).first()
            day = str(dt.datetime.now().day) if len(str(dt.datetime.now().day)) > 1 else "0" + str(dt.datetime.now().day)
            month = str(dt.datetime.now().month) if len(str(dt.datetime.now().month)) > 1 else "0" + str(dt.datetime.now().month)
            date = str(dt.datetime.now().year)+"-"+month+"-"+day
            filename = str(last_post.roll + 1)
            file = request.files["file"]
            title = request.form["title"]
            content = request.form["content"]
            if not allowed_file_img(file.filename):
                return render_template("upload.html", error=True)
            post = Post(author=username, img=filename, text=content, date=date, title=title, views=0)
            file.save(os.path.join(app.config['UPLOAD_FOLDER']+"Posts/", filename+".jpg"))
            db.session.add(post)
            db.session.commit()
            return redirect(url_for("home"))
    else:
        return redirect(url_for("home"))

@app.route('/post=<post_id>/edit', methods=["GET", "POST"])
def edit_post(post_id):
    post = Post.query.filter_by(roll=post_id).first()
    if "user" in session and session["user"] == post.author: 
        if request.method == "GET":
            return render_template("post_edit.html", post = post, user=session["user"])
        elif request.method == "POST":
            if request.files["file"]:
                if not allowed_file_img(request.files["file"].filename):
                    return render_template("post_edit.html", post = post, error=True, user=session["user"])
                request.files["file"].save(os.path.join(app.config['UPLOAD_FOLDER']+"Posts/", post.img +".jpg"))
            post.title = request.form["title"]
            post.text = request.form["content"]
            db.session.commit()
            return redirect(url_for("home"))
    else:
        return redirect(url_for("home"))

@app.route('/user=<username>/account/password', methods=["GET", "POST"])
def change_psw(username):
    user = User.query.filter_by(username=username).first()
    if "user" in session and session["user"] == user.username:
        if request.method == "GET":
            return render_template("edit_psw.html", user=session["user"])
        if request.method == "POST":
            ori = request.form["original"]
            if not passhash.verify(ori, user.password):
                return render_template("edit_psw.html",
                                        pwd_error=True,
                                        user=session["user"])
            password = request.form["password"]
            password2 = request.form["password2"]
            if password == "":
                return render_template("edit_psw.html",
                                        password_error=True,
                                        user=session["user"])
            if password != password2:
                return render_template("edit_psw.html",
                                verify=True,
                                user=session["user"])
            password = passhash.hash(password)
            user.password = password
            db.session.commit()
            return redirect("/user=" + user.username + "/account")
    else:
        return redirect(url_for("home"))
        
@app.route("/user=<username>/account/delete", methods=["GET", "POST"])
def del_acc(username):
    user = User.query.filter_by(username=username).first()
    if "user" in session and session["user"] == user.username:
        if request.method == "GET":
            return render_template("del_acc.html", user=session["user"])
        if request.method == "POST":
            posts = Post.query.filter_by(author=user.username).all()
            comments = Comment.query.filter_by(author=user.username).all()
            Follow.query.filter_by(follower=user.roll).delete()
            Follow.query.filter_by(following=user.roll).delete()
            for comment in comments:
                comment.author = "[deleted]"
            for post in posts:
                post.author = "[deleted]"
            if int(user.img) != 0:
                os.remove(app.config['UPLOAD_FOLDER']+"Users/" + user.img +".jpg")
            user = User.query.filter_by(username=user.username)
            Token.query.filter_by(user=user.first().roll).delete()
            user.delete()
            db.session.commit()
            session.pop("user", None)
            return redirect(url_for("home"))
    else:
        return redirect(url_for("home"))

@app.route('/post=<post_id>/delete', methods=["GET", "POST"])
def del_post(post_id):
    post = Post.query.filter_by(roll=post_id).first()
    user = User.query.filter_by(username=post.author).first()
    if "user" in session and session["user"] == user.username:
        if request.method == "GET":
            return render_template("del_post.html", user=session["user"])
        if request.method == "POST":
            os.remove(app.config['UPLOAD_FOLDER'] +"Posts/" + post.img +".jpg")
            post = Post.query.filter_by(roll=post_id)
            Comment.query.filter_by(post=post_id).delete()
            post.delete()
            db.session.commit()
            return redirect("/user=" + user.username + "/account")
    else:
        return redirect(url_for('home'))

@app.route('/search=<term>', methods=["GET"])
def search(term):
    users = User.query.filter(User.username.like("%"+term+"%")).all()
    posts = Post.query.filter(Post.title.like("%"+term+"%")).all()
    follows = dict()
    followers = dict()
    articles = dict()
    for user in users:
        temp = len(Follow.query.filter(Follow.following == user.roll).all())
        follows[user.roll] = temp
        temp = len(Follow.query.filter(Follow.follower == user.roll).all())
        followers[user.roll] = temp
        temp = len(Post.query.filter_by(author = user.username).all())
        articles[user.roll] = temp
    return render_template("search.html", users = users, followers=followers, follows=follows, articles=articles, posts=posts)

@app.route('/user=<username>/account/followers', methods=["GET"])
def followers(username):
    user = User.query.filter_by(username=username).first()
    follows = Follow.query.filter_by(following=user.roll).all()
    follows = tuple([follow.follower for follow in follows])
    users = User.query.filter(User.roll.in_(follows)).all()
    follows = dict()
    followers = dict()
    articles = dict()
    for user in users:
        temp = len(Follow.query.filter(Follow.following == user.roll).all())
        follows[user.roll] = temp
        temp = len(Follow.query.filter(Follow.follower == user.roll).all())
        followers[user.roll] = temp
        temp = len(Post.query.filter_by(author = user.username).all())
        articles[user.roll] = temp
    return render_template("follow.html", username=username, users = users, followers=followers, follows=follows, articles=articles, title="Followers")

@app.route('/user=<username>/account/following')
def following(username):
    user = User.query.filter_by(username=username).first()
    follows = Follow.query.filter_by(follower=user.roll).all()
    follows = tuple([follow.following for follow in follows])
    users = User.query.filter(User.roll.in_(follows)).all()
    follows = dict()
    followers = dict()
    articles = dict()
    for user in users:
        temp = len(Follow.query.filter(Follow.following == user.roll).all())
        follows[user.roll] = temp
        temp = len(Follow.query.filter(Follow.follower == user.roll).all())
        followers[user.roll] = temp
        temp = len(Post.query.filter_by(author = user.username).all())
        articles[user.roll] = temp
    return render_template("follow.html", username=username, users = users, followers=followers, follows=follows, articles=articles, title="Follows")

@app.route('/user=<username>/account/token', methods=["GET", "POST"])
def token(username):
    user = User.query.filter_by(username=username).first()
    if "user" in session and session["user"] == user.username:
        if request.method  == "GET":
            return render_template("token.html", user=username)
        if request.method == "POST":
            pwd = request.form["password"]
            if not passhash.verify(pwd, user.password):
                return render_template("token.html", user=username, pwd_error=True)
            with open("api.txt", "w") as f:
                f.write(Token.query.filter_by(user=user.roll).first().token)
            try:
                return send_from_directory(".", "api.txt", as_attachment=True)
            finally:
                os.remove("api.txt")
    else:
        return redirect(url_for('home'))


@app.route("/user=<username>/account/analytics", methods=["GET", "POST"])
def analytics(username):
    user = User.query.filter_by(username=username).first()
    if "user" in session and session["user"] == user.username:
        posts = Post.query.filter_by(author=username).order_by(Post.roll).all()
        if request.method == "GET":
            titles = [post.title for post in posts]
            views = [post.views for post in posts]
            
            fig, ax = plt.subplots(figsize=(18,10))

            ax.barh(titles, views)
            ax.set_title(username + "'s Analytics", fontsize=20)
            ax.set_ylabel("Titles", fontsize=14)
            ax.set_xlabel("Views", fontsize=14)

            for i, v in enumerate(views):
                ax.text(v, i, str(v), color='black', fontsize=11, ha='left', rotation=270)


            plt.grid(linestyle="--")

            plt.savefig(app.config["UPLOAD_FOLDER"] + "/Analytics/" + username + ".png")

            return render_template("analytics.html", user=username)
        elif request.method == "POST":
            with open("analytics.csv", "w", newline='') as f:
                f = csv.writer(f, delimiter=',')
                f.writerow(["Roll", "Author", "Title", "Text", "Date", "Image ID", "Views", "Comments"])
                for post in posts:
                    comments = len(Comment.query.filter_by(post=post.roll).all())
                    f.writerow([post.roll, post.author, post.title, post.text, post.date, post.img, post.views, comments])

            try:
                return send_from_directory(".", "analytics.csv", as_attachment=True)
            finally:
                os.remove("analytics.csv")
    else:
        return redirect(url_for('home'))