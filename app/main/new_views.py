# coding=utf-8
from __future__ import division
from flask import make_response, request, abort, jsonify, render_template
from sqlalchemy import desc
from . import main  # 导入蓝本main
from .. import db
from ..models import users, comments, articles, tags, comment_user, article_tag
from datetime import datetime
from threading import Timer


# 错误响应
@main.errorhandler(404)
def not_found(error):
    return make_response(jsonify({'error': 'Not found'}), 404)


def get_articles(article_title=None, category_id=None, article_author=None, start_timestamp=None, tag=None):
    ret = []
    articles_all = []
    if article_title is not None:  # 按标题模糊查询
        ret = articles.query.filter(articles.article_title.like('%' + article_title + '%')).all()
    elif category_id is not None:  # 某一类的新闻
        ret = articles.query.filter_by(category_id=category_id).all()
    elif article_author is not None:  # 按作者查询
        ret = articles.query.filter_by(article_author=article_author).all()
    elif start_timestamp is not None:  # 按起始时间查询
        ret = articles.query.filter(articles.article_timestamp >= start_timestamp).all()
    elif tag is not None:  # 按标签搜索
        tag = tags.query.filter_by(tag_name=tag).first()
        if tag is None:
            return
        atcl_ids = [x.article_id for x in article_tag.query.filter_by(tag_id=tag.tag_id).all()]
        if atcl_ids is None:
            return
        for atcl_id in atcl_ids:
            ret.append(articles.query.filter_by(article_id=atcl_id).first())
    else:  # 所有新闻
        ret = articles.query.all()
    if ret is None:
        return
    for atcl in ret:
        tags_all = article_tag.query.filter_by(article_id=atcl.article_id).all()
        tag_ids = []
        for tag in tags_all:
            tag_ids.append(tag.tag_id)
        tag_list = []
        for tag_id in tag_ids:
            tag_list.append(tags.query.filter_by(tag_id=tag_id).first().tag_name)
        if atcl.article_scoretimes == 0:
            score = 0
        else:
            score = float(atcl.article_quality) / atcl.article_scoretimes
        single_article = {
            'article_id': atcl.article_id,
            'category_id': atcl.category_id,
            'article_title': atcl.article_title,
            'article_desc': atcl.article_desc,
            'article_author': atcl.article_author,
            'article_timestamp': atcl.article_timestamp,
            'article_heat': atcl.article_heat,
            'article_score': score,
            'tag_list': tag_list
        }
        articles_all.append(single_article)
    return articles_all


@main.route('/', methods=['GET', 'POST'])
def ruko():
    json = request.json
    if json:
        if 'action' in json:
            action = json['action']
            if action == 'login':
                return login(request)
            elif action == 'register':
                return register(request)
            elif action == 'index':
                return index(request)
            elif action == 'category':
                category_id = json['category_id']
                return category(request, category_id)
            elif action == 'search':
                return search(request)
            elif action == 'browse_article':
                article_id = json['article_id']
                return browse_article(request, article_id)
            elif action == 'publish':
                return publish()
            elif action == 'edit_article':
                article_id = json['article_id']
                return edit_article(request, article_id)
            elif action == 'delete_article':
                article_id = json['article_id']
                return delete_article(request, article_id)
            elif action == 'reply_comment':
                return reply_comment(request, request.json['article_id'], request.json['reply_id'])
            elif action == 'add_comment':
                return add_comment(request, request.json['article_id'])
            elif action == 'edit_comment':
                return edit_comment(request, request.json['article_id'], request.json['comment_id'])
            elif action == 'delete_comment':
                return delete_comment(request, request.json['article_id'], request.json['comment_id'])
            elif action == 'admin_delete_comment':
                return admin_delete_comment(request, request.json['article_id'],
                                            request.json['user_id'], request.json['comment_id'], 0)
            elif action == 'report_comment':
                return report_comment(request, request.json['article_id'], request.json['comment_id'])
            elif action == 'get_users':
                return get_users(request)
            elif action == 'show_user':
                return show_user(request, request.json['user_id'])
            elif action == 'delete_user':
                return delete_user(request, request.json['user_id'])

    return render_template('index.html')


