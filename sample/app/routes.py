from flask import render_template, url_for, flash, redirect, request, abort, jsonify
from app import app, db, bcrypt, google
from app.forms import RegistrationForm, LoginForm, PostForm, ProfileForm, ChatForm, ScheduleForm
from app.models import User, Post, Message, Schedule, Notification
from flask_login import login_user, current_user, logout_user, login_required
from werkzeug.utils import secure_filename
from datetime import datetime
from sqlalchemy import and_, or_
import os

UPLOAD_FOLDER = os.path.join(os.getcwd(), 'app', 'static', 'profile_pics')


# =====================================================
# Landing Page
# =====================================================
@app.route("/")
def index():
    return render_template("landing.html")


# =====================================================
# Home (게시판 + 달력)
# =====================================================
@app.route("/home")
@login_required
def home():
    # 검색어
    query = request.args.get("q", "").strip()

    # 현재 페이지 (기본값 1)
    page = request.args.get("page", 1, type=int)

    schedules = []

    # 기본 쿼리
    base_query = Post.query.order_by(Post.date_posted.desc())

    # 검색어가 있다면 제목에서 단어들 AND 검색
    if query:
        terms = query.split()
        filters = [Post.title.ilike(f"%{term}%") for term in terms]
        base_query = base_query.filter(and_(*filters))

    # 🔹 페이지네이션: 한 페이지에 6개
    pagination = base_query.paginate(page=page, per_page=6, error_out=False)
    posts = pagination.items

    # 🔹 페이지 번호 블록 계산 (5개씩: 1~5, 6~10, ...)
    block_size = 5
    total_pages = pagination.pages or 1
    current_page = pagination.page

    current_block = (current_page - 1) // block_size
    block_start = current_block * block_size + 1
    block_end = min(block_start + block_size - 1, total_pages)

    page_numbers = list(range(block_start, block_end + 1))

    show_prev_block = block_start > 1
    show_next_block = block_end < total_pages
    prev_block_page = block_start - 1
    next_block_page = block_end + 1

    return render_template(
        "index.html",
        posts=posts,
        query=query,
        schedules=schedules,
        page=current_page,
        total_pages=total_pages,
        page_numbers=page_numbers,
        show_prev_block=show_prev_block,
        show_next_block=show_next_block,
        prev_block_page=prev_block_page,
        next_block_page=next_block_page,
    )



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

        hashed_pw = bcrypt.generate_password_hash(form.password.data).decode("utf-8")
        user = User(username=form.username.data, password=hashed_pw)
        db.session.add(user)
        db.session.commit()

        flash("회원가입 완료!", "success")
        return redirect(url_for('login'))

    return render_template("register.html", form=form)


# =====================================================
# 로그인/로그아웃
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
            # 🔵 프로필 완성 여부 체크
            if not is_profile_complete(user):
                flash("처음 로그인하셨네요. 프로필 정보를 먼저 입력해 주세요.", "info")
                return redirect(url_for('profile'))
            
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
@app.route("/post/new", methods=['GET', 'POST'])
@login_required
def new_post():
    form = PostForm()
    if form.validate_on_submit():
        post = Post(title=form.title.data, content=form.content.data, author=current_user)
        db.session.add(post)
        db.session.commit()
        flash("게시글 등록 완료!", "success")
        return redirect(url_for('home'))

    return render_template("create_post.html", form=form)


@app.route("/post/<int:post_id>")
def post(post_id):
    p = Post.query.get_or_404(post_id)
    return render_template("post.html", post=p)


@app.route("/post/<int:post_id>/delete", methods=['POST'])
@login_required
def delete_post(post_id):
    p = Post.query.get_or_404(post_id)

    if p.author != current_user:
        abort(403)

    db.session.delete(p)
    db.session.commit()
    flash("삭제 완료!", "success")
    return redirect(url_for('home'))


# =====================================================
# 게시글 신청 기능 (merge 중 사라졌던 부분 복구)
# =====================================================
@app.route("/post/<int:post_id>/apply", methods=['POST'])
@login_required
def apply_post(post_id):
    post = Post.query.get_or_404(post_id)

    if post.author == current_user:
        flash("자기 글에는 신청할 수 없습니다.", "danger")
        return redirect(url_for('post', post_id=post.id))

    if post.applicant_id:
        flash("이미 신청 완료된 글입니다.", "warning")
        return redirect(url_for('post', post_id=post.id))

    post.applicant_id = current_user.id

    notif = Notification(
        user_id=post.user_id,  # 글 쓴 사람
        message=f"'{post.title}' 글에 {current_user.username}님이 신청을 완료했습니다.",
        link=url_for('post', post_id=post.id)
    )

    db.session.commit()

    flash("신청 완료!", "success")
    return redirect(url_for("chat", post_id=post.id))


