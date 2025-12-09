from flask import (
    render_template, url_for, flash, redirect,
    request, abort, jsonify
)
from app import app, db, bcrypt, google
from app.forms import (
    RegistrationForm, LoginForm, PostForm,
    ProfileForm, ChatForm, ScheduleForm
)
from app.models import User, Post, Message, Schedule, Notification
from flask_login import (
    login_user, current_user,
    logout_user, login_required
)
from werkzeug.utils import secure_filename
from datetime import datetime
from sqlalchemy import and_
import os


# =====================================================
# 파일 저장 경로
# =====================================================
UPLOAD_FOLDER = os.path.join(os.getcwd(), "app", "static", "profile_pics")


# =====================================================
# Landing Page
# =====================================================
@app.route("/")
def index():
    return render_template("landing.html")


# =====================================================
# 홈 + 게시판 + 캘린더
# =====================================================
@app.route("/home")
@login_required
def home():
    query = request.args.get("q", "").strip()
    base_query = Post.query.order_by(Post.date_posted.desc())

    if query:
        terms = query.split()
        filters = [Post.title.ilike(f"%{t}%") for t in terms]
        base_query = base_query.filter(and_(*filters))

    posts = base_query.all()

    schedules = Schedule.query.filter_by(user_id=current_user.id).all()
    schedules_json = [
        {
            "id": s.id,
            "date": s.date.strftime("%Y-%m-%d"),
            "title": s.title,
            "memo": s.memo,
            "color": s.color
        }
        for s in schedules
    ]

    return render_template(
        "index.html",
        posts=posts,
        query=query,
        schedules=schedules_json
    )


# =====================================================
# 회원가입
# =====================================================
@app.route("/register", methods=["GET", "POST"])
def register():
    if current_user.is_authenticated:
        return redirect(url_for("home"))

    form = RegistrationForm()

    if form.validate_on_submit():
        if form.invite_code.data != "54321":
            flash("인증 코드가 올바르지 않습니다.", "danger")
            return render_template("register.html", form=form)

        hashed_pw = bcrypt.generate_password_hash(form.password.data).decode("utf-8")
        new_user = User(username=form.username.data, password=hashed_pw)

        db.session.add(new_user)
        db.session.commit()

        flash("회원가입 완료!", "success")
        return redirect(url_for("login"))

    return render_template("register.html", form=form)


# =====================================================
# 로그인 / 로그아웃
# =====================================================
@app.route("/login", methods=["GET", "POST"])
def login():
    if current_user.is_authenticated:
        return redirect(url_for("home"))

    form = LoginForm()

    if form.validate_on_submit():
        user = User.query.filter_by(username=form.username.data).first()

        if user and bcrypt.check_password_hash(user.password, form.password.data):
            login_user(user)

            if not is_profile_complete(user):
                flash("처음 로그인하셨네요. 프로필을 먼저 작성해주세요!", "info")
                return redirect(url_for("profile"))

            flash("로그인 성공!", "success")
            return redirect(url_for("home"))

        flash("로그인 실패!", "danger")

    return render_template("login.html", form=form)


@app.route("/logout")
def logout():
    logout_user()
    return redirect(url_for("index"))


# =====================================================
# 게시글 CRUD
# =====================================================
@app.route("/post/new", methods=["GET", "POST"])
@login_required
def new_post():
    form = PostForm()

    if form.validate_on_submit():
        post = Post(
            title=form.title.data,
            content=form.content.data,
            author=current_user
        )
        db.session.add(post)
        db.session.commit()

        flash("게시글 등록 완료!", "success")
        return redirect(url_for("home"))

    return render_template("create_post.html", form=form)


@app.route("/post/<int:post_id>")
def post(post_id):
    p = Post.query.get_or_404(post_id)
    return render_template("post.html", post=p)


@app.route("/post/<int:post_id>/delete", methods=["POST"])
@login_required
def delete_post(post_id):
    p = Post.query.get_or_404(post_id)

    if p.author != current_user:
        abort(403)

    db.session.delete(p)
    db.session.commit()

    flash("게시글 삭제 완료!", "success")
    return redirect(url_for("home"))