def login(request):
    if request.method == 'POST':
        username = request.json['name']
        password = request.json['password']
        cur_user = users.query.filter_by(user_name=username).first()
        if cur_user is None:
            return jsonify({'result': 2})  # 用户名不存在
        elif cur_user.user_key != password:
            return jsonify({'result': 1})
        else:
            # login_user(cur_user)
            cu = {
                'user_id': cur_user.user_id,
                'user_name': cur_user.user_name,
                'user_password': cur_user.user_key,
                'user_intro': cur_user.user_intro,
                'user_credit': cur_user.user_credit,
                'user_admin': cur_user.user_admin
            }
            return jsonify({'result': 0, 'user': cu})


def register(request):
    if request.method == 'POST':
        username = request.json['name']
        password = request.json['password']
        if users.query.filter_by(user_name=username).first():
            return jsonify({'result': 1})
        else:
            last_user = users.query.order_by(desc(users.user_id)).first()
            if last_user is None:
                new_user = users(user_id=1,
                                 user_name=username,
                                 user_key=password,
                                 user_intro='Nothing to be found here.',
                                 user_credit=0,
                                 user_admin=False)
            else:
                new_user = users(user_id=last_user.user_id + 1,
                                 user_name=username,
                                 user_key=password,
                                 user_intro='Nothing to be found here.',
                                 user_credit=0,
                                 user_admin=False)
            db.session.add(new_user)
            db.session.commit()
            return jsonify({'result': 0})


# 新闻主页
def index(request):
    articles_all = get_articles()
    return jsonify({'articles': articles_all})


# 分类主页
def category(request, category_id):
    articles_all = get_articles(category_id=category_id)
    return jsonify({'articles': articles_all})


# 搜索
def search(request):
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
def browse_article(request, article_id):
    comment_list = get_comments(article_id)
    atcl = articles.query.filter_by(article_id=article_id).first()
    atcl.article_heat += 1  # 热度 + 1
    if request.json:
        if 'score' in request.json:
            atcl.article_quality += request.json['score']
            atcl.article_scoretimes += 1
            # 用户评分增加信誉度
            usr = users.query.filter_by(user_id=request.json['user_id']).first()
            usr.user_credit = usr.user_credit + 1
            db.session.add(usr)
            db.session.commit()
    db.session.add(atcl)
    db.session.commit()
    tag_ids = [x.tag_id for x in article_tag.query.filter_by(article_id=atcl.article_id).all()]
    tag_list = []
    for tag_id in tag_ids:
        tag_list.append(tags.query.filter_by(tag_id=tag_id).first().tag_name)
    if atcl.article_scoretimes == 0:
        score = 0
    else:
        score = float(atcl.article_quality) / atcl.article_scoretimes
    single_article = {
        'article_id': atcl.article_id,
        'category_id': atcl.category_id,
        'article_title': atcl.article_title,
        'article_desc': atcl.article_desc,
        'article_content': atcl.article_content,
        'article_author': atcl.article_author,
        'article_timestamp': atcl.article_timestamp,
        'article_heat': atcl.article_heat,
        'article_score': score,
        'tag_list': tag_list,
        'comment_list': comment_list
    }
    return jsonify({'article': single_article})


# 添加新闻
@main.route('/publish', methods=['GET', 'POST'])
def publish(request):
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
    article = articles.query.filter_by(article_title=request.json['title']).first()
    if article is None:
        return jsonify({'result': 1})

    tag_list = request.json['tags']
    for tag in tag_list:
        if tags.query.filter_by(tag_name=tag).first() is None:
            last_tag_id = tags.query.order_by(desc(tags.tag_id)).first().tag_id
            new_tag = tags(tag_id=last_tag_id + 1, tag_name=tag)
            db.session.add(new_tag)
            db.session.commit()
        tag_id = tags.query.filter_by(tag_name=tag).first().tag_id
        new_article_tag_pair = article_tag(article_id=article.article_id, tag_id=tag_id)
        db.session.add(new_article_tag_pair)
        db.session.commit()
    return jsonify({'result': 0})


