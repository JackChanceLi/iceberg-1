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

#### 更新数据库表

+ 从其他版本处

执行

```
(venv) $ python manage.py db upgrade
```

+ 在本地自行更新

执行

```
(venv) $ python manage.py db migrate
(venv) $ python manage.py db upgrade
```
