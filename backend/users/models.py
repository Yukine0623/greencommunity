from django.db import models

# 用户模型
class User(models.Model):
    username = models.CharField(max_length=50, unique=True)  # 用户名唯一
    password = models.CharField(max_length=128)  # 可以存明文，生产环境建议哈希
    role = models.CharField(max_length=20, default='user')  # 用户角色：user / admin / 邻里达人
    phone = models.CharField(max_length=20, null=True, blank=True)
    points = models.IntegerField(default=100, verbose_name="互助积分")
    created_at = models.DateTimeField(auto_now_add=True)  # 创建时间

    def __str__(self):
        return self.username


# 社区帖子 / 发布内容模型
class Post(models.Model):
    title = models.CharField(max_length=200)
    content = models.TextField()
    author = models.CharField(max_length=100)
    status = models.CharField(max_length=20, default='pending') # pending, approved, rejected
    reject_reason = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True) # 记录最后一次修改时间

# 历史足迹：记录每一次被覆盖掉的旧版本
class PostHistory(models.Model):
    # ForeignKey 建立一对多关系：一个帖子可以有多个历史记录
    post = models.ForeignKey(Post, on_delete=models.CASCADE, related_name='history_records')
    old_title = models.CharField(max_length=200)
    old_content = models.TextField()
    edited_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-edited_at'] # 最新的修改排在最前面

# 申请成为邻里达人
class ExpertApplication(models.Model):
    username = models.CharField(max_length=50)

    reason = models.TextField()  # 申请理由

    status = models.CharField(max_length=20, default='pending')     # pending / approved / rejected

    created_at = models.DateTimeField(auto_now_add=True)    #提交时间

    reviewed_at = models.DateTimeField(null=True, blank=True)  # 审核时间

    reject_reason = models.TextField(null=True, blank=True)  # 拒绝理由

# 邻里达人申请记录（闲置表 最后记得删）
class Application(models.Model):
    username = models.CharField(max_length=50)
    reason = models.TextField()
    status = models.CharField(max_length=20, default='pending')  # pending / approved / rejected
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.username

# 任务
# users/models.py

class Task(models.Model):
    # 任务分类常量
    CATEGORY_CHOICES = [
        ('errand', '跑腿代购'),
        ('repair', '家电维修'),
        ('pet', '宠物照顾'),
        ('other', '其他互助'),
    ]

    title = models.CharField(max_length=20, verbose_name="任务标题")
    category = models.CharField(max_length=20, choices=CATEGORY_CHOICES, default='other')
    content = models.TextField(max_length=1000, verbose_name="任务详情")

    # 关联发布人
    creator = models.ForeignKey(User, on_delete=models.CASCADE, related_name='created_tasks')
    # 关联接单人 (可以为空，因为刚发布时没人接)
    worker = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='accepted_tasks')

    # 状态：审核中(auditing)，招募中(pending), 已接单(accepted), 已完成(finished)
    status = models.CharField(max_length=20, default='auditing')

    # 🚀 新增：用于存放提交时的描述文字
    result_desc = models.TextField(null=True, blank=True, verbose_name="交付描述")

    # 🚀 新增：用于存放放弃任务时的原因
    abandon_reason = models.TextField(null=True, blank=True, verbose_name="放弃原因")

    created_at = models.DateTimeField(auto_now_add=True)

    # 🚀 新增：初审拒绝原因
    audit_reason = models.TextField(null=True, blank=True, verbose_name="审核评语")

    # 🚀 新增：复审/仲裁判定理由
    intervention_decision = models.TextField(null=True, blank=True, verbose_name="仲裁理由")

    def __str__(self):
        return self.title