# 修改新闻
@main.route('/article/<int:article_id>/edit', methods=['POST', 'GET'])
def edit_article(request, article_id):
    # if current_user.user_admin:
    dat_article = articles.query.filter_by(article_id=article_id).first()
    if 'title' in request.json:
        dat_article.article_title = request.json['title']
    if 'desc' in request.json:
        dat_article.article_desc = request.json['desc']
    # dat_article.category_id = request.json['category']
    # dat_article.article_author = request.json['author']
    if 'content' in request.json:
        dat_article.article_content = request.json['content']
    # dat_article.article_timestamp = request.json['time']
    db.session.add(dat_article)
    db.session.commit()
    # new_tag_list = request.json['tags']
    # old_tag_id_list = article_tag.query.filter_by(article_id=article_id).all()
    # old_tag_list = []
    # for old_tag_id in old_tag_id_list:
    #     old_tag_list.append(tags.query.filter_by(tag_id=old_tag_id).first().tag_name)
    # deleted_tags = list(set(old_tag_list).difference(set(new_tag_list)))
    # added_tags = list(set(new_tag_list).difference(set(old_tag_list)))
    # for tag in deleted_tags:
    #     tag_id = tags.query.filter_by(tag_name=tag).first().tag_id
    #     for deleted_pair in article_tag.query.filter_by(tag_id=tag_id).all():
    #         db.session.delete(deleted_pair)
    # db.session.commit()
    # for tag in added_tags:
    #     if tags.query.filter_by(tag_name=tag).first() is None:
    #         new_tag = tags(tag_name=tag)
    #         db.session.add(new_tag)
    #         db.session.commit()
    #     tag_id = tags.query.filter_by(tag_name=tag).first().tag_id
    #     new_article_tag_pair = article_tag(article_id=article_id, tag_id=tag_id)
    #     db.session.add(new_article_tag_pair)
    # db.session.commit()
    return jsonify({'result': 0})


# 删除新闻
@main.route('/article/<int:article_id>/delete', methods=['POST', 'GET'])
def delete_article(request, article_id):
    deleted_article = articles.query.filter_by(article_id=article_id).first()
    deleted_comments = comments.query.filter_by(article_id=article_id).all()
    deleted_pairs = article_tag.query.filter_by(article_id=article_id).all()

    for d_comment in deleted_comments:
        db.session.delete(d_comment)
    for deleted_pair in deleted_pairs:
        db.session.delete(deleted_pair)
    db.session.delete(deleted_article)
    db.session.commit()
    return jsonify({'result': 0})


def get_usr(user_id):
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
    return q_user, user_comments


# 获得某一个评论的点赞用户列表
def get_endorse_use(request, comment_id):
    ans = comment_user.query.filter_by(comment_id=comment_id)
    usr = []
    for com in ans:
        user_info, _ = get_usr(com.user_id)
        usr.append(user_info)
    return usr