# =====================================================
# 게시글 신청
# =====================================================
@app.route("/post/<int:post_id>/apply", methods=["POST"])
@login_required
def apply_post(post_id):
    p = Post.query.get_or_404(post_id)

    if p.author == current_user:
        flash("자기 글에는 신청할 수 없습니다.", "danger")
        return redirect(url_for("post", post_id=p.id))

    if p.applicant_id:
        flash("이미 신청된 글입니다.", "warning")
        return redirect(url_for("post", post_id=p.id))

    p.applicant_id = current_user.id

    notif = Notification(
        user_id=p.user_id,
        message=f"'{p.title}' 글에 {current_user.username}님이 신청했습니다.",
        link=url_for("post", post_id=p.id)
    )
    db.session.add(notif)
    db.session.commit()

    flash("신청 완료!", "success")
    return redirect(url_for("chat", post_id=p.id))


# =====================================================
# 채팅
# =====================================================
@app.route("/chat/<int:post_id>", methods=["GET", "POST"])
@login_required
def chat(post_id):
    p = Post.query.get_or_404(post_id)

    if not p.applicant_id:
        flash("아직 신청자가 없습니다.", "warning")
        return redirect(url_for("post", post_id=post_id))

    if current_user.id not in [p.user_id, p.applicant_id]:
        flash("채팅 권한이 없습니다.", "danger")
        return redirect(url_for("home"))

    other = User.query.get(p.applicant_id if current_user.id == p.user_id else p.user_id)
    form = ChatForm()

    if form.validate_on_submit():
        msg = Message(
            post_id=post_id,
            sender_id=current_user.id,
            receiver_id=other.id,
            content=form.content.data
        )
        db.session.add(msg)

        notif = Notification(
            user_id=other.id,
            message=f"{current_user.username}님이 새 메시지를 보냈습니다.",
            link=url_for("chat", post_id=p.id)
        )
        db.session.add(notif)

        db.session.commit()
        return redirect(url_for("chat", post_id=post_id))

    msgs = Message.query.filter_by(post_id=post_id).order_by(Message.timestamp.asc()).all()
    return render_template("chat.html", post=p, messages=msgs, other_user=other, form=form)


# =====================================================
# 프로필 / 프로필 보기
# =====================================================
@app.route("/profile", methods=["GET", "POST"], endpoint="profile")
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

        birth = request.form.get("birthdate")
        if birth:
            try:
                current_user.birthdate = datetime.strptime(birth, "%Y-%m-%d").date()
            except:
                flash("생년월일 형식 오류!", "warning")

        db.session.commit()
        flash("프로필 수정 완료!", "success")
        return redirect(url_for("profile"))

    return render_template("profile.html", user=current_user)


@app.route("/profile/<int:user_id>")
@login_required
def view_profile(user_id):
    user = User.query.get_or_404(user_id)
    return render_template("view_profile.html", user=user)


# =====================================================
# 프로필 완성 여부 체크
# =====================================================
def is_profile_complete(user):
    return bool(
        getattr(user, "real_name", None)
        and getattr(user, "company", None)
        and getattr(user, "grade", None)
    )


@app.before_request
def require_profile_complete():
    if not current_user.is_authenticated:
        return

    if is_profile_complete(current_user):
        return

    allowed = {"profile", "logout", "static"}

    ep = request.endpoint

    if ep not in allowed:
        return redirect(url_for("profile"))


# =====================================================
# 일정 — 전체 기능 구현
# =====================================================

# 일정 새로 추가
@app.route("/schedule/new", methods=["GET", "POST"])
@login_required
def new_schedule():
    form = ScheduleForm()
    selected_date = request.args.get("date")

    if request.method == "POST":
        color = request.form.get("color")

        if not color:
            flash("색상을 선택해주세요!", "danger")
            return render_template("new_schedule.html", form=form)

        if form.validate_on_submit():
            new_s = Schedule(
                user_id=current_user.id,
                date=form.date.data,
                title=form.title.data,
                memo=form.memo.data,
                color=color
            )
            db.session.add(new_s)
            db.session.commit()

            flash("일정이 추가되었습니다!", "success")
            return redirect(
                url_for("schedule_day", date_str=form.date.data.strftime("%Y-%m-%d"))
            )

    if selected_date:
        form.date.data = datetime.strptime(selected_date, "%Y-%m-%d").date()

    return render_template("new_schedule.html", form=form)


