# coding=utf-8
from __future__ import division
from flask import make_response, request, abort, jsonify
from . import main  # 导入蓝本main
from .. import db
from ..models import users, comments, articles, tags
from datetime import datetime


# 错误响应
@main.errorhandler(404)
def not_found(error):
    return make_response(jsonify({'error': 'Not found'}), 404)


def get_articles(article_title=None, category_id=None, article_author=None, start_timestamp=None, tag=None):
    global ret
    articles_all = []
    if article_title is not None:  # 按标题模糊查询
        ret = articles.query.filter(articles.article_title.like('%'+article_title+'%')).all()
    elif category_id is not None:  # 某一类的新闻
        ret = articles.query.filter_by(category_id=category_id).all()
    elif article_author is not None:  # 按作者查询
        ret = articles.query.filter_by(article_author=article_author).all()
    elif start_timestamp is not None:  # 按起始时间查询
        ret = articles.query.filter(articles.article_timestamp >= start_timestamp).all()
    elif tag is not None:  # 按标签搜索
        atcl_ids = [x.article_id for x in tags.query.filter_by(tag_id=tag).all()]
        for atcl_id in atcl_ids:
            ret.append(articles.query.filter_by(article_id=atcl_id).first())
    else:  # 所有新闻
        ret = articles.query.all()
    for atcl in ret:
        single_article = {
            'article_id': atcl.article_id,
            'category_id': atcl.category_id,
            'article_title': atcl.article_title,
            'article_desc': atcl.article_desc,
            'article_author': atcl.article_author,
            'article_timestamp': atcl.article_timestamp,
            'article_heat': atcl.article_heat,
            'article_score': float(atcl.article_quality) / atcl.article_scoretimes,
            'tag_list': list(tags.query.filter_by(article_id=atcl.article_id).all())
        }
        articles_all.append(single_article)
    return articles_all


# 新闻主页
@main.route('/index', methods=['GET', 'POST'])
def index():
    articles_all = get_articles()
    return jsonify({'articles': articles_all})


# 分类主页
@main.route('/category/<int:category_id>', methods=['GET', 'POST'])
def category(category_id):
    articles_all = get_articles(category_id=category_id)
    return jsonify({'articles': articles_all})


# 搜索
@main.route('/search', methods=['GET', 'POST'])
def search():
    search_type = request.json['search_type']
    keyword = request.json['keyword']
    if search_type == 0:  # 按标题搜索
        result = get_articles(article_title=keyword)
        return jsonify({'articles': result})
    elif search_type == 1:  # 标签
        result = get_articles(tag=keyword)
        return jsonify({'articles': result})
    elif search_type == 2:  # 起始时间
        result = get_articles(start_timestamp=keyword)
        return jsonify({'articles': result})
    elif search_type == 3:  # 按作者搜索
        result = get_articles(article_author=keyword)
        return jsonify({'articles': result})


# 查看新闻
@main.route('/article/<int:article_id>', methods=['GET', 'POST'])
def browse_article(article_id):
    comment_list = get_comments(article_id)
    atcl = articles.query.filter_by(article_id=article_id).first()
    atcl.article_heat += 1  # 热度 + 1
    if 'score' in request.json:
        atcl.article_quality += request.json['score']
    db.session.add(atcl)
    db.session.commit()
    single_article = {
        'article_id': atcl.article_id,
        'category_id': atcl.category_id,
        'article_title': atcl.article_title,
        'article_content': atcl.article_content,
        'article_author': atcl.article_author,
        'article_timestamp': atcl.article_timestamp,
        'article_heat': atcl.article_heat,
        'article_score': float(atcl.article_quality) / atcl.article_scoretimes,
        'tag_list': list(tags.query.filter_by(article_id=atcl.article_id).all()),
        'comment_list': comment_list
    }
    return jsonify({'article': single_article})


