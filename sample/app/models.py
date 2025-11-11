from datetime import datetime
from app import db, login_manager
from flask_login import UserMixin

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(20), unique=True, nullable=False)
    password = db.Column(db.String(60), nullable=False)
    company = db.Column(db.String(20))        
    grade = db.Column(db.String(10))          
    real_name = db.Column(db.String(50))      
    birthdate = db.Column(db.Date)            
    specialty = db.Column(db.String(200))     
    posts = db.relationship('Post', foreign_keys='Post.user_id', backref='author', lazy='dynamic')
    posts_applied_to = db.relationship('Post', foreign_keys='Post.applicant_id', backref='applicant', lazy='dynamic')
    comments = db.relationship('Comment', backref='applicant', lazy='dynamic')

    @property
    def mentor_activity_count(self):
        """멘토 활동 횟수 계산"""
        # 멘토 활동: 내가 쓴 글 (self.posts) 중에서,
        # applicant_id가 채워진(None이 아닌) 글의 개수
        return self.posts.filter(Post.applicant_id != None).count()

    @property
    def mentee_activity_count(self):
        """멘티 활동 횟수 계산"""
        # 멘티 활동: 내가 신청한(posts_applied_to) 글의 총 개수
        return self.posts_applied_to.count()

    def __repr__(self):
        return f"User('{self.username}')"

class Post(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(100), nullable=False)
    date_posted = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    content = db.Column(db.Text, nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    comments = db.relationship('Comment', backref='post', lazy=True, cascade="all, delete-orphan")
    applicant_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=True)

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