# =====================================================
# 채팅
# =====================================================
@app.route("/chat/<int:post_id>", methods=['GET', 'POST'])
@login_required
def chat(post_id):
    post = Post.query.get_or_404(post_id)

    # 1) 이 글이 신청 완료 상태인지 확인
    if not post.applicant_id:
        flash("아직 신청이 완료되지 않은 게시글입니다.", "warning")
        return redirect(url_for('post', post_id=post.id))

    # 2) 현재 사용자가 채팅 참여자인지 확인 (작성자 or 신청자)
    if current_user.id not in [post.user_id, post.applicant_id]:
        flash("이 채팅에 참여할 권한이 없습니다.", "danger")
        return redirect(url_for('home'))

    # ✅ 3) 여기서 other_user를 항상 먼저 계산 (GET/POST 공통)
    if current_user.id == post.user_id:
        other_user = User.query.get(post.applicant_id)
    else:
        other_user = User.query.get(post.user_id)

    form = ChatForm()

    if form.validate_on_submit():
        msg = Message(
            post_id=post.id,
            sender_id=current_user.id,
            receiver_id=other_user.id,   # ← 여기서 other_user 사용 가능
            content=form.content.data
        )
        db.session.add(msg)
        db.session.commit()

        # (알림 기능을 쓰고 있다면 여기서 Notification 생성하면 됨)
        # notif = Notification(
        #     user_id=other_user.id,
        #     message=f"'{post.title}' 채팅에 새 메시지가 있습니다.",
        #     url=url_for('chat', post_id=post.id)
        # )
        # db.session.add(notif)
        # db.session.commit()

        return redirect(url_for('chat', post_id=post.id))

    # 이 게시글에 대한 기존 메시지 (오래된 순으로)
    messages = Message.query.filter_by(post_id=post.id) \
                            .order_by(Message.timestamp.asc()) \
                            .all()

    return render_template(
        "chat.html",
        post=post,
        other_user=other_user,   # ← 템플릿에서 쓰는 변수
        messages=messages,
        form=form
    )


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

        birth = request.form.get("birthdate")
        if birth:
            try:
                current_user.birthdate = datetime.strptime(birth, "%Y-%m-%d").date()
            except:
                flash("날짜 형식 오류!", "warning")

        db.session.commit()
        flash("프로필 수정 완료!", "success")
        return redirect(url_for("profile"))

    return render_template("profile.html", user=current_user)


# =====================================================
# 🔥 빠져있던 view_profile 복구 (BuildError 원인 해결)
# =====================================================
@app.route("/profile/<int:user_id>")
@login_required
def view_profile(user_id):
    user = User.query.get_or_404(user_id)
    return render_template("view_profile.html", user=user)


# =====================================================
# 일정 추가
# =====================================================
@app.route("/schedule/new", methods=["GET", "POST"])
@login_required
def new_schedule():
    form = ScheduleForm()
    selected_date = request.args.get("date")

    # POST 요청 처리
    if request.method == "POST":
        color = request.form.get("color")

        # color가 선택되지 않았다면 에러 처리
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

            flash("일정 추가 완료!", "success")
            return redirect(url_for(
                "schedule_day",
                date_str=form.date.data.strftime("%Y-%m-%d")
            ))
        else:
            # 디버깅용 (폼 검증 실패 시 원인 확인)
            print("폼 에러:", form.errors)
            flash("입력값이 올바르지 않습니다.", "danger")

    # GET 요청일 때 날짜 세팅
    if selected_date:
        form.date.data = datetime.strptime(selected_date, "%Y-%m-%d").date()

    return render_template("new_schedule.html", form=form)




# =====================================================
# 일정 삭제
# =====================================================
@app.route("/schedule/delete/<int:schedule_id>", methods=["POST"])
@login_required
def delete_schedule(schedule_id):
    s = Schedule.query.get_or_404(schedule_id)

    if s.user_id != current_user.id:
        abort(403)

    date_str = s.date.strftime("%Y-%m-%d")

    db.session.delete(s)
    db.session.commit()

    flash("일정 삭제 완료!", "success")

    return redirect(url_for("schedule_day", date_str=date_str))


