# coding=utf-8
from flask import Flask, render_template, redirect, url_for, request, flash, make_response, request, abort, jsonify
from . import main  # 导入蓝本main
from .. import db
from .forms import *
from ..models import users, comments
from werkzeug.utils import secure_filename
from datetime import datetime


# 错误响应
@main.errorhandler(404)
def not_found(error):
    return make_response(jsonify({'error': 'Not found'}), 404)


# 获得全部的评论，返回一个列表
def get_comments(article_id):
    comments_all = []
    ans = comments.query.all()
    for com in ans:
        single_comment = {
            'article_id': com.article_id,                  # 文章id
            'comment_id': com.comment_id,                  # 评论id
            'user_id': com.user_id,                        # 用户id
            'comment_content': com.comment_content,        # 评论内容
            'comment_timestamp': com.comment_timestamp,    # 评论时间
            'comment_karma': com.comment_karma,            # 点赞数量
            'comment_mod_timestamp': com.comment_mod_timestamp,  # 最后修改时间
        }
        if com.father_comment_id is not None:
            single_comment['is_reply'] = True
            single_comment['father_comment_content'] = \
                comments.query.filter_by(father_comment_id=com.father_comment_id).first().comment_content
            single_comment['father_comment_user'] = \
                users.query.filter_by(user_id=comments.query.filter_by(
                    father_comment_id=com.father_comment_id).first().user_id).first().user_name
        else:
            single_comment['is_reply'] = False
        comments_all.append(single_comment)
    return comments_all


# 添加评论的回复
@main.route('/article/<int:article_id>/<int:reply_id>/comment', methods=['POST'])
def reply_comment(article_id, reply_id):
    if not request.json:
        abort(400)
    comments_all = get_comments(article_id)
    single_comment = {
        'article_id': article_id,                       # 文章id
        'comment_id': comments_all[-1]['comment_id'] + 1,   # 评论id
        'user_id': request.json['user_id'],             # 用户id
        'comment_content': request.json['content'],     # 评论内容
        'comment_timestamp': datetime.now(),            # 评论时间
        'comment_karma': 0,                             # 点赞数量
        'comment_mod_timestamp': datetime.now(),        # 最后修改时间
        'is_reply': True,                               # 是否是评论的回复
        'father_comment_id': reply_id,                  # 回复的评论的id
        'father_comment_content': comments.query.filter_by(reply_id).comment_content,  # 回复的评论内容
        'father_comment_user': users.query.filter_by(comments.query.filter_by(reply_id).user_id).user_name  # 回复的评论的用户名
    }
    new_comment = comments(comment_id=single_comment['comment_id'],
                           article_id=article_id,
                           user_id=single_comment['user_id'],
                           comment_content=single_comment['comment_content'],
                           comment_timestamp=single_comment['comment_timestamp'],
                           comment_karma=single_comment['comment_karma'],
                           comment_mod_timestamp=single_comment['comment_mod_timestamp'],
                           father_comment_id=reply_id)
    db.session.add(new_comment)
    comments_all.append(single_comment)
    sorted_comments = sorted(comments_all, key=lambda x: (-x['comment_karma'], x['comment_timestamp']))
    return jsonify({'comments':sorted_comments})


# 添加评论
@main.route('/article/<int:article_id>/comment', methods=['POST'])
def add_comment(article_id):
    if not request.json:
        abort(400)
    comments_all = get_comments(article_id)
    single_comment = {
        'article_id': article_id,                       # 文章id
        'comment_id': comments_all[-1]['comment_id'] + 1,   # 评论id
        'user_id': request.json['user_id'],             # 用户id
        'comment_content': request.json['content'],     # 评论内容
        'comment_timestamp': datetime.now(),            # 评论时间
        'comment_karma': 0,                             # 点赞数量
        'comment_mod_timestamp': datetime.now(),        # 最后修改时间
        'is_reply': False
    }
    new_comment = comments(comment_id=single_comment['comment_id'],
                           article_id=article_id,
                           user_id=single_comment['user_id'],
                           comment_content=single_comment['comment_content'],
                           comment_timestamp=single_comment['comment_timestamp'],
                           comment_karma=single_comment['comment_karma'],
                           comment_mod_timestamp=single_comment['comment_mod_timestamp'])
    db.session.add(new_comment)
    db.session.commit()
    comments_all.append(single_comment)
    sorted_comments = sorted(comments_all, key=lambda x: (-x['comment_karma'], x['comment_timestamp']))
    return jsonify({'comments':sorted_comments})



