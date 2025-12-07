from flask import render_template, url_for, flash, redirect, request, abort
from app import app, db, bcrypt, google
from app.forms import RegistrationForm, LoginForm, PostForm, ProfileForm, ChatForm, ScheduleForm
from app.models import User, Post, Message, Schedule
from flask_login import login_user, current_user, logout_user, login_required
from werkzeug.utils import secure_filename
from datetime import datetime, date
from sqlalchemy import and_
import os

UPLOAD_FOLDER = os.path.join(os.getcwd(), 'app', 'static', 'profile_pics')


# =====================================================
# Landing Page (로그인 전)
# =====================================================
@app.route("/")
def index():
    return render_template("landing.html")


# =====================================================
# Home (로그인 후 메인 게시판)
# =====================================================
@app.route("/home")
@login_required
def home():
    query = request.args.get("q", "").strip()

    base_query = Post.query.order_by(Post.date_posted.desc())

    if query:
        terms = query.split()
        filters = [Post.title.ilike(f"%{term}%") for term in terms]
        base_query = base_query.filter(and_(*filters))

    posts = base_query.all()

    # 사용자 일정 불러오기
    schedules = Schedule.query.filter_by(user_id=current_user.id).all()

    schedules_json = [
        {
            "id": s.id,
            "date": s.date.strftime("%Y-%m-%d"),
            "title": s.title,
            "color": s.color
        }
        for s in schedules
    ]

    return render_template("index.html", posts=posts, query=query, schedules=schedules_json)



# =====================================================
# 회원가입
# =====================================================
@app.route("/register", methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('home'))

    form = RegistrationForm()

    if form.validate_on_submit():
        if form.invite_code.data != '54321':
            flash("인증 코드가 올바르지 않습니다.", "danger")
            return render_template("register.html", form=form)

        hashed_password = bcrypt.generate_password_hash(form.password.data).decode("utf-8")
        user = User(username=form.username.data, password=hashed_password)

        db.session.add(user)
        db.session.commit()

        flash("회원가입이 완료되었습니다!", "success")
        return redirect(url_for('login'))

    return render_template("register.html", form=form)



# =====================================================
# 로그인 / 로그아웃
# =====================================================
@app.route("/login", methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('home'))

    form = LoginForm()

    if form.validate_on_submit():
        user = User.query.filter_by(username=form.username.data).first()

        if user and bcrypt.check_password_hash(user.password, form.password.data):
            login_user(user)
            flash(f"{user.username}님 환영합니다!", "info")
            return redirect(url_for("home"))

        flash("로그인 실패. 아이디/비밀번호 확인!", "danger")

    return render_template("login.html", form=form)


@app.route("/logout")
def logout():
    logout_user()
    return redirect(url_for("index"))



# =====================================================
# 게시글 CRUD
# =====================================================
@app.route("/post/new", methods=['GET', 'POST'])
@login_required
def new_post():
    form = PostForm()

    if form.validate_on_submit():
        post = Post(title=form.title.data, content=form.content.data, author=current_user)
        db.session.add(post)
        db.session.commit()
        flash("게시글이 등록되었습니다.", "success")
        return redirect(url_for('home'))

    return render_template("create_post.html", form=form)


@app.route("/post/<int:post_id>")
def post(post_id):
    post = Post.query.get_or_404(post_id)
    return render_template("post.html", post=post)


@app.route("/post/<int:post_id>/delete", methods=['POST'])
@login_required
def delete_post(post_id):
    post = Post.query.get_or_404(post_id)

    if post.author != current_user:
        abort(403)

    db.session.delete(post)
    db.session.commit()
    flash("게시글 삭제 완료!", "success")
    return redirect(url_for('home'))