# 添加新闻
@main.route('/publish', methods=['GET', 'POST'])
def publish():
    # if current_user.user_admin:
    new_article = articles(article_title=request.json['title'],
                           category_id=request.json['category'],
                           article_author=request.json['author'],
                           article_desc=request.json['desc'],
                           article_content=request.json['content'],
                           article_timestamp=request.json['time'],
                           article_heat=0,
                           article_quality=0,
                           article_scoretimes=0)
    db.session.add(new_article)
    db.session.commit()
    tag_list = request.json['tags']
    for tag in tag_list:
        new_tag_pair = tags(tag_id=tag, article_id=new_article.article_id)
        db.session.add(new_tag_pair)
    db.session.commit()
    return jsonify({'result': 0})


# 修改新闻
@main.route('/article/<int:article_id>/edit', methods=['POST', 'GET'])
def edit_article(article_id):
    # if current_user.user_admin:
    dat_article = articles.query.filter_by(article_id=article_id).first()
    dat_article.article_title = request.json['title']
    dat_article.article_desc = request.json['desc']
    dat_article.category_id = request.json['category']
    dat_article.article_author = request.json['author']
    dat_article.article_content = request.json['content']
    dat_article.article_timestamp = request.json['time']
    db.session.add(dat_article)
    db.session.commit()
    new_tag_list = request.json['tags']
    old_tag_list = list(tags.query.filter_by(article_id=article_id).all())
    deleted_tags = list(set(old_tag_list).difference(set(new_tag_list)))
    added_tags = list(set(new_tag_list).difference(set(old_tag_list)))
    for tag in deleted_tags:
        tag_atcl = tags.query.filter_by(tag_id=tag, article_id=article_id).first()
        db.session.delete(tag_atcl)
    for tag in added_tags:
        tag_atcl = tags(tag_id=tag, article_id=article_id)
        db.session.add(tag_atcl)
    db.session.commit()
    return jsonify({'result': 0})


# 删除新闻
@main.route('/article/<int:article_id>/delete', methods=['POST', 'GET'])
def delete_article(article_id):
    # if current_user.user_admin:
    deleted_article = articles.query.filter_by(article_id=article_id).first()
    deleted_tags = tags.query.filter_by(article_id=article_id).all()
    deleted_comments = comments.query.filter_by(article_id=article_id).all()
    for d_comment in deleted_comments:
        db.session.delete(d_comment)
    for d_tag in deleted_tags:
        db.session.delete(d_tag)
    db.session.delete(deleted_article)
    db.session.commit()
    return jsonify({'result': 0})


