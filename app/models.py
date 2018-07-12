# coding=utf-8
from . import db
from sqlalchemy.orm import relationship

article_tag = db.Table('a_t',
                       db.Column('article_id', db.Integer, db.ForeignKey('articles.article_id')),
                       db.Column('tag_id', db.Integer, db.ForeignKey('tags.tag_id')))  # tag到article有多对多关系


class article(db.Model):
    """新闻文章表"""
    __tablename__ = 'articles'

    article_id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    category_id = db.Column(db.Integer, db.ForeignKey('categories.category_id'))
    article_title = db.Column(db.String(100), nullable=False, index=True)
    article_content = db.Column(db.Text, nullable=False)
    article_author = db.Column(db.String(100), nullable=False, index=True)
    article_timestamp = db.Column(db.DateTime, nullable=False, index=True)
    article_heat = db.Column(db.Integer, nullable=False, index=True)
    article_quality = db.Column(db.Integer, nullable=False)
    article_scoretimes = db.Column(db.Integer, nullable=False)
    comments = relationship('comments', backref='articles')  # 与评论是一对多关系


class tag(db.Model):
    """标签表"""
    __tablename__ = 'tags'

    tag_id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    article_id = db.Column(db.Integer, primary_key=True)
    articles = db.relationship('articles', secondary=article_tag,
                               backref=db.backref('tags', lazy='dynamic'),
                               lazy='dynamic')


class category(db.Model):
    """类别表"""
    __tablename__ = 'categories'

    category_id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    article_id = db.Column(db.Integer, primary_key=True)
    articles = relationship('articles', backref='categories')  # 与文章是一对多关系


class comment(db.Model):
    """评论表"""
    __tablename__ = 'comments'

    comment_id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    article_id = db.Column(db.Integer, db.ForeignKey('articles.article_id'), primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.user_id'), nullable=False)
    comment_timestamp = db.Column(db.DateTime, nullable=False)
    comment_content = db.Column(db.Text, nullable=False)
    comment_karma = db.Column(db.Integer, nullable=False)
    comment_mod_timestamp = db.Column(db.DateTime, nullable=True)
    father_comment_id = db.Column(db.Integer, db.ForeignKey('comments.comment_id'), nullable=True)
    father = db.relationship('comments', uselist=False, remote_side=[comment_id], backref='sons')


class user(db.Model):
    """用户表"""
    __tablename__ = 'users'

    user_id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    user_name = db.Column(db.String(100), nullable=False)
    user_key = db.Column(db.String(100), nullable=False)
    user_intro = db.Column(db.Text, nullable=True)
    user_credit = db.Column(db.Integer, nullable=False)
    comments = relationship('comments', backref='users')
