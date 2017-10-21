# -*- coding: utf-8 -*-

from flask import Flask, g, request
import pymysql

app = Flask(__name__)  #创建Flask类的实例
app.config.from_object("config")  #从config.py读入配置
config_users = {
    'host' : '127.0.0.1',
    'port' : 3306,
    'user' : 'root',
    'passwd' : '',
    'db' : 'blog',
    'charset':'utf8'
    }
def connect_db():
    return pymysql.connect(**config_users)

@app.before_request
def before_request():
    g.db = connect_db()

@app.teardown_request
def teardown_request(exception):
    db = getattr(g, 'db', None)
    if db is not None:
        db.close()
#这个import语句放在这里, 防止views, models import发生循环import
from app import views, models

