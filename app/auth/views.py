# coding=utf-8
from flask import render_template, redirect, url_for, request, flash, jsonify
from flask_login import login_user, logout_user, login_required, current_user
from sqlalchemy import desc
from . import auth  # 导入蓝本auth
from .. import db
from ..models import users
from werkzeug.utils import secure_filename


@auth.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.json['name']
        password = request.json['password']
        cur_user = users.query.filter_by(user_name=username).first()
        if cur_user is None:
            return jsonify({'result': 2})  # 用户名不存在
        elif cur_user.user_key != password:
            return jsonify({'result': 1})
        else:
            login_user(cur_user)
            cu = {
                'user_id': cur_user.user_id,
                'user_name': cur_user.user_name,
                'user_password': cur_user.user_key,
                'user_intro': cur_user.user_intro,
                'user_credit': cur_user.user_credit,
                'user_admin': cur_user.user_admin
            }
            return jsonify({'result': 0, 'user': cu})


@auth.route('/logout')
@login_required
def logout():
    logout_user()


@auth.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.json['name']
        password = request.json['password']
        if users.query.filter_by(user_name=username).first():
            return jsonify({'result': 1})
        else:
            last_id = users.query.order_by(desc(users.user_id)).first()
            new_user = users(user_id=last_id + 1,
                             user_name=username,
                             user_key=password,
                             user_intro='这里空空如也',
                             user_credit=0,
                             user_admin=False)
            db.session.add(new_user)
            db.session.commit()
            return jsonify({'result': 0})
