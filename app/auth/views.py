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
    # form = login_form()
    # if form.validate_on_submit():
    pass


@auth.route('/register', methods=['GET', 'POST'])
def register():
    form = registry_form()
    if form.validate_on_submit():
        new_user = user(
            user_name=form.username.data,
            user_key=form.password.data,
            user_credit=0
            )
        db.session.add(new_user)
        db.session.commit()
        flash('注册成功!')
        return redirect(url_for('auth.login'))
    return render_template('auth/register.html', form=form)
