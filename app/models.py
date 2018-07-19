# coding=utf-8
from . import db
from sqlalchemy.orm import relationship
from flask_login import UserMixin
from . import lm

# article_tag = db.Table('a_t',
#                        db.Column('article_id', db.Integer, db.ForeignKey('articles.article_id')),
#                        db.Column('tag_id', db.Integer, db.ForeignKey('tags.tag_id')))  # tags到articles有多对多关系


class article_tag(db.Model):
    __tablename__ = 'article_tag'
    article_id = db.Column(db.Integer, db.ForeignKey('articles.article_id'), primary_key=True)
    tag_id = db.Column(db.Integer, db.ForeignKey('tags.tag_id'), primary_key=True)


class articles(db.Model):
    """新闻文章表"""
    __tablename__ = 'articles'

    article_id = db.Column(db.Integer, primary_key=True)
    category_id = db.Column(db.Integer, nullable=False)
    article_title = db.Column(db.String(100), nullable=False, index=True)
    article_desc = db.Column(db.Text, nullable=False)
    article_content = db.Column(db.Text, nullable=False)
    article_author = db.Column(db.String(100), nullable=False, index=True)
    article_timestamp = db.Column(db.DateTime, nullable=False, index=True)
    article_heat = db.Column(db.Integer, nullable=False, index=True)
    article_quality = db.Column(db.Integer, nullable=False)
    article_scoretimes = db.Column(db.Integer, nullable=False)
    comments = relationship('comments', backref='articles')  # 与评论是一对多关系


class tags(db.Model):
    """标签表"""
    __tablename__ = 'tags'

    tag_id = db.Column(db.Integer, primary_key=True)
    tag_name = db.Column(db.String(100), unique=True)


# comment_user = db.Table('c_u',
#                         db.Column('user_id', db.Integer, db.ForeignKey('users.user_id')),
#                         db.Column('comment_id', db.Integer),
#                         db.Column('article_id', db.Integer),
#                         ForeignKeyConstraint(
#                             ('comment_id', 'article_id'),
#                             ('comments.comment_id', 'articles.article_id')
#                         ))  # comments到users有多对多的点赞关系


class comment_user(db.Model):
    """comments到users有多对多的点赞关系"""
    comment_id = db.Column(db.Integer, db.ForeignKey('comments.comment_id'), primary_key=True)
    article_id = db.Column(db.Integer, db.ForeignKey('comments.article_id'), primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.user_id'), primary_key=True)


class comments(db.Model):
    """评论表"""
    __tablename__ = 'comments'

    comment_id = db.Column(db.Integer, primary_key=True)
    article_id = db.Column(db.Integer, db.ForeignKey('articles.article_id'), primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.user_id'), nullable=False)
    comment_timestamp = db.Column(db.DateTime, nullable=False)
    comment_content = db.Column(db.Text, nullable=False)
    comment_karma = db.Column(db.Integer, nullable=False)
    comment_mod_timestamp = db.Column(db.DateTime, nullable=True)
    comment_report_sign = db.Column(db.Boolean, nullable=True)
    father_comment_id = db.Column(db.Integer, db.ForeignKey('comments.comment_id'), nullable=True)
    father = db.relationship('comments', uselist=False, remote_side=[comment_id], backref='sons')
    # starred_users = db.relationship('users', secondary=comment_user,
    #                                 backref=db.backref('starred_comments', lazy='dynamic'),
    #                                 lazy='dynamic')


class users(db.Model):
    """用户表"""
    __tablename__ = 'users'

    user_id = db.Column(db.Integer, primary_key=True)
    user_name = db.Column(db.String(100), nullable=False, unique=True, index=True)
    user_key = db.Column(db.String(100), nullable=False)
    user_intro = db.Column(db.Text, nullable=True)
    user_credit = db.Column(db.Integer, nullable=False)
    user_admin = db.Column(db.Boolean, nullable=False)
    comments = relationship('comments', backref='users')


@lm.user_loader
def load_user(user_id):
    return users.query.get(int(user_id))
