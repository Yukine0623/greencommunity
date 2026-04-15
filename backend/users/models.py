from django.db import models

# 用户模型
class User(models.Model):
    username = models.CharField(max_length=50, unique=True)  # 用户名唯一
    password = models.CharField(max_length=128)  # 可以存明文，生产环境建议哈希
    role = models.CharField(max_length=20, default='user')  # 用户角色：user / admin / 邻里达人
    is_expert = models.BooleanField(default=False, verbose_name="邻里达人资格")
    is_provider = models.BooleanField(default=False, verbose_name="认证服务者资格")
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


class Announcement(models.Model):
    title = models.CharField(max_length=100)
    content = models.TextField()
    author = models.CharField(max_length=50)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']


class ChatMessage(models.Model):
    task = models.ForeignKey('Task', on_delete=models.CASCADE, related_name='chat_messages', null=True, blank=True)
    sender = models.CharField(max_length=50)
    content = models.TextField(max_length=500)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['id']

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
    APPLY_TYPE_CHOICES = [
        ('expert', '邻里达人'),
        ('provider', '认证服务者'),
    ]

    username = models.CharField(max_length=50)
    apply_type = models.CharField(max_length=20, choices=APPLY_TYPE_CHOICES, default='expert')

    reason = models.TextField()  # 申请理由
    service_scope = models.CharField(max_length=100, null=True, blank=True, verbose_name='服务范围')
    pricing_note = models.CharField(max_length=120, null=True, blank=True, verbose_name='定价参考')

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
    CATEGORY_CHOICES = [
        ('errand', '跑腿代购'),
        ('repair', '家电维修'),
        ('pet', '宠物照顾'),
        ('other', '其他互助'),
    ]

    # 1. 基础信息
    title = models.CharField(max_length=50, verbose_name="任务标题")  # 长度建议给 50
    category = models.CharField(max_length=20, choices=CATEGORY_CHOICES, default='other')
    content = models.TextField(max_length=1000, verbose_name="任务详情")

    # 2. 🚀 积分悬赏：发布时扣除/预留多少分
    reward_points = models.IntegerField(default=0, verbose_name="悬赏积分")
    community_zone = models.CharField(max_length=50, null=True, blank=True, verbose_name="社区片区")
    latitude = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True, verbose_name="纬度")
    longitude = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True, verbose_name="经度")

    # 3. 关联角色
    creator = models.ForeignKey(User, on_delete=models.CASCADE, related_name='created_tasks')
    worker = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='accepted_tasks')

    # 4. 状态机：建议在注释里写全所有状态，方便以后维护
    # auditing: 待审核
    # rejected: 审核未通过 (初审拒绝)
    # pending: 招募中 (审核通过)
    # accepted: 进行中 (达人已接单)
    # submitted: 已完成提交 (待用户确认)
    # intervention: 争议介入 (用户不满意请求仲裁)
    # finished: 已圆满完成 (归档)
    status = models.CharField(max_length=40, default='auditing')

    # 5. 流程描述字段
    result_desc = models.TextField(null=True, blank=True, verbose_name="达人提交成果描述")
    abandon_reason = models.TextField(null=True, blank=True, verbose_name="放弃/取消原因")

    # 6. 🚀 审批与历史记录的核心
    audit_reason = models.TextField(null=True, blank=True, verbose_name="管理员审核/拒绝理由")
    intervention_decision = models.TextField(null=True, blank=True, verbose_name="仲裁判定判定依据")
    terminate_requested_by = models.CharField(max_length=50, null=True, blank=True, verbose_name="终止申请发起人")
    terminate_reason = models.TextField(null=True, blank=True, verbose_name="终止申请原因")
    terminate_agreed_by = models.CharField(max_length=50, null=True, blank=True, verbose_name="终止申请同意人")
    terminate_reject_reason = models.TextField(null=True, blank=True, verbose_name="终止申请拒绝/驳回原因")
    terminate_creator_points = models.IntegerField(null=True, blank=True, verbose_name="终止结算发单方积分")
    terminate_worker_points = models.IntegerField(null=True, blank=True, verbose_name="终止结算接单方积分")

    # 7. 时间戳
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="创建时间")
    accepted_at = models.DateTimeField(null=True, blank=True, verbose_name="接单时间")
    submitted_at = models.DateTimeField(null=True, blank=True, verbose_name="提交成果时间")
    terminated_at = models.DateTimeField(null=True, blank=True, verbose_name="终止时间")
    # 🚀 增加这个字段：每次 save() 时自动更新，用于记录“处理时间”
    updated_at = models.DateTimeField(auto_now=True, verbose_name="最后更新时间")

    def __str__(self):
        return self.title



class CommunityTask(models.Model):
    TASK_TYPE = (
        ('MUTUAL', '邻里互助'),
        ('PRO', '专业报修'),
    )

    title = models.CharField(max_length=200)
    description = models.TextField()
    task_type = models.CharField(max_length=10, choices=TASK_TYPE)

    # 模糊位置：存储经纬度，但在前端展示时只显示“XX社区”或模糊半径
    latitude = models.DecimalField(max_digits=9, decimal_places=6)
    longitude = models.DecimalField(max_digits=9, decimal_places=6)

    budget = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    publisher = models.ForeignKey('User', on_delete=models.CASCADE, related_name='published_tasks')

    # 状态控制
    is_completed = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

#积分流水
class PointTransaction(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    change = models.IntegerField()  # 正数加积分，负数减积分
    reason = models.CharField(max_length=255)  # 比如：“发布任务-代买咖啡”、“完成任务-修理水龙头”
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']
