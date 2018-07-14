# coding=utf-8
from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, BooleanField, SubmitField
from wtforms.validators import InputRequired, Optional, Length, Regexp, EqualTo
from wtforms import ValidationError
from ..models import users


class LoginForm(FlaskForm):
    username = StringField('用户名', validators=[InputRequired])
    password = PasswordField('密码', validators=[InputRequired])
    remember = BooleanField('记住我')
    submit = SubmitField('登录')


class RegistryForm(FlaskForm):
    username = StringField('用户名', validators=[InputRequired])
    password = PasswordField('密码', validators=[
        InputRequired, EqualTo('password2', message='两次输入需一致!'),])
    password2 = PasswordField('确认密码', validators=[InputRequired])
    submit = SubmitField('注册')

    def validate_username(self, field):
        if users.query.filter_by(username=field.data).first():
            raise ValidationError('用户名已存在!')