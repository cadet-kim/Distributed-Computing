from flask import render_template, url_for, flash, redirect, request, abort
from app import app, db, bcrypt
from app.forms import RegistrationForm, LoginForm, PostForm, ProfileForm  # ← ProfileForm 추가
from app.models import User, Post
from flask_login import login_user, current_user, logout_user, login_required

@app.route("/")
@app.route("/home")
def home():
    posts = Post.query.order_by(Post.date_posted.desc()).all()
    return render_template('index.html', posts=posts)

@app.route("/register", methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('home'))
    form = RegistrationForm()
    if form.validate_on_submit():
        if form.invite_code.data != '54321':
            flash('인증 코드가 올바르지 않습니다.', 'danger')
            return render_template('register.html', title='회원가입', form=form)
        hashed_password = bcrypt.generate_password_hash(form.password.data).decode('utf-8')
        user = User(username=form.username.data, password=hashed_password)
        db.session.add(user)
        db.session.commit()
        flash('회원가입이 완료되었습니다! 이제 로그인할 수 있습니다.', 'success')
        return redirect(url_for('login'))
    return render_template('register.html', title='회원가입', form=form)

@app.route("/login", methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('home'))
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(username=form.username.data).first()
        if user and bcrypt.check_password_hash(user.password, form.password.data):
            login_user(user)
            flash(f'{user.username}님, 환영합니다!', 'info')
            next_page = request.args.get('next')
            return redirect(next_page) if next_page else redirect(url_for('home'))
        else:
            flash('로그인에 실패했습니다. 사용자 이름과 비밀번호를 확인하세요.', 'danger')
    return render_template('login.html', title='로그인', form=form)

@app.route("/logout")
def logout():
    logout_user()
    return redirect(url_for('home'))

@app.route("/post/new", methods=['GET', 'POST'])
@login_required
def new_post():
    form = PostForm()
    if form.validate_on_submit():
        post = Post(title=form.title.data, content=form.content.data, author=current_user)
        db.session.add(post)
        db.session.commit()
        flash('게시글이 등록되었습니다.', 'success')
        return redirect(url_for('home'))
    return render_template('create_post.html', title='새 글 작성', form=form, legend='새 글 작성')

@app.route("/post/<int:post_id>", methods=['GET', 'POST'])
def post(post_id):
    # 1. 해당 ID의 게시글이 없으면 404 에러
    post = Post.query.get_or_404(post_id)

    # 2. 게시글 상세 페이지 렌더링
    #    - 템플릿에서는 post.title, post.content, post.author, post.applicant 등을 사용할 수 있음
    #    - 댓글 기능은 제거했으므로 comments, form 같은 값은 넘기지 않는다.
    return render_template(
        'post.html',
        title=post.title,
        post=post
    )

@app.route("/post/<int:post_id>/delete", methods=['POST'])
@login_required
def delete_post(post_id):
    post = Post.query.get_or_404(post_id)
    if post.author != current_user:
        abort(403)
    db.session.delete(post)
    db.session.commit()
    flash('게시글이 삭제되었습니다.', 'success')
    return redirect(url_for('home'))

# ====== 여기부터 신규: 프로필 보기/수정 ======
@app.route("/profile", methods=['GET', 'POST'])
@login_required
def profile():
    form = ProfileForm()
    if form.validate_on_submit():
        current_user.company = form.company.data
        current_user.grade = form.grade.data
        current_user.real_name = form.real_name.data
        current_user.birthdate = form.birthdate.data
        current_user.specialty = form.specialty.data
        db.session.commit()
        flash("프로필이 저장되었습니다.", "success")
        return redirect(url_for("profile"))

    # GET일 때 현재 값 채우기
    if request.method == "GET":
        form.company.data = current_user.company
        form.grade.data = current_user.grade
        form.real_name.data = current_user.real_name
        form.birthdate.data = current_user.birthdate
        form.specialty.data = current_user.specialty

    return render_template("profile.html", title="내 프로필", form=form)
# ============================================
@app.route("/post/<int:post_id>/apply", methods=['POST'])
@login_required
def apply_post(post_id):
    post = Post.query.get_or_404(post_id)
    
    # 1. 자기 자신의 글에는 신청 불가
    if post.author == current_user:
        flash('자신의 게시글에 신청할 수 없습니다.', 'danger')
        return redirect(url_for('post', post_id=post.id))
        
    # 2. 이미 다른 사람이 신청(마감)했는지 확인
    if post.applicant_id:
        flash('이미 신청이 마감된 게시글입니다.', 'warning')
        return redirect(url_for('post', post_id=post.id))

    # 3. 신청 처리 (게시글의 applicant_id를 현재 로그인한 사용자로 설정)
    post.applicant_id = current_user.id
    db.session.commit()
    flash('신청이 완료되었습니다.', 'success')
    return redirect(url_for('post', post_id=post.id))