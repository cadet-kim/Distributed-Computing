from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField, TextAreaField
from wtforms.validators import DataRequired, Length, EqualTo, ValidationError
from app.models import User

class RegistrationForm(FlaskForm):
    username = StringField('사용자 이름', validators=[DataRequired(), Length(min=2, max=20)])
    password = PasswordField('비밀번호', validators=[DataRequired(), Length(min=4)])
    confirm_password = PasswordField('비밀번호 확인', validators=[DataRequired(), EqualTo('password', message='비밀번호가 일치하지 않습니다.')])
    invite_code = StringField('인증 코드', validators=[DataRequired(), Length(min=5, max=5, message='5자리 코드를 입력해야 합니다.')])
    submit = SubmitField('가입하기')

    def validate_username(self, username):
        user = User.query.filter_by(username=username.data).first()
        if user:
            raise ValidationError('이미 존재하는 사용자 이름입니다. 다른 이름을 사용해주세요.')

class LoginForm(FlaskForm):
    username = StringField('사용자 이름', validators=[DataRequired()])
    password = PasswordField('비밀번호', validators=[DataRequired()])
    submit = SubmitField('로그인')

class PostForm(FlaskForm):
    title = StringField('제목', validators=[DataRequired()])
    content = TextAreaField('내용', validators=[DataRequired()])
    submit = SubmitField('등록')

class CommentForm(FlaskForm):
    content = TextAreaField('댓글 내용', validators=[DataRequired()], render_kw={"placeholder": "댓글을 입력하세요..."})
    submit = SubmitField('댓글 등록')
