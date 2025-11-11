from datetime import datetime
from app import db, login_manager
from flask_login import UserMixin


@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))


class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(20), unique=True, nullable=False)   # 교번(5자리 제한은 폼에서)
    password = db.Column(db.String(128), nullable=False)               # ✔ 라우트가 저장하므로 반드시 필요
    # ⬇️ 라우트가 real_name을 안 넣으니 NULL 허용 + 기본값
    real_name = db.Column(db.String(30), nullable=True, default='')    # ✔ 에러 원인 해결 포인트
    company = db.Column(db.String(10), nullable=True)
    grade = db.Column(db.String(10), nullable=True)
    specialty = db.Column(db.String(30), nullable=True)
    birthdate = db.Column(db.Date, nullable=True)
    profile_image = db.Column(db.String(100), nullable=True, default='default.jpg')

    posts = db.relationship('Post', backref='author', lazy=True, foreign_keys='Post.user_id')
    applications = db.relationship('Post', backref='applicant', lazy=True, foreign_keys='Post.applicant_id')


  

    def get_mentor_activity_count(self):
        """멘토 활동 횟수: 내가 쓴 글 중 신청이 완료된 글"""
        return Post.query.filter_by(user_id=self.id).filter(Post.applicant_id != None).count()

    def get_mentee_activity_count(self):
        """멘티 활동 횟수: 내가 신청자로 등록된 글"""
        return Post.query.filter_by(applicant_id=self.id).count()

    def __repr__(self):
        return f"User('{self.username}')"


class Post(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(100), nullable=False)
    date_posted = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    content = db.Column(db.Text, nullable=False)

    # ✅ 작성자(멘토)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    # ✅ 신청자(멘티)
    applicant_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=True)

    comments = db.relationship(
        'Comment',
        backref='post',
        lazy=True,
        cascade="all, delete-orphan"
    )

    def __repr__(self):
        return f"Post('{self.title}', '{self.date_posted}')"


class Comment(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    date_posted = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    content = db.Column(db.Text, nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    post_id = db.Column(db.Integer, db.ForeignKey('post.id'), nullable=False)

    def __repr__(self):
        return f"Comment('{self.content}', '{self.date_posted}')"
