# app/forms.py

from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField, TextAreaField
from wtforms.validators import (
    DataRequired, Length, EqualTo, ValidationError,
    Regexp, Optional   # ✅ 추가: Regexp, Optional
)
from app.models import User
from wtforms.fields import DateField
from wtforms.validators import DataRequired, Length, EqualTo, ValidationError, Regexp, Optional


class RegistrationForm(FlaskForm):
    # 아이디: 영문/숫자/언더스코어 4~20자
    username = StringField(
        '교번',
        validators=[
            DataRequired(),
            Length(min=5, max=5),
            Regexp(r'^[0-9]{5}$', message='교번은 5자리 숫자만 입력 가능합니다.')
        ]
    )

    # 사용자 이름(표시명)
    display_name = StringField(
        '사용자 이름',
        validators=[DataRequired(), Length(min=1, max=30)]
    )

    password = PasswordField(
        '비밀번호',
        validators=[DataRequired(), Length(min=6, max=128)]
    )

    confirm_password = PasswordField(
        '비밀번호 확인',
        validators=[DataRequired(), EqualTo('password', message='비밀번호가 일치하지 않습니다.')]
    )

    # 초대/인증 코드는 선택 입력(있으면 5자리)
    invite_code = StringField(
        '인증 코드',
        validators=[Optional(), Length(min=5, max=5, message='인증 코드는 5자리여야 합니다.')]
    )

    submit = SubmitField('가입하기')

    # (선택) 아이디 중복 체크
    def validate_username(self, field):
        if User.query.filter_by(username=field.data).first():
            raise ValidationError('이미 사용 중인 아이디입니다.')


class LoginForm(FlaskForm):
    # 로그인도 아이디 기준이면 라벨을 맞춰 주세요
    username = StringField('아이디', validators=[DataRequired()])
    password = PasswordField('비밀번호', validators=[DataRequired()])
    submit = SubmitField('로그인')


class PostForm(FlaskForm):
    title = StringField('제목', validators=[DataRequired()])
    content = TextAreaField('내용', validators=[DataRequired()])
    submit = SubmitField('등록')


class CommentForm(FlaskForm):
    content = TextAreaField('댓글 내용', validators=[DataRequired()], render_kw={"placeholder": "댓글을 입력하세요..."})
    submit = SubmitField('댓글 등록')
    

class ProfileForm(FlaskForm):
    company   = StringField('중대', validators=[Optional(), Length(max=20)])
    grade     = StringField('학년', validators=[Optional(), Length(max=10)])
    real_name = StringField('이름', validators=[Optional(), Length(max=50)])
    birthdate = DateField('생년월일', format='%Y-%m-%d', validators=[Optional()])
    specialty = StringField('특징(자격증)', validators=[Optional(), Length(max=200)])
    submit    = SubmitField('저장')
    submit    = SubmitField('저장')