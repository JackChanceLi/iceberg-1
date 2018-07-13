# coding=utf-8
from flask import Flask, render_template, redirect, url_for, request, flash
from . import main  # 导入蓝本main
from .. import db
from .forms import *
from ..models import *
from werkzeug.utils import secure_filename