# 获得全部的评论，返回一个列表
def get_comments(request, article_id):
    comments_all = []
    ans = comments.query.filter_by(article_id=article_id).all()
    for com in ans:
        user_name = users.query.filter_by(user_id=com.user_id).first().user_name
        single_comment = {
            'article_id': com.article_id,  # 文章id
            'comment_id': com.comment_id,  # 评论id
            'starred_user': get_endorse_use(com.comment_id),  # 点赞列表
            'user_id': com.user_id,  # 用户id
            'user_name': user_name,  # 用户姓名
            'comment_content': com.comment_content,  # 评论内容
            'comment_timestamp': com.comment_timestamp,  # 评论时间
            'comment_karma': com.comment_karma,  # 点赞数量
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
def reply_comment(request, article_id, reply_id):
    if not request.json:
        abort(400)
    credit = users.query.filter_by(user_id=request.json['user_id']).first().user_credit
    comments_all = get_comments(article_id)
    sorted_comments = sorted(comments_all, key=lambda x: (-x['comment_karma'], x['comment_timestamp']))
    # 信誉度低无法评论
    if credit < 0:
        return jsonify({'result': 0, 'comments': sorted_comments})
    user_name = users.query.filter_by(user_id=request.json['user_id']).first().user_name
    single_comment = {
        'article_id': article_id,  # 文章id
        # 'comment_id': comments_all[-1]['comment_id'] + 1,   # 评论id
        'starred_user': [],  # 点赞用户列表
        "user_id": request.json['user_id'],  # 用户id
        'user_name': user_name,  # 用户姓名
        'comment_content': request.json['content'],  # 评论内容
        'comment_timestamp': datetime.now(),  # 评论时间
        'comment_karma': 0,  # 点赞数量
        'comment_mod_timestamp': datetime.now(),  # 最后修改时间
        'is_reply': True,  # 是否是评论的回复
        'father_comment_id': reply_id,  # 回复的评论的id
        # 回复的评论内容
        'father_comment_content': comments.query.filter_by(comment_id=reply_id).first().comment_content,
        # 回复的评论的用户名
        'father_comment_user': users.query.filter_by(
            user_id=comments.query.filter_by(
                comment_id=reply_id).first().user_id).first().user_name
    }
    if len(comments_all) == 0:
        single_comment['comment_id'] = 1
    else:
        single_comment['comment_id'] = comments_all[-1]['comment_id'] + 1
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
    return jsonify({'result': 0, 'comments': sorted_comments})


# 添加评论
@main.route('/article/<int:article_id>/comment', methods=['POST'])
def add_comment(request, article_id):
    if not request.json:
        abort(400)
    credit = users.query.filter_by(user_id=request.json['user_id']).first().user_credit
    comments_all = get_comments(article_id)
    sorted_comments = sorted(comments_all, key=lambda x: (-x['comment_karma'], x['comment_timestamp']))
    # 信誉度低无法评论
    if credit < 0:
        return jsonify({'result': 0, 'comments': sorted_comments})
    user_name = users.query.filter_by(user_id=request.json['user_id']).first().user_name
    single_comment = {
        'article_id': article_id,  # 文章id
        # 'comment_id': comments_all[-1]['comment_id'] + 1,   # 评论id
        'user_id': request.json['user_id'],  # 用户id
        'starred_user': [],  # 点赞用户列表
        'user_name': user_name,  # 用户名
        'comment_content': request.json['content'],  # 评论内容
        'comment_timestamp': datetime.now(),  # 评论时间
        'comment_karma': 0,  # 点赞数量
        'comment_mod_timestamp': datetime.now(),  # 最后修改时间
        'is_reply': False
    }
    if len(comments_all) == 0:
        single_comment['comment_id'] = 1
    else:
        single_comment['comment_id'] = comments_all[-1]['comment_id'] + 1
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
    return jsonify({'result': 0, 'comments': sorted_comments})


# 修改评论
@main.route('/article/<int:article_id>/<int:comment_id>/edit', methods=['POST'])
def edit_comment(request, article_id, comment_id):
    if not request.json or 'content' not in request.json:
        abort(400)
    com = comments.query.filter_by(article_id=article_id, comment_id=comment_id).first()
    user_name = users.query.filter_by(user_id=com.user_id).first().user_name
    single_comment = {
        'article_id': com.article_id,  # 文章id
        'comment_id': com.comment_id,  # 评论id
        'starred_user': get_endorse_use(com.comment_id),  # 点赞列表
        'user_name': user_name,  # 用户名
        'comment_content': request.json['content'],  # 评论内容
        'comment_timestamp': com.comment_timestamp,  # 评论时间
        'comment_karma': com.comment_karma,  # 点赞数量ac
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
    com.comment_content = request.json['content']
    db.session.add(com)
    db.session.commit()
    return jsonify({'comment': single_comment})


# 删除评论，用户删除
@main.route('/article/<int:article_id>/<int:comment_id>/delete', methods=['GET'])
def delete_comment(request, article_id, comment_id):
    com = comments.query.filter_by(article_id=article_id, comment_id=comment_id).first()
    usrs = comment_user.query.filter_by(article_id=article_id, comment_id=comment_id).all()
    for usr in usrs:
        db.session.delete(usr)
    db.session.delete(com)
    db.session.commit()
    return jsonify({'result': 0})


# 删除评论，管理员删除,需要降低信誉度
@main.route('/admin/article/<int:article_id>/<int:comment_id>/delete', methods=['GET'])
def admin_delete_comment(request, article_id, comment_id):
    com = comments.query.filter_by(article_id=article_id, comment_id=comment_id).first()
    usr = users.query.filter_by(user_id=com.user_id).first()
    usr.user_credit = usr.user_credit - 5
    db.session.add(usr)
    db.session.delete(com)
    usrs = comment_user.query.filter_by(article_id=article_id, comment_id=comment_id).all()
    for u in usrs:
        db.session.delete(u)
    db.session.commit()
    return jsonify({'result': 0})


# 给评论点赞/点灭
@main.route('/article/<int:article_id>/<int:user_id>/<int:comment_id>/light/<int:flag>', methods=['GET'])
def light_comment(request, article_id, user_id, comment_id, flag):
    if flag == 1:
        flag = -1
    else:
        flag = 1
    com = comments.query.filter_by(article_id=article_id, comment_id=comment_id).first()
    user = users.query.filter_by(user_id=user_id).first()
    com.comment_karma = com.comment_karma + flag
    if com.comment_karma == 10:
        user.user_credit += 1
    light = comment_user(comment_id=comment_id, article_id=article_id, user_id=user_id)
    db.session.add(light)
    db.session.add(user)
    db.session.add(com)
    db.session.commit()
    return jsonify({'result': 0})


# 举报评论
@main.route('/article/<int:article_id>/<int:comment_id>/report', methods=['GET'])
def report_comment(request, article_id, comment_id):
    com = comments.query.filter_by(article_id=article_id, comment_id=comment_id).first()
    com.comment_report_sign = True
    db.session.add(com)
    db.session.commit()
    return jsonify({'result': 0})


# 返回被举报的评论的列表
@main.route('/admin/report_comments', methods=['GET'])
def get_report_comments(request):
    comments_all = []
    ans = comments.query.filter_by(comment_report_sign=True).all()
    for com in ans:
        user_name = users.query.filter_by(user_id=com.user_id).first().user_name
        single_comment = {
            'article_id': com.article_id,  # 文章id
            'comment_id': com.comment_id,  # 评论id
            'starred_user': get_endorse_use(com.comment_id),  # 点赞列表
            'user_id': com.user_id,  # 用户id
            'user_name': user_name,  # 用户姓名
            'comment_content': com.comment_content,  # 评论内容
            'comment_timestamp': com.comment_timestamp,  # 评论时间
            'comment_karma': com.comment_karma,  # 点赞数量
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
    return jsonify({'comments': comments_all})


# 返回全部用户
@main.route('/admin/manage_user', methods=['GET'])
def get_users(request):
    all_user = users.query.all()
    all_users = []
    for usr in all_user:
        q_user = {
            'user_id': usr.user_id,
            'name': usr.user_name,
            'intro': usr.user_intro,
            'credit': usr.user_credit
        }
        all_users.append(q_user)
    return jsonify({'users': all_users})


# 用户主页
@main.route('/user/<int:user_id>', methods=['GET'])
def show_user(request, user_id):
    q_user, user_comments = get_usr(user_id)
    return jsonify({'user_id': q_user.user_id,
                    'name': q_user.user_name,
                    'intro': q_user.user_intro,
                    'credit': q_user.user_credit,
                    'comments': user_comments})


# 定时修改用户信誉度
def change_credit():
    all_users = users.query.all()
    for usr in all_users:
        if usr.user_credit < 0:
            usr.user_credit += 1
            db.session.add(usr)
    db.session.commit()
    t = Timer(1, change_credit)
    print "running"
    t.start()


# 删除用户，包括用户的评论也会全部删除
@main.route('/user/<int:user_id>/delete', methods=['GET'])
def delete_user(request, user_id):
    q_user = users.query.filter_by(user_id=user_id).first()
    q_comments = comments.query.filter_by(user_id=user_id).all()
    q_usr_com = comment_user.query.filter_by(user_id=user_id).all()
    for uc in q_usr_com:
        db.session.delete(uc)
    for com in q_comments:
        db.session.delete(com)
    db.session.delete(q_user)
    db.session.commit()
    return jsonify({'result': 0})


if __name__ == "__main__":
    change_credit()
