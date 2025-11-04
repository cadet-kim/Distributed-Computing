from flask import render_template, url_for, flash, redirect, request, abort
from app import app, db, bcrypt
from app.forms import RegistrationForm, LoginForm, PostForm, CommentForm
from app.models import User, Post, Comment
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
    post = Post.query.get_or_404(post_id)
    form = CommentForm()
    if form.validate_on_submit():
        if not current_user.is_authenticated:
            flash('댓글을 작성하려면 로그인이 필요합니다.', 'warning')
            return redirect(url_for('login', next=request.url))
        comment = Comment(content=form.content.data, author=current_user, post=post)
        db.session.add(comment)
        db.session.commit()
        flash('댓글이 등록되었습니다.', 'success')
        return redirect(url_for('post', post_id=post.id))
    comments = Comment.query.filter_by(post_id=post.id).order_by(Comment.date_posted.asc()).all()
    return render_template('post.html', title=post.title, post=post, comments=comments, form=form)

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