# 일정 상세 보기
@app.route("/schedule/detail/<int:schedule_id>")
@login_required
def schedule_detail(schedule_id):
    s = Schedule.query.get_or_404(schedule_id)

    if s.user_id != current_user.id:
        abort(403)

    return render_template("schedule_detail.html", schedule=s)


# 일정 수정
@app.route("/schedule/<int:schedule_id>/edit", methods=["GET", "POST"])
@login_required
def edit_schedule(schedule_id):
    s = Schedule.query.get_or_404(schedule_id)

    if s.user_id != current_user.id:
        abort(403)

    if request.method == "POST":
        s.title = request.form["title"]
        s.date = datetime.strptime(request.form["date"], "%Y-%m-%d").date()
        s.memo = request.form.get("memo", "")
        s.color = request.form.get("color", s.color)

        db.session.commit()
        flash("일정이 수정되었습니다!", "success")

        return redirect(url_for("schedule_detail", schedule_id=s.id))

    return render_template("edit_schedule.html", schedule=s)


# 일정 삭제
@app.route("/schedule/delete/<int:schedule_id>", methods=["POST"])
@login_required
def delete_schedule(schedule_id):
    s = Schedule.query.get_or_404(schedule_id)

    if s.user_id != current_user.id:
        abort(403)

    db.session.delete(s)
    db.session.commit()

    flash("일정이 삭제되었습니다!", "success")
    return redirect(url_for("total_schedules"))


# 날짜별 일정 보기
@app.route("/schedule/<string:date_str>")
@login_required
def schedule_day(date_str):
    try:
        date_obj = datetime.strptime(date_str, "%Y-%m-%d").date()
    except:
        flash("잘못된 날짜 형식입니다.", "danger")
        return redirect(url_for("home"))

    day_schedules = Schedule.query.filter_by(
        user_id=current_user.id, date=date_obj
    ).all()

    all_schedules = Schedule.query.filter_by(user_id=current_user.id).all()

    schedule_data = [
        {
            "id": s.id,
            "date": s.date.strftime("%Y-%m-%d"),
            "title": s.title,
            "memo": s.memo,
            "color": s.color
        }
        for s in all_schedules
    ]

    return render_template(
        "schedule_day.html",
        schedules=day_schedules,
        date=date_str,
        schedule_data=schedule_data
    )


# 전체 일정 보기
@app.route("/total_schedules")
@login_required
def total_schedules():
    all_schedules = Schedule.query.filter_by(
        user_id=current_user.id
    ).order_by(Schedule.date.asc()).all()

    return render_template("total_schedules.html", schedules=all_schedules)


# =====================================================
# Google Login
# =====================================================
@app.route("/google_login")
def google_login():
    redirect_uri = url_for("google_callback", _external=True)
    return google.authorize_redirect(redirect_uri)


@app.route("/google_callback")
def google_callback():
    token = google.authorize_access_token()

    if not token:
        flash("Google 로그인 실패!", "danger")
        return redirect(url_for("login"))

    user_info = google.get("userinfo").json()
    email = user_info.get("email")

    if not email:
        flash("Google 계정 정보를 가져올 수 없습니다.", "danger")
        return redirect(url_for("login"))

    user = User.query.filter_by(username=email).first()

    if not user:
        user = User(username=email, password="google_oauth")
        db.session.add(user)
        db.session.commit()

    login_user(user)

    if not is_profile_complete(user):
        flash("프로필을 먼저 작성해주세요!", "info")
        return redirect(url_for("profile"))

    flash("Google 로그인 성공!", "success")
    return redirect(url_for("home"))


# =====================================================
# 알림 폴링
# =====================================================
@app.route("/notifications/poll")
@login_required
def poll_notifications():
    notifs = Notification.query.filter_by(
        user_id=current_user.id, is_read=False
    ).order_by(Notification.created_at.asc()).all()

    data = []
    for n in notifs:
        data.append({
            "id": n.id,
            "message": n.message,
            "url": n.link
        })
        n.is_read = True

    db.session.commit()
    return jsonify(data)
