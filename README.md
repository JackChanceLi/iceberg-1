# iceberg
database course design

#### 创建数据库表

在数据库中新建dev、test、prd三个schema,

修改config.py中的SQLALCHEMY_DATABASE_URI为`mysql+pymysql://username:password@hostname/database`,

然后执行
```
(venv) $ python manage.py shell
>>> db.create_all()
```
