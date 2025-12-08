from datetime import datetime, date
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
    
class Schedule(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)

    date = db.Column(db.Date, nullable=False)
    title = db.Column(db.String(100), nullable=False)

    memo = db.Column(db.Text, nullable=True)   # 🆕 메모
    color = db.Column(db.String(20), nullable=True, default="#3B82F6")  # 🆕 색깔 (기본 파랑)

    timestamp = db.Column(db.DateTime, default=datetime.utcnow)

class Message(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    post_id = db.Column(db.Integer, db.ForeignKey('post.id'), nullable=False)

    sender_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    receiver_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)

    content = db.Column(db.Text, nullable=False)
    timestamp = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)

    # 관계 (선택적으로 달아주면 편함)
    sender = db.relationship('User', foreign_keys=[sender_id])
    receiver = db.relationship('User', foreign_keys=[receiver_id])
    post = db.relationship('Post', backref=db.backref('messages', lazy='dynamic'))

class Notification(db.Model):
    id = db.Column(db.Integer, primary_key=True)

    # 알림을 받을 사용자
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)

    # 알림 내용
    message = db.Column(db.String(200), nullable=False)

    # 클릭 시 이동할 링크 (옵션)
    link = db.Column(db.String(200))

    # 읽었는지 여부
    is_read = db.Column(db.Boolean, default=False)

    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    user = db.relationship(
        'User',
        backref=db.backref('notifications', lazy='dynamic')
    )

    def __repr__(self):
        return f"<Notification {self.user_id} {self.message}>"