# =====================================================
# 일정 날짜별 보기
# =====================================================
@app.route("/schedule/<string:date_str>")
@login_required
def schedule_day(date_str):
    try:
        date_obj = datetime.strptime(date_str, "%Y-%m-%d").date()
    except:
        flash("잘못된 날짜 형식입니다.", "danger")
        return redirect(url_for("home"))

    day_schedules = Schedule.query.filter_by(
        user_id=current_user.id,
        date=date_obj
    ).all()

    all_schedules = Schedule.query.filter_by(user_id=current_user.id).all()

    schedules_json = [
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
        schedule_data=schedules_json
    )


# =====================================================
# Google Login
# =====================================================
@app.route("/google_login")
def google_login():
    redirect_uri = url_for("google_callback", _external=True)
    print("DEBUG redirect_uri:", redirect_uri, flush=True)
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
        user = User(username=email, password="google_oauth")  # 임시 패스워드
        db.session.add(user)
        db.session.commit()

    login_user(user)

    # 🔵 구글 로그인도 프로필 체크
    if not is_profile_complete(user):
        flash("프로필 정보를 먼저 입력해 주세요.", "info")
        return redirect(url_for("profile"))
    
    flash("Google 로그인 성공!", "success")
    return redirect(url_for("home"))

@app.route("/notifications/poll")
@login_required
def poll_notifications():
    # 아직 읽지 않은(not is_read) 알림만 가져오기
    notifs = Notification.query.filter_by(
        user_id=current_user.id,
        is_read=False
    ).order_by(Notification.created_at.asc()).all()

    data = []
    for n in notifs:
        data.append({
            "id": n.id,
            "message": n.message,
            "url": n.link
        })
        n.is_read = True  # 가져간 건 읽은 것으로 표시

    db.session.commit()
    return jsonify(data)

def is_profile_complete(user):
    # 이름(real_name), 중대(company), 학년(grade)가 모두 채워져 있어야 완성
    return bool(
        getattr(user, "real_name", None) and
        getattr(user, "company", None) and
        getattr(user, "grade", None)
    )

@app.before_request
def require_profile_complete():
    """
    로그인한 사용자가 프로필(이름, 중대, 학년)을 다 채우기 전까지는
    /profile, /logout, 정적파일(static) 말고는 이동 못하게 막는다.
    """
    # 로그인 안 되어 있으면 신경 안 씀
    if not current_user.is_authenticated:
        return

    # 프로필이 이미 완성되어 있으면 통과
    if is_profile_complete(current_user):
        return

    # 허용할 endpoint 목록 (여기는 이동 가능)
    allowed_endpoints = {
        "profile",          # 프로필 작성 페이지
        "logout",           # 로그아웃은 항상 허용
        "static",           # CSS, JS, 이미지 로딩
    }

    # request.endpoint가 없을 수도 있으니 방어 코드
    ep = request.endpoint

    # 프로필 미완성 + 허용되지 않은 곳으로 가려면 → profile로 강제 이동
    if ep not in allowed_endpoints:
        return redirect(url_for("profile"))
    
@app.route("/chats")
@login_required
def chats():
    # 현재 유저가 참여자인 채팅(신청 완료된 글)만 가져오기
    posts = Post.query.filter(
        Post.applicant_id.isnot(None),
        or_(
            Post.user_id == current_user.id,      # 내가 글쓴이이거나
            Post.applicant_id == current_user.id  # 내가 신청자이거나
        )
    ).order_by(Post.date_posted.desc()).all()

    chat_items = []
    for post in posts:
        # 상대방 결정
        if current_user.id == post.user_id:
            other = post.applicant
        else:
            other = post.author

        # 마지막 메시지
        last_msg = Message.query.filter_by(post_id=post.id)\
                                .order_by(Message.timestamp.desc())\
                                .first()

        chat_items.append({
            "post": post,
            "other": other,
            "last_msg": last_msg,
        })

    return render_template("chats.html", chats=chat_items)

@app.route("/chat/<int:post_id>/messages")
@login_required
def chat_messages(post_id):
    post = Post.query.get_or_404(post_id)

    # 참여자인지 확인 (안 그러면 남의 채팅도 볼 수 있게 됨)
    if not post.applicant_id or current_user.id not in [post.user_id, post.applicant_id]:
        abort(403)

    messages = Message.query.filter_by(post_id=post.id)\
                            .order_by(Message.timestamp.asc()).all()

    data = []
    for m in messages:
        data.append({
            "id": m.id,
            "sender_id": m.sender_id,
            "sender_name": m.sender.real_name or m.sender.username,
            "content": m.content,
            "timestamp": m.timestamp.strftime('%Y-%m-%d %H:%M'),
        })
    return jsonify(data)
