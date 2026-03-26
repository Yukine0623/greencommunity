from django.db import models

# 用户模型
class User(models.Model):
    username = models.CharField(max_length=50, unique=True)  # 用户名唯一
    password = models.CharField(max_length=128)  # 可以存明文，生产环境建议哈希
    role = models.CharField(max_length=20, default='user')  # 用户角色：user / admin / 邻里达人
    phone = models.CharField(max_length=20, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)  # 创建时间

    def __str__(self):
        return self.username


# 社区帖子 / 发布内容模型
class Post(models.Model):
    title = models.CharField(max_length=100)
    content = models.TextField()
    author = models.CharField(max_length=50)  # 可以存用户名，也可以关联 User
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.title  # 返回标题，更直观

# 申请成为邻里达人
class ExpertApplication(models.Model):
    username = models.CharField(max_length=50)

    reason = models.TextField()  # 申请理由（比如：我会修电脑）

    status = models.CharField(max_length=20, default='pending')
    # pending / approved / rejected

    created_at = models.DateTimeField(auto_now_add=True)

# 邻里达人申请记录
class Application(models.Model):
    username = models.CharField(max_length=50)
    reason = models.TextField()
    status = models.CharField(max_length=20, default='pending')  # pending / approved / rejected
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.username