# 获得全部的评论，返回一个列表
def get_comments(article_id):
    comments_all = []
    ans = comments.query.filter_by(article_id=article_id).all()
    for com in ans:
        user_name = users.query.filter_by(user_id=com.user_id).first().user_name
        single_comment = {
            'article_id': com.article_id,                  # 文章id
            'comment_id': com.comment_id,                  # 评论id
            'user_name': user_name,                        # 用户姓名
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
    user_name = users.query.filter_by(user_id=request.json['user_id']).first().user_name
    single_comment = {
        'article_id': article_id,                           # 文章id
        'comment_id': comments_all[-1]['comment_id'] + 1,   # 评论id
        'user_name': user_name,                             # 用户姓名
        'comment_content': request.json['content'],         # 评论内容
        'comment_timestamp': datetime.now(),                # 评论时间
        'comment_karma': 0,                                 # 点赞数量
        'comment_mod_timestamp': datetime.now(),            # 最后修改时间
        'is_reply': True,                                   # 是否是评论的回复
        'father_comment_id': reply_id,                      # 回复的评论的id
        # 回复的评论内容
        'father_comment_content': comments.query.filter_by(father_comment_id=reply_id).first().comment_content,
        # 回复的评论的用户名
        'father_comment_user': users.query.filter_by(
            user_id=comments.query.filter_by(
                father_comment_id=reply_id).first().user_id).first().user_name
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
    db.session.commit()
    comments_all.append(single_comment)
    sorted_comments = sorted(comments_all, key=lambda x: (-x['comment_karma'], x['comment_timestamp']))
    return jsonify({'comments': sorted_comments})


# 添加评论
@main.route('/article/<int:article_id>/comment', methods=['POST'])
def add_comment(article_id):
    if not request.json:
        abort(400)
    comments_all = get_comments(article_id)
    user_name = users.query.filter_by(user_id=request.json['user_id']).first().user_name
    single_comment = {
        'article_id': article_id,                           # 文章id
        'comment_id': comments_all[-1]['comment_id'] + 1,   # 评论id
        'user_name': user_name,                             # 用户名
        'comment_content': request.json['content'],         # 评论内容
        'comment_timestamp': datetime.now(),                # 评论时间
        'comment_karma': 0,                                 # 点赞数量
        'comment_mod_timestamp': datetime.now(),            # 最后修改时间
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
    return jsonify({'comments': sorted_comments})


# 修改评论
@main.route('/article/<int:article_id>/<int:comment_id>/edit', methods=['POST'])
def edit_comment(article_id, comment_id):
    if not request.json or 'content' not in request.json:
        abort(400)
    com = comments.query.filter_by(article_id=article_id, comment_id=comment_id).first()
    user_name = users.query.filter_by(user_id=com.user_id).first().user_name
    single_comment = {
        'article_id': com.article_id,                           # 文章id
        'comment_id': com.comment_id,                           # 评论id
        'user_name': user_name,                                 # 用户名
        'comment_content': request.json['content'],             # 评论内容
        'comment_timestamp': com.comment_timestamp,             # 评论时间
        'comment_karma': com.comment_karma,                     # 点赞数量ac
        'comment_mod_timestamp': com.comment_mod_timestamp,     # 最后修改时间
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
    com.comment_content = request.json['content']
    db.session.add(com)
    db.session.commit()
    return jsonify({'comment': single_comment})


# 删除评论
@main.route('/article/<int:article_id>/<int:comment_id>/delete', methods=['GET'])
def delete_comment(article_id, comment_id):
    com = comments.query.filter_by(article_id=article_id, comment_id=comment_id).first()
    db.session.delete(com)
    db.session.commit()
    return jsonify({'result': 0})


# 给评论点赞/点灭
@main.route('/article/<int:article_id>/<int:comment_id>/light/<int:flag>', methods=['GET'])
def light_comment(article_id, comment_id, flag):
    if flag == 1:
        flag = -1
    else:
        flag = 1
    com = comments.query.filter_by(article_id=article_id, comment_id=comment_id).first()
    com.comment_karma = com.comment_karma + flag
    db.session.add(com)
    db.session.commit()
    return jsonify({'result': 0})


# 用户主页
@main.route('/user/<int:user_id>', methods=['GET'])
def show_user(user_id):
    q_user = users.query.filter_by(user_id=user_id).first()
    user_comments = []
    q_comments = comments.query.filter_by(user_id=user_id).all()
    for com in q_comments:
        user_name = users.query.filter_by(user_id=com.user_id).first().user_name
        single_comment = {
            'article_id': com.article_id,  # 文章id
            'comment_id': com.comment_id,  # 评论id
            'user_name': user_name,  # 用户id
            'comment_content': com.comment_content,  # 评论内容
            'comment_timestamp': com.comment_timestamp,  # 评论时间
            'comment_karma': com.comment_karma,  # 点赞数量
            'comment_mod_timestamp': com.comment_mod_timestamp,  # 最后修改时间
            'article_title': articles.query.filter_by(article_id=com.article_id).first().article_title
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
        user_comments.append(single_comment)
    return jsonify({'name': q_user.user_name,
                    'intro': q_user.user_intro,
                    'credit': q_user.user_credit,
                    'comments': user_comments})


# 删除用户，包括用户的评论也会全部删除
@main.route('/user/<int:user_id>/delete', methods=['GET'])
def delete_user(user_id):
    q_user = users.query.filter_by(user_id=user_id).first()
    q_comments = comments.query.filter_by(user_id=user_id).all()
    for com in q_comments:
        db.session.delete(com)
    db.session.delete(q_user)
    db.session.commit()
    return jsonify({'result': 0})
