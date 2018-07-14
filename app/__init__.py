# coding=utf-8
from flask import Flask, render_template
from config import config
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager

db = SQLAlchemy()
lm = LoginManager()
lm.session_protection = 'basic'
lm.login_view = 'auth.login'

def create_app(config_name):
    app = Flask(__name__)
    app.config.from_object(config[config_name])
    config[config_name].init_app(app)

    db.init_app(app)
    lm.init_app(app)

    from .main import main as main_blueprint
    app.register_blueprint(main_blueprint)  # 注册蓝本

    from .auth import auth as auth_blueprint
    app.register_blueprint(auth_blueprint, url_prefix='/auth')

    return app