# =====================================================
# 채팅
# =====================================================
@app.route("/chat/<int:post_id>", methods=['GET', 'POST'])
@login_required
def chat(post_id):
    post = Post.query.get_or_404(post_id)

    if not post.applicant_id:
        flash("아직 신청이 완료되지 않은 게시글입니다.", "warning")
        return redirect(url_for('post', post_id=post.id))

    if current_user.id not in [post.user_id, post.applicant_id]:
        flash("채팅 권한이 없습니다!", "danger")
        return redirect(url_for('home'))

    other_user = User.query.get(post.applicant_id if current_user.id == post.user_id else post.user_id)
    form = ChatForm()

    if form.validate_on_submit():
        msg = Message(
            post_id=post.id,
            sender_id=current_user.id,
            receiver_id=other_user.id,
            content=form.content.data
        )
        db.session.add(msg)
        db.session.commit()
        return redirect(url_for('chat', post_id=post.id))

    messages = Message.query.filter_by(post_id=post.id).order_by(Message.timestamp.asc()).all()

    return render_template("chat.html", post=post, messages=messages, other_user=other_user, form=form)



# =====================================================
# 프로필
# =====================================================
@app.route("/profile", methods=['GET', 'POST'], endpoint="profile")
@login_required
def profile():
    if request.method == "POST":
        file = request.files.get("image")
        if file:
            filename = secure_filename(file.filename)
            file.save(os.path.join(UPLOAD_FOLDER, filename))
            current_user.image_file = filename

        current_user.real_name = request.form.get("real_name")
        current_user.company = request.form.get("company")
        current_user.grade = request.form.get("grade")
        current_user.specialty = request.form.get("specialty")

        birth_str = request.form.get("birthdate")
        if birth_str:
            try:
                current_user.birthdate = datetime.strptime(birth_str, "%Y-%m-%d").date()
            except:
                flash("생년월일 형식 오류!", "warning")

        db.session.commit()
        flash("프로필이 수정되었습니다!", "success")
        return redirect(url_for("profile"))

    return render_template("profile.html", user=current_user)



# =====================================================
# 게시글 신청
# =====================================================
@app.route("/post/<int:post_id>/apply", methods=['POST'])
@login_required
def apply_post(post_id):
    post = Post.query.get_or_404(post_id)

    if post.author == current_user:
        flash("자기 글에는 신청 불가!", "danger")
        return redirect(url_for('post', post_id=post.id))

    if post.applicant_id:
        flash("이미 마감된 글입니다.", "warning")
        return redirect(url_for('post', post_id=post.id))

    post.applicant_id = current_user.id
    db.session.commit()

    flash("신청이 완료되었습니다!", "success")
    return redirect(url_for('post', post_id=post.id))



# =====================================================
# 구글 로그인
# =====================================================
@app.route("/login/google")
def google_login():
    redirect_uri = url_for("google_callback", _external=True)
    return google.authorize_redirect(redirect_uri)


@app.route("/login/google/callback")
def google_callback():
    token = google.authorize_access_token()
    user_info = google.parse_id_token(token)

    email = user_info.get("email")
    name = user_info.get("name")

    user = User.query.filter_by(username=email).first()

    if not user:
        user = User(username=email, real_name=name, password="google_oauth_no_password")
        db.session.add(user)
        db.session.commit()

    login_user(user)
    flash(f"{name}님 구글 로그인 성공!", "success")
    return redirect(url_for("home"))



# =====================================================
# 일정 날짜별 보기
# =====================================================
@app.route("/schedule/date/<string:date_str>")
@login_required
def schedule_by_date(date_str):
    try:
        date_obj = datetime.strptime(date_str, "%Y-%m-%d").date()
    except:
        flash("잘못된 날짜 형식!", "danger")
        return redirect(url_for("home"))

    schedules = Schedule.query.filter_by(
        user_id=current_user.id,
        date=date_obj
    ).all()

    return render_template("schedule_by_date.html", schedules=schedules, date=date_str)




@app.route("/api/schedule/add", methods=["POST"])
@login_required
def api_schedule_add():
    data = request.get_json()
    date_str = data.get("date")
    title = data.get("title")

    date_obj = datetime.strptime(date_str, "%Y-%m-%d").date()

    new_s = Schedule(
        user_id=current_user.id,
        date=date_obj,
        title=title
    )
    db.session.add(new_s)
    db.session.commit()

    return {"status": "ok"}


@app.route("/profile/<int:user_id>")
def view_profile(user_id):
    user = User.query.get_or_404(user_id)
    return render_template("view_profile.html", user=user)
