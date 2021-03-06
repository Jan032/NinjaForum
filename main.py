from flask import Flask
import hashlib
from flask import render_template, request, make_response, redirect, url_for
from models.user import User
from models.post import Post
from models.settings import db
import uuid

app = Flask(__name__)


@app.route('/', methods=["GET"])  # http://localhost(/) M <-- V <-- View (HTML)  C <- COntroller
def index():
    return render_template("index.html")


@app.route('/login', methods=["POST"])  # http://localhost(/) M <-- V <-- View (HTML)  C <- COntroller
def login():
    email = request.form.get("email")
    password = request.form.get("password")

    tryUser = db.query(User).filter_by(email=email).first()

    if not tryUser:
        return "This user does not exist - try registration on /register"
    else:
        tryPassword = hashlib.sha256(password.encode()).hexdigest()
        # print(tryUser)
        # exit()
        if tryPassword == tryUser.password:
            # tryUser.session_token = uuid.uuid4()
            # db.commit(tryUser) { session_token : "token" }
            # db.query(User).filter_by(email=email).update(dict(session_token=uuid.uuid4().__str__()))
            # db.commit()

            tryUser.session_token = uuid.uuid4().__str__()
            db.add(tryUser)
            db.commit()

            response = make_response(redirect(url_for("dashboard")))
            # print(response)
            # exit()
            response.set_cookie("session_token", tryUser.session_token, httponly=True, samesite='Strict')

            return response
        else:
            return "Wrong username/password!"


@app.route('/register', methods=["GET", "POST"])  # http://localhost(/) M <-- V <-- View (HTML)  C <- Controller
def register():
    if request.method == "GET":
        url = request.url_rule
        return render_template("register.html", url=url)
    elif request.method == "POST":
        email = request.form.get("email")
        password = request.form.get("password")

        newUser = User(email=email, password=hashlib.sha256(password.encode()).hexdigest())
        db.add(newUser)
        db.commit()
        return "Su??es"


@app.route('/dashboard', methods=["GET"])  # http://localhost(/) M <-- V <-- View (HTML)  C <- Controller
def dashboard():
    if isLoggedIn():
        return render_template("dashboard.html", user=getCurrentUser(), posts=db.query(Post).all())
    else:
        return redirectToLogin()


@app.route('/post_add_form', methods=["GET"])
def post_form():
    return render_template("post_add_form.html") if isLoggedIn() else redirectToLogin()


@app.route('/post/<post_id>', methods=["GET", "DELETE", "POST"])
def handlePost(post_id):
    post = db.query(Post).get(int(post_id))
    user = getCurrentUser()

    return render_template("post_details.html", post=post, user=user)

@app.route("/post/<post_id>/edit", methods=["GET", "POST"])
def post_edit(post_id):
    post = db.query(Post).get(int(post_id))

    if request.method == "GET":
        return render_template("postedit.html", post=post)

    elif request.method == "POST":
        title = request.form.get("title")
        description = request.form.get("description")

        user = getCurrentUser()

        # check if user is logged in and user is author
        if not user:
            return redirect(url_for('login'))
        elif post.author_id != user.id:
            return "You are not the author!"
        else:
            # update the topic fields
            post.title = title
            post.description = description
            db.add(post)
            db.commit()

            return redirect(url_for('handlePost', post_id=post_id))


@app.route("/post/<post_id>/delete", methods=["GET", "POST"])
def post_delete(post_id):
    post = db.query(Post).get(int(post_id))

    if request.method == "GET":
        return render_template("postdelete.html", post=post)

    elif request.method == "POST":
        user = getCurrentUser()

        if not user:
            return redirect(url_for('login'))
        elif post.author_id != user.id:
            return "You are not the author!"
        else:
            db.delete(post)
            db.commit()
            return redirect(url_for("dashboard", user=user))



@app.route('/post', methods=["POST"])
def createPost():
    title = request.form.get('title')
    description = request.form.get('description')
    author = getCurrentUser()

    Post.create(title=title, description=description, author=author)

    return redirectToRoute("dashboard")



def isLoggedIn():
    session_token = request.cookies.get("session_token")
    user = getCurrentUser() if session_token else None

    return user is not None


def redirectToLogin():
    return redirectToRoute("index")


def getCurrentUser():
    session_token = request.cookies.get("session_token")
    return db.query(User).filter_by(session_token=session_token).first()


def redirectToRoute(route):
    return make_response(redirect(url_for(route)))

if __name__ == '__main__':
    app.run(use_reloader=True)