# coding=utf-8
from flask import Blueprint

main = Blueprint('main', __name__)  # 创建蓝本

from . import views, errors
