# coding=utf-8
from flask import render_template, redirect, url_for, request, flash
from flask_login import login_user, logout_user, login_required, current_user
from . import auth  # 导入蓝本auth
from .. import db
from .forms import *
from ..models import *
from werkzeug.utils import secure_filename


@auth.route('/login', methods=['GET', 'POST'])
def login():
    form = LoginForm()
    if form.validate_on_submit():
        cur_user = users.query.filter_by(user_name=form.username.data).first()
        if cur_user is not None and cur_user.user_key == form.password.data:
            login_user(cur_user, form.remember.data)
            return redirect(request.args.get('next') or url_for('main.index'))
        # flash('用户名或密码无效!')
    return render_template('auth/login.html', form=form)


@auth.route('/logout')
@login_required
def logout():
    logout_user()
    flash('您已登出')
    return redirect(url_for('main.index'))


@auth.route('/register', methods=['GET', 'POST'])
def register():
    form = RegistryForm()
    if form.validate_on_submit():
        # noinspection PyArgumentList
        new_user = users(user_name=form.username.data,
                        user_key=form.password.data,
                        user_credit=0)
        db.session.add(new_user)
        db.session.commit()
        flash('注册成功!')
        return redirect(url_for('auth.login'))
    return render_template('auth/register.html', form=form)
