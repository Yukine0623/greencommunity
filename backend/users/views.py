from django.db.models import Q, Count, Avg
from django.views.decorators.csrf import csrf_exempt
from django.http import JsonResponse, HttpResponse
from .models import User, Post, ExpertApplication, PostHistory, Task, PointTransaction, Announcement, ChatMessage, TaskQuote, TaskReview, AuditLog, BlacklistAppeal
from django.utils.timezone import now
from datetime import timedelta
from math import radians, cos, sin, asin, sqrt
from .models import CommunityTask
from django.db import transaction
from django.db.models import F
from django.http import JsonResponse
from django.views.decorators.http import require_POST
#from .models import Task, PointTransaction, User
import json
import csv


AUTO_ACCEPT_MINUTES = 5

TERMINATION_SETTLEMENT_STATUSES = {'finished', 'terminated'}
SENSITIVE_KEYWORDS = ['诈骗', '刷单', '赌博', '涉黄', '代开发票', '买卖证件']
PROVIDER_SERVICE_DIRECTIONS = {
    '家电维修', '管道疏通', '电路检修', '搬运服务', '保洁服务', '家居安装', '上门做饭', '宠物照护'
}
PROVIDER_SERVICE_TIME_BLOCKS = {'0:00-8:00', '8:00-13:00', '13:00-18:00', '18:00-24:00'}


def parse_multi_tags(value):
    if isinstance(value, list):
        raw = value
    else:
        raw = str(value or '').split(',')
    cleaned = []
    for item in raw:
        text = str(item or '').strip()
        if text and text not in cleaned:
            cleaned.append(text)
    return cleaned


def parse_price_range(raw_value):
    text = str(raw_value or '').strip()
    if not text:
        return None, None
    normalized = text.replace('元', '').replace(' ', '')
    if '-' not in normalized:
        return None, None
    parts = normalized.split('-', 1)
    if len(parts) != 2:
        return None, None
    left, right = parts[0].strip(), parts[1].strip()
    if not left.isdigit() or not right.isdigit():
        return None, None
    low = int(left)
    high = int(right)
    if low > high:
        low, high = high, low
    return low, high


def serialize_price_range(low, high):
    if low is None or high is None:
        return None
    return f'{low}-{high}'


def detect_sensitive_keywords(*texts):
    joined = ' '.join([(t or '') for t in texts]).lower()
    hits = []
    for keyword in SENSITIVE_KEYWORDS:
        if keyword.lower() in joined:
            hits.append(keyword)
    return hits


def is_user_blacklisted(user):
    if not user:
        return False
    if not user.is_blacklisted:
        return False
    if user.blacklist_until and user.blacklist_until < now():
        user.is_blacklisted = False
        user.blacklist_reason = None
        user.blacklist_until = None
        user.save(update_fields=['is_blacklisted', 'blacklist_reason', 'blacklist_until'])
        return False
    return True


def log_audit(action, actor=None, target_type=None, target_id=None, detail=None):
    AuditLog.objects.create(
        actor=actor,
        action=action,
        target_type=target_type,
        target_id=str(target_id) if target_id is not None else None,
        detail=detail
    )


def can_user_manage_task(user, task):
    return task.creator_id == user.id and task.status in {'auditing', 'pending', 'rejected'}


def can_user_request_termination(username, task):
    if task.status != 'accepted':
        return False
    if task.creator.username == username:
        return True
    return bool(task.worker and task.worker.username == username)


def normalize_user_role_flags(user):
    """
    兼容历史单角色数据：
    - role=expert/provider => 转为 resident + 资格标记
    - role=user => resident
    """
    changed_fields = []
    role = user.role
    if role == 'expert':
        if not user.is_expert:
            user.is_expert = True
            changed_fields.append('is_expert')
        user.role = 'resident'
        changed_fields.append('role')
    elif role == 'provider':
        if not user.is_provider:
            user.is_provider = True
            changed_fields.append('is_provider')
        user.role = 'resident'
        changed_fields.append('role')
    elif role == 'user':
        user.role = 'resident'
        changed_fields.append('role')

    if changed_fields:
        user.save(update_fields=list(dict.fromkeys(changed_fields)))


def auto_finish_overdue_submitted_tasks():
    """自动验收：submitted 超过 5 分钟未处理则自动完成并发放积分。"""
    cutoff = now() - timedelta(minutes=AUTO_ACCEPT_MINUTES)
    overdue_ids = list(
        Task.objects.filter(
            status='submitted',
            worker__isnull=False,
            submitted_at__isnull=False,
            submitted_at__lte=cutoff
        ).values_list('id', flat=True)[:200]
    )
    for task_id in overdue_ids:
        try:
            with transaction.atomic():
                task = Task.objects.select_for_update().select_related('worker').get(id=task_id)
                if task.status != 'submitted' or not task.worker:
                    continue
                if not task.submitted_at or task.submitted_at > cutoff:
                    continue

                worker = task.worker
                worker.points = F('points') + task.reward_points
                worker.save(update_fields=['points'])

                PointTransaction.objects.create(
                    user=worker,
                    change=task.reward_points,
                    reason=f'任务超时自动验收发放积分：{task.title}'
                )

                task.status = 'finished'
                task.settlement_points = task.reward_points
                task.refund_points = 0
                task.save(update_fields=['status', 'settlement_points', 'refund_points', 'updated_at'])
                log_audit(
                    action='auto_finish_task',
                    actor=None,
                    target_type='task',
                    target_id=task.id,
                    detail=f'自动验收并发放积分 {task.reward_points}'
                )
        except Task.DoesNotExist:
            continue


# 登录接口
@csrf_exempt
def login(request):
    if request.method != 'POST':
        return JsonResponse({'code': 405, 'message': '只支持POST'})

    try:
        data = json.loads(request.body)
        username = data.get('username')
        password = data.get('password')
    except:
        return JsonResponse({'code': 400, 'message': '数据格式错误'})

    try:
        user = User.objects.get(username=username)
        normalize_user_role_flags(user)

        if user.password != password:
            return JsonResponse({'code': 401, 'message': '密码错误'})

        # 🔥 关键：返回 role
        return JsonResponse({
            'code': 200,
            'message': '登录成功',
            'role': user.role,   # 返回用户身份
            'points': user.points, # 返回当前用户积分
            'is_expert': user.is_expert,
            'is_provider': user.is_provider,
            'is_blacklisted': user.is_blacklisted
        })

    except User.DoesNotExist:
        return JsonResponse({'code': 404, 'message': '用户不存在'})
# 注册接口
@csrf_exempt
def register(request):
    if request.method == 'POST':
        data = json.loads(request.body)

        username = data.get('username')
        password = data.get('password')

        # 判断用户是否已存在
        if User.objects.filter(username=username).exists():
            return JsonResponse({
                'code': 400,
                'message': '用户已存在'
            })

        # 创建用户
        User.objects.create(
            username=username,
            password=password,
            role='resident'
        )

        return JsonResponse({
            'code': 200,
            'message': '注册成功'
        })

    return JsonResponse({'code': 405, 'message': '只支持POST'})

# 返回所有注册用户信息
@csrf_exempt
def user_list(request):
    if request.method == 'GET':
        users = User.objects.all()
        user_data = []
        for user in users:
            normalize_user_role_flags(user)
            user_data.append({
                'id': user.id,
                'username': user.username,
                'role': user.role,
                'is_expert': user.is_expert,
                'is_provider': user.is_provider,
                'phone': user.phone,
                'points': user.points,
                'is_blacklisted': user.is_blacklisted,
                'blacklist_reason': user.blacklist_reason,
                'blacklist_until': user.blacklist_until.strftime('%Y-%m-%d %H:%M:%S') if user.blacklist_until else None,
                'created_at': user.created_at.strftime('%Y-%m-%d %H:%M:%S')
            })
        return JsonResponse({'code': 200, 'users': user_data})

    return JsonResponse({'code': 405, 'message': '只支持GET'})

# 发帖接口
@csrf_exempt
def create_post(request):
    if request.method == 'POST':
        data = json.loads(request.body)

        title = data.get('title')
        content = data.get('content')
        author = data.get('author')
        status = data.get('status')

        Post.objects.create(
            title=title,
            content=content,
            author=author,
            status='pending'
        )

        return JsonResponse({
            'code': 200,
            'message': '提交成功，等待管理员审核。'
        })

    return JsonResponse({'code': 405, 'message': '只支持POST'})

# 获取帖子列表（支持关键词搜索和 Tab 过滤）
@csrf_exempt
def get_posts(request):
    username = request.GET.get('username')

    # 核心逻辑：
    # 首页显示：所有状态为 'approved' 的帖子
    # 我的帖子：作者是 '我' 的所有帖子（不管什么状态）
    posts_query = Post.objects.filter(
        Q(status='approved') | Q(author=username)
    ).order_by('-created_at')

    res_list = []
    for p in posts_query:
        res_list.append({
            'id': p.id,
            'title': p.title,
            'content': p.content,
            'author': p.author,
            'status': p.status,
            'reject_reason': p.reject_reason,
            'created_at': p.created_at.strftime('%Y-%m-%d %H:%M')
        })
    return JsonResponse({'posts': res_list})


@csrf_exempt
def get_announcements(request):
    if request.method != 'GET':
        return JsonResponse({'code': 405, 'message': '只支持GET'})

    announcements = Announcement.objects.all()
    data = []
    for item in announcements:
        data.append({
            'id': item.id,
            'title': item.title,
            'content': item.content,
            'author': item.author,
            'created_at': item.created_at.strftime('%Y-%m-%d %H:%M')
        })

    return JsonResponse({'code': 200, 'announcements': data})


@csrf_exempt
def create_announcement(request):
    if request.method != 'POST':
        return JsonResponse({'code': 405, 'message': '只支持POST'})

    try:
        data = json.loads(request.body)
        username = data.get('username')
        title = data.get('title')
        content = data.get('content')
    except Exception:
        return JsonResponse({'code': 400, 'message': '请求数据格式错误'})

    if not username or not title or not content:
        return JsonResponse({'code': 400, 'message': '参数不完整'})

    user = User.objects.filter(username=username).first()
    if not user:
        return JsonResponse({'code': 404, 'message': '用户不存在'})
    if is_user_blacklisted(user):
        return JsonResponse({'code': 403, 'message': '你已被限制发布任务，请先申诉或联系管理员'})

    if user.role != 'admin':
        return JsonResponse({'code': 403, 'message': '只有管理员可以发布公告'})

    Announcement.objects.create(
        title=title.strip(),
        content=content.strip(),
        author=username
    )
    return JsonResponse({'code': 200, 'message': '公告发布成功'})


@csrf_exempt
def delete_announcement(request):
    if request.method != 'POST':
        return JsonResponse({'code': 405, 'message': '只支持POST'})

    try:
        data = json.loads(request.body)
        username = (data.get('username') or '').strip()
        announcement_id = data.get('id')
    except Exception:
        return JsonResponse({'code': 400, 'message': '请求数据格式错误'})

    if not username or not announcement_id:
        return JsonResponse({'code': 400, 'message': '参数不完整'})

    user = User.objects.filter(username=username).first()
    if not user or user.role != 'admin':
        return JsonResponse({'code': 403, 'message': '只有管理员可以删除公告'})

    announcement = Announcement.objects.filter(id=announcement_id).first()
    if not announcement:
        return JsonResponse({'code': 404, 'message': '公告不存在'})

    announcement.delete()
    return JsonResponse({'code': 200, 'message': '公告已删除'})


@csrf_exempt
def get_chat_messages(request):
    if request.method != 'GET':
        return JsonResponse({'code': 405, 'message': '只支持GET'})

    username = (request.GET.get('username') or '').strip()
    task_id = request.GET.get('task_id')
    if not username or not task_id:
        return JsonResponse({'code': 400, 'message': '缺少必要参数'})

    try:
        task = Task.objects.get(id=task_id)
    except Task.DoesNotExist:
        return JsonResponse({'code': 404, 'message': '任务不存在'})

    is_creator = task.creator.username == username
    is_worker = task.worker and task.worker.username == username
    if not (is_creator or is_worker):
        return JsonResponse({'code': 403, 'message': '你没有查看该任务聊天的权限'})

    try:
        after_id = int(request.GET.get('after_id', 0))
    except ValueError:
        after_id = 0

    try:
        limit = int(request.GET.get('limit', 50))
    except ValueError:
        limit = 50

    limit = max(1, min(limit, 200))

    queryset = ChatMessage.objects.filter(task=task, id__gt=after_id).order_by('id')[:limit]
    data = []
    for msg in queryset:
        data.append({
            'id': msg.id,
            'sender': msg.sender,
            'content': msg.content,
            'created_at': msg.created_at.strftime('%Y-%m-%d %H:%M:%S')
        })

    return JsonResponse({'code': 200, 'messages': data})


@csrf_exempt
def send_chat_message(request):
    if request.method != 'POST':
        return JsonResponse({'code': 405, 'message': '只支持POST'})

    try:
        data = json.loads(request.body)
        username = (data.get('username') or '').strip()
        task_id = data.get('task_id')
        content = (data.get('content') or '').strip()
    except Exception:
        return JsonResponse({'code': 400, 'message': '请求数据格式错误'})

    if not username:
        return JsonResponse({'code': 400, 'message': '缺少用户名'})
    if not task_id:
        return JsonResponse({'code': 400, 'message': '缺少任务ID'})
    if not content:
        return JsonResponse({'code': 400, 'message': '消息不能为空'})
    if len(content) > 500:
        return JsonResponse({'code': 400, 'message': '消息长度不能超过500字'})

    sender_user = User.objects.filter(username=username).first()
    if not sender_user:
        return JsonResponse({'code': 404, 'message': '用户不存在'})
    if is_user_blacklisted(sender_user):
        return JsonResponse({'code': 403, 'message': '你已被限制发言，请先申诉或联系管理员'})

    try:
        task = Task.objects.get(id=task_id)
    except Task.DoesNotExist:
        return JsonResponse({'code': 404, 'message': '任务不存在'})

    is_creator = task.creator.username == username
    is_worker = task.worker and task.worker.username == username
    if not (is_creator or is_worker):
        return JsonResponse({'code': 403, 'message': '你没有发送该任务聊天消息的权限'})

    if not task.worker:
        return JsonResponse({'code': 400, 'message': '任务尚未接单，暂不能聊天'})

    if task.status in TERMINATION_SETTLEMENT_STATUSES:
        return JsonResponse({'code': 400, 'message': '任务已结束，聊天已关闭'})

    msg = ChatMessage.objects.create(
        task=task,
        sender=username,
        content=content
    )
    log_audit(
        action='send_chat_message',
        actor=sender_user,
        target_type='task',
        target_id=task.id,
        detail='发送任务聊天消息'
    )

    return JsonResponse({
        'code': 200,
        'message': '发送成功',
        'data': {
            'id': msg.id,
            'sender': msg.sender,
            'content': msg.content,
            'created_at': msg.created_at.strftime('%Y-%m-%d %H:%M:%S')
        }
    })

# 获取指定帖子的历史修改记录
def get_post_history(request):
    post_id = request.GET.get('id')
    # 查找该帖子关联的所有历史记录，按时间倒序
    records = PostHistory.objects.filter(post_id=post_id).order_by('-edited_at')

    history_data = []
    for r in records:
        history_data.append({
            'old_title': r.old_title,
            'old_content': r.old_content,
            'edited_at': r.edited_at.strftime('%Y-%m-%d %H:%M')
        })
    return JsonResponse({'history': history_data})

#接受前段发来的新帖
@csrf_exempt
def create_post(request):
    if request.method == 'POST':
        data = json.loads(request.body)
        author_name = data.get('author')
        author = User.objects.filter(username=author_name).first()
        if author and is_user_blacklisted(author):
            return JsonResponse({'code': 403, 'message': '你已被限制发帖，请先申诉或联系管理员'})

        hits = detect_sensitive_keywords(data.get('title'), data.get('content'))
        Post.objects.create(
            title=data.get('title'),
            content=data.get('content'),
            author=author_name,
            status='pending', # 初始状态必须是待审核
            risk_flagged=bool(hits),
            risk_keywords=','.join(hits) if hits else None
        )
        if author:
            log_audit(
                action='create_post',
                actor=author,
                target_type='post',
                detail=f'创建帖子，关键词命中: {",".join(hits) if hits else "无"}'
            )
        if hits:
            return JsonResponse({'code': 200, 'message': '内容已提交，检测到敏感词，已进入人工复核队列'})
        return JsonResponse({'code': 200, 'message': '发布成功，请等待管理员审核'})

#修改被拒绝的帖子
@csrf_exempt
def update_post(request):
    if request.method == 'POST':
        data = json.loads(request.body)
        try:
            post = Post.objects.get(id=data.get('id'))

            # 🚀 核心逻辑：先存档，再更新
            PostHistory.objects.create(
                post=post,
                old_title=post.title,
                old_content=post.content
            )

            # 更新主表
            post.title = data.get('title')
            post.content = data.get('content')
            post.status = 'pending'  # 修改后必须重新审核
            post.save()

            return JsonResponse({'code': 200, 'message': '修改成功，已重新进入审核队列'})
        except Post.DoesNotExist:
            return JsonResponse({'code': 404, 'message': '帖子不存在'})

# 获取我的帖子
def my_posts(request):
    data = json.loads(request.body)
    username = data.get('username')

    posts = Post.objects.filter(author=username).order_by('-created_at')

    return JsonResponse({'posts': list(posts.values())})


# users/views.py
# 管理员获取全社区所有待审核的帖子
@csrf_exempt
def all_pending_posts(request):
    # 查找数据库中所有状态为 'pending' 的帖子
    posts = Post.objects.filter(status='pending').order_by('-created_at')

    data = []
    for p in posts:
        data.append({
            'id': p.id,
            'title': p.title,
            'content': p.content,
            'author': p.author,
            'created_at': p.created_at.strftime('%Y-%m-%d %H:%M')
        })
    return JsonResponse({'posts': data})

# 管理员审核帖子的接口（通过或拒绝）
@csrf_exempt
def review_post(request):
    if request.method == 'POST':
        import json
        data = json.loads(request.body)
        post_id = data.get('id')
        action = data.get('action')  # 'approve' 或 'reject'
        reason = data.get('reason', '')  # 拒绝理由

        try:
            post = Post.objects.get(id=post_id)
            if action == 'approve':
                post.status = 'approved'
            else:
                post.status = 'rejected'
                post.reject_reason = reason
            post.save()
            return JsonResponse({'code': 200, 'message': '操作成功'})
        except Post.DoesNotExist:
            return JsonResponse({'code': 404, 'message': '帖子不存在'})

# 用户修改后重新提交
@csrf_exempt
def update_post(request):
    data = json.loads(request.body)

    post = Post.objects.get(id=data.get('id'))
    author = User.objects.filter(username=post.author).first()
    if author and is_user_blacklisted(author):
        return JsonResponse({'code': 403, 'message': '你已被限制发帖，请先申诉或联系管理员'})

    post.title = data.get('title')
    post.content = data.get('content')
    post.status = 'pending'
    post.reject_reason = None
    hits = detect_sensitive_keywords(post.title, post.content)
    post.risk_flagged = bool(hits)
    post.risk_keywords = ','.join(hits) if hits else None

    post.save()
    if author:
        log_audit(
            action='update_post',
            actor=author,
            target_type='post',
            target_id=post.id,
            detail=f'修改帖子，关键词命中: {",".join(hits) if hits else "无"}'
        )

    if hits:
        return JsonResponse({'code': 200, 'message': '已重新提交，检测到敏感词，等待人工复核'})
    return JsonResponse({'code': 200, 'message': '已重新提交审核'})


# users/views.py

def get_audit_history(request):
    """获取所有已处理（通过/拒绝）的帖子"""
    # 过滤掉 pending 状态，按更新时间排序（最新的处理排前面）
    posts = Post.objects.filter(status__in=['approved', 'rejected','finished']).order_by('-updated_at')

    data = []
    for p in posts:
        data.append({
            'id': p.id,
            'title': p.title,
            'author': p.author,
            'status': p.status,
            'content': p.content,
            'reject_reason': p.reject_reason or '--',
            'processed_at': p.updated_at.strftime('%Y-%m-%d %H:%M')
        })
    return JsonResponse({'history': data})

# 邻里达人申请接口
@csrf_exempt
def apply_expert(request):
    if request.method == 'POST':
        # 请求必须是json格式
        try:
            data = json.loads(request.body)
        except:
            return JsonResponse({
                'code': 400,
                'message': '请求数据格式错误'
            })

        username = data.get('username')
        reason = (data.get('reason') or '').strip()
        apply_type = (data.get('apply_type') or 'expert').strip()
        service_scope = (data.get('service_scope') or '').strip()
        pricing_note = (data.get('pricing_note') or '').strip()
        provider_service_directions = parse_multi_tags(data.get('provider_service_directions'))
        provider_service_times = parse_multi_tags(data.get('provider_service_times'))
        provider_price_min = data.get('provider_price_min')
        provider_price_max = data.get('provider_price_max')
        provider_intro = (data.get('provider_intro') or '').strip()

        # 参数校验
        if apply_type not in {'expert', 'provider'}:
            return JsonResponse({'code': 400, 'message': '申请类型不正确'})
        if not username or not reason:
            return JsonResponse({
                'code': 400,
                'message': '参数不完整'
            })
        if apply_type == 'provider' and not service_scope:
            return JsonResponse({'code': 400, 'message': '认证服务者请填写服务范围'})
        if apply_type == 'provider':
            if not provider_service_directions:
                return JsonResponse({'code': 400, 'message': '认证服务者请至少选择一个服务方向'})
            if not provider_service_times:
                return JsonResponse({'code': 400, 'message': '认证服务者请至少选择一个服务时间'})
            invalid_directions = [x for x in provider_service_directions if x not in PROVIDER_SERVICE_DIRECTIONS]
            invalid_times = [x for x in provider_service_times if x not in PROVIDER_SERVICE_TIME_BLOCKS]
            if invalid_directions or invalid_times:
                return JsonResponse({'code': 400, 'message': '服务方向或服务时间标签不合法'})
            min_price = None
            max_price = None
            if provider_price_min not in (None, '') or provider_price_max not in (None, ''):
                if str(provider_price_min).strip().isdigit() and str(provider_price_max).strip().isdigit():
                    min_price = int(provider_price_min)
                    max_price = int(provider_price_max)
                    if min_price > max_price:
                        min_price, max_price = max_price, min_price
                else:
                    return JsonResponse({'code': 400, 'message': '价格区间只允许填写数字'})
            provider_price_range = serialize_price_range(min_price, max_price)
        else:
            provider_price_range = None

        # 用户是否存在
        try:
            user = User.objects.get(username=username)
            normalize_user_role_flags(user)
        except User.DoesNotExist:
            return JsonResponse({
                'code': 400,
                'message': '用户不存在'
            })

        has_qualification = user.is_expert if apply_type == 'expert' else user.is_provider
        if has_qualification:
            role_name = '邻里达人' if apply_type == 'expert' else '认证服务者'
            return JsonResponse({'code': 400, 'message': f'你已经是{role_name}，无需重复申请'})

        # 是否已有未处理申请
        if ExpertApplication.objects.filter(username=username, apply_type=apply_type, status='pending').exists():
            return JsonResponse({
                'code': 400,
                'message': '你已经提交过申请，请等待审核'
            })

        # 创建申请
        ExpertApplication.objects.create(
            username=username,
            apply_type=apply_type,
            reason=reason,
            service_scope=service_scope or None,
            pricing_note=pricing_note or None,
            provider_service_directions=','.join(provider_service_directions) if provider_service_directions else None,
            provider_service_times=','.join(provider_service_times) if provider_service_times else None,
            provider_price_range=provider_price_range,
            provider_intro=provider_intro or None,
            status='pending'   # 明确写一下（更规范）
        )

        return JsonResponse({
            'code': 200,
            'message': '申请已提交，等待审核'
        })

    return JsonResponse({
        'code': 405,
        'message': '只支持POST请求'
    })

#用户查询邻里达人申请状态
@csrf_exempt
def get_my_application(request):
    if request.method != 'POST':
        return JsonResponse({'code': 405, 'message': '只支持POST'})

    try:
        data = json.loads(request.body)
        username = data.get('username')
        apply_type = (data.get('apply_type') or 'expert').strip()
        if apply_type not in {'expert', 'provider'}:
            return JsonResponse({'code': 400, 'message': '申请类型不正确'})

        app = ExpertApplication.objects.filter(
            username=username,
            apply_type=apply_type
        ).order_by('-created_at').first()   #-created_at按时间倒序   .first取最新一条

        if not app:
            return JsonResponse({
                'code': 200,
                'status': 'none'   # 👈 没申请
            })

        return JsonResponse({
            'code': 200,
            'apply_type': apply_type,
            'status': app.status,
            'reason': app.reason,
            'service_scope': app.service_scope,
            'pricing_note': app.pricing_note,
            'provider_service_directions': parse_multi_tags(app.provider_service_directions),
            'provider_service_times': parse_multi_tags(app.provider_service_times),
            'provider_price_range': app.provider_price_range,
            'provider_price_min': parse_price_range(app.provider_price_range)[0],
            'provider_price_max': parse_price_range(app.provider_price_range)[1],
            'provider_intro': app.provider_intro
        })

    except Exception as e:
        print(e)
        return JsonResponse({'code': 500, 'message': '服务器错误'})

#管理员审核接口
#通过
@csrf_exempt
def approve_expert(request):
    if request.method != 'POST':
        return JsonResponse({'code': 405, 'message': '只支持POST'})

    try:
        data = json.loads(request.body)
        app_id = data.get('id')
        username = data.get('username')
        apply_type = (data.get('apply_type') or '').strip()

        # 找到待审核申请
        if app_id:
            app = ExpertApplication.objects.filter(id=app_id, status='pending').first()
        else:
            if not username:
                return JsonResponse({'code': 400, 'message': '缺少用户名'})
            filters = {'username': username, 'status': 'pending'}
            if apply_type in {'expert', 'provider'}:
                filters['apply_type'] = apply_type
            app = ExpertApplication.objects.filter(**filters).order_by('-created_at').first()

        if not app:
            return JsonResponse({'code': 404, 'message': '申请不存在或已处理'})

        # ✅ 修改申请状态
        app.status = 'approved'
        app.reviewed_at = now()
        app.save()

        # ✅ 同时把用户角色改成 expert
        user = User.objects.filter(username=app.username).first()
        if user:
            normalize_user_role_flags(user)
            if app.apply_type == 'expert':
                user.is_expert = True
                user.save(update_fields=['is_expert'])
            else:
                user.is_provider = True
                user.save(update_fields=['is_provider'])

        return JsonResponse({'code': 200, 'message': '审核通过'})

    except Exception as e:
        print(e)
        return JsonResponse({'code': 500, 'message': '服务器错误'})

#拒绝
@csrf_exempt
def reject_expert(request):
    if request.method != 'POST':
        return JsonResponse({'code': 405, 'message': '只支持POST'})

    try:
        data = json.loads(request.body)
        app_id = data.get('id')
        username = data.get('username')
        apply_type = (data.get('apply_type') or '').strip()
        reason = data.get('reason')

        # 找到待审核申请
        if app_id:
            app = ExpertApplication.objects.filter(id=app_id, status='pending').first()
        else:
            if not username:
                return JsonResponse({'code': 400, 'message': '缺少用户名'})
            filters = {'username': username, 'status': 'pending'}
            if apply_type in {'expert', 'provider'}:
                filters['apply_type'] = apply_type
            app = ExpertApplication.objects.filter(**filters).order_by('-created_at').first()

        if not app:
            return JsonResponse({'code': 404, 'message': '申请不存在或已处理'})

        # 修改状态为拒绝
        app.status = 'rejected'
        app.reviewed_at = now()  # ⭐ 审核时间
        app.reject_reason = reason
        app.save()

        return JsonResponse({'code': 200, 'message': '已拒绝该申请'})

    except Exception as e:
        print(e)
        return JsonResponse({'code': 500, 'message': '服务器错误'})

# 获取申请列表
@csrf_exempt
def application_list(request):
    if request.method != 'GET':
        return JsonResponse({'code': 405, 'message': '只支持GET'})

    applications = ExpertApplication.objects.all().order_by('-created_at')

    result = []
    for item in applications:
        result.append({
            'id': item.id,
            'username': item.username,
            'apply_type': item.apply_type,
            'reason': item.reason,
            'service_scope': item.service_scope,
            'pricing_note': item.pricing_note,
            'provider_service_directions': parse_multi_tags(item.provider_service_directions),
            'provider_service_times': parse_multi_tags(item.provider_service_times),
            'provider_price_range': item.provider_price_range,
            'provider_price_min': parse_price_range(item.provider_price_range)[0],
            'provider_price_max': parse_price_range(item.provider_price_range)[1],
            'provider_intro': item.provider_intro,
            'status': item.status,
            'created_at': item.created_at.strftime('%Y-%m-%d %H:%M:%S')
        })

    return JsonResponse({
        'code': 200,
        'data': result
    })

# 获取当前用户role
@csrf_exempt
def get_user_info(request):
    if request.method != 'POST':
        return JsonResponse({'code': 405, 'message': '只支持POST'})

    try:
        data = json.loads(request.body)
        username = data.get('username')

        user = User.objects.filter(username=username).first()

        if not user:
            return JsonResponse({'code': 404, 'message': '用户不存在'})
        normalize_user_role_flags(user)

        return JsonResponse({
            'code': 200,
            'username': user.username,
            'role': user.role,
            'points': user.points,
            'is_expert': user.is_expert,
            'is_provider': user.is_provider,
            'is_blacklisted': user.is_blacklisted,
            'blacklist_reason': user.blacklist_reason,
            'blacklist_until': user.blacklist_until.strftime('%Y-%m-%d %H:%M:%S') if user.blacklist_until else None
        })

    except Exception as e:
        print(e)
        return JsonResponse({'code': 500, 'message': '服务器错误'})

# 获取历史用户信息
@csrf_exempt
def my_application_history(request):
    if request.method != 'POST':
        return JsonResponse({'code': 405, 'message': '只支持POST'})

    data = json.loads(request.body)
    username = data.get('username')
    apply_type = (data.get('apply_type') or '').strip()

    filters = {'username': username}
    if apply_type in {'expert', 'provider'}:
        filters['apply_type'] = apply_type
    apps = ExpertApplication.objects.filter(**filters).order_by('-created_at')

    result = []
    for item in apps:
        result.append({
            'id': item.id,
            'apply_type': item.apply_type,
            'status': item.status,
            'reason': item.reason,
            'service_scope': item.service_scope,
            'pricing_note': item.pricing_note,
            'provider_service_directions': parse_multi_tags(item.provider_service_directions),
            'provider_service_times': parse_multi_tags(item.provider_service_times),
            'provider_price_range': item.provider_price_range,
            'provider_price_min': parse_price_range(item.provider_price_range)[0],
            'provider_price_max': parse_price_range(item.provider_price_range)[1],
            'provider_intro': item.provider_intro,
            'created_at': item.created_at.strftime('%Y-%m-%d %H:%M:%S'),
            'reviewed_at': item.reviewed_at.strftime('%Y-%m-%d %H:%M:%S') if item.reviewed_at else None,
            'reject_reason': item.reject_reason
        })

    return JsonResponse({
        'code': 200,
        'data': result
    })


@csrf_exempt
def my_point_transactions(request):
    if request.method != 'GET':
        return JsonResponse({'code': 405, 'message': '只支持GET'})

    username = (request.GET.get('username') or '').strip()
    if not username:
        return JsonResponse({'code': 400, 'message': '缺少用户名'})

    user = User.objects.filter(username=username).first()
    if not user:
        return JsonResponse({'code': 404, 'message': '用户不存在'})

    try:
        page = max(int(request.GET.get('page', 1)), 1)
    except Exception:
        page = 1
    try:
        page_size = int(request.GET.get('page_size', 10))
    except Exception:
        page_size = 10
    page_size = min(max(page_size, 1), 50)

    qs = PointTransaction.objects.filter(user=user).order_by('-created_at')
    total = qs.count()
    start = (page - 1) * page_size
    rows = qs[start:start + page_size]

    data = []
    for item in rows:
        data.append({
            'id': item.id,
            'change': item.change,
            'reason': item.reason,
            'created_at': item.created_at.strftime('%Y-%m-%d %H:%M:%S')
        })

    return JsonResponse({
        'code': 200,
        'data': data,
        'pagination': {
            'page': page,
            'page_size': page_size,
            'total': total,
            'total_pages': max((total + page_size - 1) // page_size, 1)
        }
    })


@csrf_exempt
def admin_point_transactions(request):
    if request.method != 'GET':
        return JsonResponse({'code': 405, 'message': '只支持GET'})

    admin_username = (request.GET.get('admin_username') or '').strip()
    keyword = (request.GET.get('keyword') or '').strip()
    admin = User.objects.filter(username=admin_username, role='admin').first()
    if not admin:
        return JsonResponse({'code': 403, 'message': '只有管理员可以查看积分流水'})

    try:
        page = max(int(request.GET.get('page', 1)), 1)
    except Exception:
        page = 1
    try:
        page_size = int(request.GET.get('page_size', 10))
    except Exception:
        page_size = 10
    page_size = min(max(page_size, 1), 100)

    qs = PointTransaction.objects.select_related('user').all().order_by('-created_at')
    if keyword:
        qs = qs.filter(Q(user__username__icontains=keyword) | Q(reason__icontains=keyword))

    total = qs.count()
    start = (page - 1) * page_size
    rows = qs[start:start + page_size]

    data = []
    for item in rows:
        data.append({
            'id': item.id,
            'username': item.user.username,
            'change': item.change,
            'reason': item.reason,
            'created_at': item.created_at.strftime('%Y-%m-%d %H:%M:%S')
        })

    return JsonResponse({
        'code': 200,
        'data': data,
        'pagination': {
            'page': page,
            'page_size': page_size,
            'total': total,
            'total_pages': max((total + page_size - 1) // page_size, 1)
        }
    })


@csrf_exempt
def export_admin_point_transactions_csv(request):
    if request.method != 'GET':
        return JsonResponse({'code': 405, 'message': '只支持GET'})

    admin_username = (request.GET.get('admin_username') or '').strip()
    keyword = (request.GET.get('keyword') or '').strip()
    admin = User.objects.filter(username=admin_username, role='admin').first()
    if not admin:
        return JsonResponse({'code': 403, 'message': '只有管理员可以导出积分流水'})

    qs = PointTransaction.objects.select_related('user').all().order_by('-created_at')
    if keyword:
        qs = qs.filter(Q(user__username__icontains=keyword) | Q(reason__icontains=keyword))

    response = HttpResponse(content_type='text/csv; charset=utf-8-sig')
    filename = f'point_transactions_{now().strftime("%Y%m%d_%H%M%S")}.csv'
    response['Content-Disposition'] = f'attachment; filename="{filename}"'

    writer = csv.writer(response)
    writer.writerow(['流水ID', '用户名', '积分变动', '变动原因', '时间'])
    for item in qs:
        writer.writerow([
            item.id,
            item.user.username,
            item.change,
            item.reason,
            item.created_at.strftime('%Y-%m-%d %H:%M:%S')
        ])

    log_audit(
        action='export_admin_point_transactions_csv',
        actor=admin,
        target_type='point_transaction',
        detail=f'关键词筛选: {keyword or "无"}'
    )
    return response


@csrf_exempt
def get_tasks(request):
    """获取所有待接单的任务"""
    category = request.GET.get('category')
    user_lat = request.GET.get('user_lat')
    user_lng = request.GET.get('user_lng')
    username = (request.GET.get('username') or '').strip()
    sort_mode = (request.GET.get('sort_mode') or '').strip()

    tasks = Task.objects.filter(status='pending').select_related('creator', 'invited_provider')
    if category and category != 'all':
        tasks = tasks.filter(category=category)

    tasks = tasks.order_by('-created_at')
    creator_stats = {}
    for row in Task.objects.values('creator_id').annotate(
        total=Count('id'),
        finished=Count('id', filter=Q(status='finished')),
        avg_accept=Avg(F('accepted_at') - F('created_at'))
    ):
        creator_stats[row['creator_id']] = {
            'total': row['total'] or 0,
            'finished': row['finished'] or 0,
            'avg_accept': row['avg_accept']
        }
    preferred_categories = set()
    if username:
        user = User.objects.filter(username=username).first()
        if user:
            for c in Task.objects.filter(worker=user, status='finished').values_list('category', flat=True):
                preferred_categories.add(c)

    task_list = []
    for t in tasks:
        # 定向邀约任务：只有发布者本人和被邀约认证服务者可见
        if t.invited_provider_id and username not in {t.creator.username, t.invited_provider.username}:
            continue
        distance_km = None
        if user_lat and user_lng and t.latitude is not None and t.longitude is not None:
            try:
                distance_km = round(haversine_distance(user_lat, user_lng, t.latitude, t.longitude), 2)
            except Exception:
                distance_km = None
        c_stat = creator_stats.get(t.creator_id, {'total': 0, 'finished': 0, 'avg_accept': None})
        completion_rate = 0
        if c_stat['total'] > 0:
            completion_rate = round((c_stat['finished'] / c_stat['total']) * 100, 2)
        # 响应速度（小时），越小越好；没有历史则置空
        response_hours = None
        if c_stat['avg_accept'] is not None:
            response_hours = round(c_stat['avg_accept'].total_seconds() / 3600, 2)

        score = 0.0
        if distance_km is not None:
            score += max(0, 40 - distance_km * 4)
        if preferred_categories and t.category in preferred_categories:
            score += 20
        score += min(25, completion_rate * 0.25)
        if response_hours is not None:
            score += max(0, 15 - response_hours)
        score += min(10, (t.reward_points or 0) / 10)

        task_list.append({
            'id': t.id,
            'title': t.title,
            'category': t.category,
            'content': t.content,
            'reward_points': t.reward_points,
            'assignee_type': t.assignee_type or 'any',
            'invited_provider': t.invited_provider.username if t.invited_provider else None,
            'community_zone': t.community_zone,
            'distance_km': distance_km,
            'creator_completion_rate': completion_rate,
            'creator_response_hours': response_hours,
            'recommend_score': round(score, 2),
            'creator': t.creator.username,
            'created_at': t.created_at.strftime('%Y-%m-%d %H:%M')
        })

    if sort_mode == 'smart':
        task_list.sort(key=lambda x: x.get('recommend_score', 0), reverse=True)
    elif user_lat and user_lng:
        # 有距离信息的任务优先，按距离升序；无距离的排后面
        task_list.sort(key=lambda x: (x['distance_km'] is None, x['distance_km'] if x['distance_km'] is not None else 999999))

    return JsonResponse({'code': 200, 'tasks': task_list})


# backend/users/views.py

# backend/users/views.py

@csrf_exempt
def create_task(request):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)

            # 1. 🚀 修复 500 报错的关键：从 localStorage/前端传来的 username 找人
            # 不要相信 user_id，因为前端可能没存 ID，只存了用户名
            username = data.get('username')
            if not username:
                return JsonResponse({'code': 400, 'message': '未检测到登录状态，请重新登录'})

            # 2. 找到对应的用户对象
            try:
                user = User.objects.get(username=username)
            except User.DoesNotExist:
                return JsonResponse({'code': 404, 'message': '发布人账号异常'})
            if is_user_blacklisted(user):
                return JsonResponse({'code': 403, 'message': '你已被限制发布任务，请先申诉或联系管理员'})

            reward_points = int(data.get('reward_points', data.get('reward', 10)))
            if reward_points <= 0:
                return JsonResponse({'code': 400, 'message': '积分必须大于 0'})

            if user.points < reward_points:
                return JsonResponse({'code': 400, 'message': '积分不足，无法发布该任务'})

            latitude = data.get('latitude')
            longitude = data.get('longitude')
            community_zone = data.get('community_zone')
            assignee_type = (data.get('assignee_type') or 'any').strip()
            invited_provider_username = (data.get('invited_provider_username') or '').strip()

            if assignee_type not in {'any', 'expert', 'provider'}:
                return JsonResponse({'code': 400, 'message': '接单身份类型不合法'})
            invited_provider = None
            if invited_provider_username:
                invited_provider = User.objects.filter(username=invited_provider_username).first()
                if not invited_provider or not invited_provider.is_provider:
                    return JsonResponse({'code': 400, 'message': '被邀约对象不存在或不是认证服务者'})
                assignee_type = 'provider'

            if not community_zone and latitude is not None and longitude is not None:
                try:
                    community_zone = f"约 {float(latitude):.2f}, {float(longitude):.2f} 附近"
                except Exception:
                    community_zone = None
            hits = detect_sensitive_keywords(data.get('title'), data.get('content'), community_zone)

            with transaction.atomic():
                user.points = F('points') - reward_points
                user.save(update_fields=['points'])
                user.refresh_from_db(fields=['points'])

                created_task = Task.objects.create(
                    title=data.get('title'),
                    content=data.get('content'),
                    category=data.get('category'),
                    reward_points=reward_points,
                    assignee_type=assignee_type,
                    settlement_points=None,
                    refund_points=None,
                    invited_provider=invited_provider,
                    community_zone=community_zone,
                    latitude=latitude if latitude not in ['', None] else None,
                    longitude=longitude if longitude not in ['', None] else None,
                    creator=user,
                    status='auditing',
                    risk_flagged=bool(hits),
                    risk_keywords=','.join(hits) if hits else None
                )

                PointTransaction.objects.create(
                    user=user,
                    change=-reward_points,
                    reason='发布任务冻结积分'
                )
                log_audit(
                    action='create_task',
                    actor=user,
                    target_type='task',
                    target_id=created_task.id,
                    detail=f'发布任务，冻结积分 {reward_points}，接单身份 {assignee_type}，定向邀约 {invited_provider_username or "无"}，关键词命中: {",".join(hits) if hits else "无"}'
                )

            return JsonResponse({
                'code': 200,
                'message': '提交成功！任务已进入待审核队列，通过后将发布到市场。' if not hits else '任务已提交，检测到敏感词，等待人工复核。',
                'points': user.points
            })

        except Exception as e:
            # 这里的 print 会出现在你的 PyCharm/黑窗口里，方便你看具体错哪了
            print(f"创建任务时发生错误: {str(e)}")
            return JsonResponse({'code': 500, 'message': f'服务器内部错误: {str(e)}'})

    return JsonResponse({'code': 405, 'message': '只支持POST请求'})

@csrf_exempt
def accept_task(request):
    """接单逻辑"""
    if request.method == 'POST':
        data = json.loads(request.body)
        task = Task.objects.get(id=data.get('task_id'))
        worker_user = User.objects.get(username=data.get('username'))
        if is_user_blacklisted(worker_user):
            return JsonResponse({'code': 403, 'message': '你已被限制接单，请先申诉或联系管理员'})

        if task.status != 'pending':
            return JsonResponse({'code': 400, 'message': '当前任务不可接单'})
        if task.worker_id:
            return JsonResponse({'code': 400, 'message': '任务已被接单'})
        if task.assignee_type == 'expert' and not worker_user.is_expert:
            return JsonResponse({'code': 403, 'message': '该任务仅限邻里达人接单'})
        if task.assignee_type == 'provider' and not worker_user.is_provider:
            return JsonResponse({'code': 403, 'message': '该任务仅限认证服务者接单'})
        if task.invited_provider_id and task.invited_provider_id != worker_user.id:
            return JsonResponse({'code': 403, 'message': '该任务为定向邀约任务，仅限被邀约认证服务者接单'})

        # 更新任务状态和接单人
        task.worker = worker_user
        task.status = 'accepted'
        task.accepted_at = now()
        task.submitted_at = None
        task.terminate_requested_by = None
        task.terminate_reason = None
        task.terminate_agreed_by = None
        task.terminate_reject_reason = None
        task.terminate_creator_points = None
        task.terminate_worker_points = None
        task.terminated_at = None
        task.save(update_fields=[
            'worker', 'status', 'accepted_at', 'submitted_at',
            'terminate_requested_by', 'terminate_reason', 'terminate_agreed_by',
            'terminate_reject_reason', 'terminate_creator_points', 'terminate_worker_points',
            'terminated_at', 'updated_at'
        ])
        log_audit(
            action='accept_task',
            actor=worker_user,
            target_type='task',
            target_id=task.id,
            detail='接单成功'
        )
        return JsonResponse({'code': 200, 'message': '接单成功！'})


@csrf_exempt
def get_my_tasks(request):
    """获取与当前用户相关的任务"""
    auto_finish_overdue_submitted_tasks()

    username = request.GET.get('username')
    user = User.objects.get(username=username)

    # 我发布的
    my_posted = Task.objects.filter(creator=user).select_related('creator', 'worker', 'review', 'invited_provider').order_by('-created_at')
    # 我接手的
    my_accepted = Task.objects.filter(worker=user).select_related('creator', 'worker', 'review', 'invited_provider').order_by('-created_at')

    # 序列化逻辑（建议封装成函数，这里为了演示直接写）
    def serialize(queryset):
        auto_cutoff = timedelta(minutes=AUTO_ACCEPT_MINUTES)
        rows = []
        for t in queryset:
            review_data = None
            if hasattr(t, 'review'):
                review_data = {
                    'rating': t.review.rating,
                    'comment': t.review.comment,
                    'tags': t.review.tags,
                    'reviewer': t.review.reviewer.username,
                    'reviewee': t.review.reviewee.username,
                    'created_at': t.review.created_at.strftime('%Y-%m-%d %H:%M:%S')
                }
            rows.append({
                'id': t.id,
                'title': t.title,
                'status': t.status,
                'worker': t.worker.username if t.worker else None,
                'creator': t.creator.username,
                'content': t.content,
                'category': t.category,
                'reward_points': t.reward_points,
                'assignee_type': t.assignee_type or 'any',
                'invited_provider': t.invited_provider.username if t.invited_provider else None,
                'community_zone': t.community_zone,
                'latitude': float(t.latitude) if t.latitude is not None else None,
                'longitude': float(t.longitude) if t.longitude is not None else None,
                'result_desc': t.result_desc,
                'abandon_reason': t.abandon_reason,
                'terminate_requested_by': t.terminate_requested_by,
                'terminate_reason': t.terminate_reason,
                'terminate_agreed_by': t.terminate_agreed_by,
                'terminate_reject_reason': t.terminate_reject_reason,
                'terminate_creator_points': t.terminate_creator_points,
                'terminate_worker_points': t.terminate_worker_points,
                'settlement_points': t.settlement_points,
                'refund_points': t.refund_points,
                'quote_count': t.quotes.count(),
                'reviewed_by_creator': review_data is not None,
                'review': review_data,
                'accepted_at': t.accepted_at.strftime('%Y-%m-%d %H:%M:%S') if t.accepted_at else None,
                'submitted_at': t.submitted_at.strftime('%Y-%m-%d %H:%M:%S') if t.submitted_at else None,
                'terminated_at': t.terminated_at.strftime('%Y-%m-%d %H:%M:%S') if t.terminated_at else None,
                'auto_accept_deadline': (t.submitted_at + auto_cutoff).strftime('%Y-%m-%d %H:%M:%S')
                if t.status == 'submitted' and t.submitted_at else None,
                'created_at': t.created_at.strftime('%Y-%m-%d %H:%M')
            })
        return rows

    return JsonResponse({
        'code': 200,
        'posted': serialize(my_posted),
        'accepted': serialize(my_accepted)
    })


@csrf_exempt
def submit_task(request):
    """接单人提交任务成果"""
    if request.method == 'POST':
        data = json.loads(request.body)
        try:
            task = Task.objects.get(id=data.get('taskId'))
            task.status = 'submitted'  # 变更状态为：已提交(待确认)
            task.result_desc = data.get('desc')
            task.submitted_at = now()
            task.save(update_fields=['status', 'result_desc', 'submitted_at', 'updated_at'])
            return JsonResponse({'code': 200, 'message': '提交成功'})
        except Task.DoesNotExist:
            return JsonResponse({'code': 404, 'message': '任务不存在'})


@csrf_exempt
def abandon_task(request):
    """接单人放弃任务"""
    if request.method == 'POST':
        data = json.loads(request.body)
        try:
            task = Task.objects.get(id=data.get('taskId'))
            # 记录原因（可选，为了毕设完整性建议保留）
            task.abandon_reason = data.get('reason')

            # 🚀 核心逻辑：清空接单人，将状态重置为招募中
            task.worker = None
            task.status = 'pending'
            task.accepted_at = None
            task.submitted_at = None
            task.terminate_requested_by = None
            task.terminate_reason = None
            task.terminate_agreed_by = None
            task.terminate_reject_reason = None
            task.terminate_creator_points = None
            task.terminate_worker_points = None
            task.terminated_at = None

            task.save(update_fields=[
                'abandon_reason', 'worker', 'status', 'accepted_at', 'submitted_at',
                'terminate_requested_by', 'terminate_reason', 'terminate_agreed_by',
                'terminate_reject_reason', 'terminate_creator_points', 'terminate_worker_points',
                'terminated_at', 'updated_at'
            ])
            return JsonResponse({'code': 200, 'message': '已放弃任务，任务已重回市场'})
        except Task.DoesNotExist:
            return JsonResponse({'code': 404, 'message': '任务不存在'})

# users/views.py

@csrf_exempt
def finish_task(request):
    """发布人确认任务已圆满完成"""
    if request.method == 'POST':
        data = json.loads(request.body)
        username = data.get('username')
        try:
            with transaction.atomic():
                task = Task.objects.select_for_update().get(id=data.get('task_id'))

                if task.status == 'finished':
                    return JsonResponse({'code': 200, 'message': '该任务已完成，无需重复确认'})

                if task.status != 'submitted':
                    return JsonResponse({'code': 400, 'message': '当前状态不可确认结项'})

                if not task.worker:
                    return JsonResponse({'code': 400, 'message': '任务尚未分配接单人'})

                if username and task.creator.username != username:
                    return JsonResponse({'code': 403, 'message': '只有发布人可以确认结项'})

                worker = task.worker
                worker.points = F('points') + task.reward_points
                worker.save(update_fields=['points'])

                PointTransaction.objects.create(
                    user=worker,
                    change=task.reward_points,
                    reason=f'完成任务获得积分：{task.title}'
                )

                task.status = 'finished'
                task.settlement_points = task.reward_points
                task.refund_points = 0
                task.save(update_fields=['status', 'settlement_points', 'refund_points', 'updated_at'])

                worker.refresh_from_db(fields=['points'])
                creator = User.objects.filter(username=username).first() if username else None
                log_audit(
                    action='finish_task',
                    actor=creator,
                    target_type='task',
                    target_id=task.id,
                    detail=f'确认结项，全额发放 {task.reward_points}'
                )

            return JsonResponse({
                'code': 200,
                'message': f'任务已完结，已向接单者发放 {task.reward_points} 积分',
                'worker_points': worker.points
            })
        except Task.DoesNotExist:
            return JsonResponse({'code': 404, 'message': '任务不存在'})


@csrf_exempt
def finish_task_with_settlement(request):
    """发布人确认任务完成，支持部分结算+退款"""
    if request.method != 'POST':
        return JsonResponse({'code': 405, 'message': '只支持POST'})
    try:
        data = json.loads(request.body)
        task_id = data.get('task_id')
        username = (data.get('username') or '').strip()
        worker_points = int(data.get('worker_points'))
    except Exception:
        return JsonResponse({'code': 400, 'message': '请求参数错误'})

    with transaction.atomic():
        task = Task.objects.select_for_update().select_related('creator', 'worker').filter(id=task_id).first()
        if not task:
            return JsonResponse({'code': 404, 'message': '任务不存在'})
        if task.status != 'submitted':
            return JsonResponse({'code': 400, 'message': '当前状态不可确认结项'})
        if not task.worker:
            return JsonResponse({'code': 400, 'message': '任务尚未分配接单人'})
        if username and task.creator.username != username:
            return JsonResponse({'code': 403, 'message': '只有发布人可以确认结项'})
        if worker_points < 0 or worker_points > task.reward_points:
            return JsonResponse({'code': 400, 'message': f'结算积分必须在 0 到 {task.reward_points} 之间'})

        refund_points = task.reward_points - worker_points
        if worker_points > 0:
            task.worker.points = F('points') + worker_points
            task.worker.save(update_fields=['points'])
            PointTransaction.objects.create(
                user=task.worker,
                change=worker_points,
                reason=f'任务结项获得积分：{task.title}'
            )
        if refund_points > 0:
            task.creator.points = F('points') + refund_points
            task.creator.save(update_fields=['points'])
            PointTransaction.objects.create(
                user=task.creator,
                change=refund_points,
                reason=f'任务结项退款：{task.title}'
            )

        task.status = 'finished'
        task.settlement_points = worker_points
        task.refund_points = refund_points
        task.save(update_fields=['status', 'settlement_points', 'refund_points', 'updated_at'])
        log_audit(
            action='finish_task_with_settlement',
            actor=task.creator,
            target_type='task',
            target_id=task.id,
            detail=f'结项分配：接单方 {worker_points}，发单方退款 {refund_points}'
        )

    return JsonResponse({
        'code': 200,
        'message': '结项成功',
        'worker_points': worker_points,
        'refund_points': refund_points
    })


@csrf_exempt
def update_task(request):
    if request.method != 'POST':
        return JsonResponse({'code': 405, 'message': '只支持POST'})

    try:
        data = json.loads(request.body)
        username = (data.get('username') or '').strip()
        task_id = data.get('task_id')
        title = (data.get('title') or '').strip()
        content = (data.get('content') or '').strip()
        category = (data.get('category') or '').strip()
        reward_points = int(data.get('reward_points', 0))
    except Exception:
        return JsonResponse({'code': 400, 'message': '请求参数错误'})

    if not username or not task_id:
        return JsonResponse({'code': 400, 'message': '缺少必要参数'})
    if not title or not content:
        return JsonResponse({'code': 400, 'message': '任务标题和内容不能为空'})
    if reward_points <= 0:
        return JsonResponse({'code': 400, 'message': '积分必须大于 0'})

    user = User.objects.filter(username=username).first()
    if not user:
        return JsonResponse({'code': 404, 'message': '用户不存在'})

    task = Task.objects.filter(id=task_id).select_related('creator').first()
    if not task:
        return JsonResponse({'code': 404, 'message': '任务不存在'})

    if not can_user_manage_task(user, task):
        return JsonResponse({'code': 403, 'message': '当前任务状态不允许修改'})

    points_diff = reward_points - task.reward_points
    if points_diff > 0 and user.points < points_diff:
        return JsonResponse({'code': 400, 'message': '积分不足，无法提高悬赏积分'})

    with transaction.atomic():
        if points_diff != 0:
            user.points = F('points') - points_diff
            user.save(update_fields=['points'])
            user.refresh_from_db(fields=['points'])
            PointTransaction.objects.create(
                user=user,
                change=-points_diff,
                reason=f'修改任务悬赏积分：{task.title}'
            )

        if 'community_zone' in data:
            community_zone = (data.get('community_zone') or '').strip() or None
        else:
            community_zone = task.community_zone

        latitude = data.get('latitude') if 'latitude' in data else task.latitude
        longitude = data.get('longitude') if 'longitude' in data else task.longitude
        hits = detect_sensitive_keywords(title, content, community_zone)

        task.title = title
        task.content = content
        task.category = category or task.category
        task.reward_points = reward_points
        task.community_zone = community_zone
        task.latitude = latitude if latitude not in ['', None] else None
        task.longitude = longitude if longitude not in ['', None] else None
        task.status = 'auditing'
        task.audit_reason = '任务已修改，等待重新审核'
        task.risk_flagged = bool(hits)
        task.risk_keywords = ','.join(hits) if hits else None
        task.save(update_fields=[
            'title', 'content', 'category', 'reward_points', 'community_zone',
            'latitude', 'longitude', 'status', 'audit_reason', 'risk_flagged', 'risk_keywords', 'updated_at'
        ])
        log_audit(
            action='update_task',
            actor=user,
            target_type='task',
            target_id=task.id,
            detail=f'修改任务，关键词命中: {",".join(hits) if hits else "无"}'
        )

    return JsonResponse({
        'code': 200,
        'message': '任务已修改并下架，需管理员审核后重新发布',
        'points': user.points
    })


@csrf_exempt
def delete_task(request):
    if request.method != 'POST':
        return JsonResponse({'code': 405, 'message': '只支持POST'})

    try:
        data = json.loads(request.body)
        username = (data.get('username') or '').strip()
        task_id = data.get('task_id')
    except Exception:
        return JsonResponse({'code': 400, 'message': '请求参数错误'})

    if not username or not task_id:
        return JsonResponse({'code': 400, 'message': '缺少必要参数'})

    user = User.objects.filter(username=username).first()
    if not user:
        return JsonResponse({'code': 404, 'message': '用户不存在'})

    task = Task.objects.filter(id=task_id).select_related('creator').first()
    if not task:
        return JsonResponse({'code': 404, 'message': '任务不存在'})

    if task.creator_id != user.id:
        return JsonResponse({'code': 403, 'message': '只有发布者可以删除任务'})
    if task.status in {'accepted', 'submitted', 'intervention', 'terminating_pending_peer', 'terminating_admin_review'}:
        return JsonResponse({'code': 400, 'message': '该任务正在执行或审核中，暂不可删除'})

    with transaction.atomic():
        if task.status in {'auditing', 'pending', 'rejected'}:
            user.points = F('points') + task.reward_points
            user.save(update_fields=['points'])
            PointTransaction.objects.create(
                user=user,
                change=task.reward_points,
                reason=f'删除任务退回冻结积分：{task.title}'
            )
        task.delete()
    log_audit(action='delete_task', actor=user, target_type='task', target_id=task_id, detail='删除任务')

    return JsonResponse({'code': 200, 'message': '任务已删除'})


@csrf_exempt
def request_terminate_task(request):
    if request.method != 'POST':
        return JsonResponse({'code': 405, 'message': '只支持POST'})

    try:
        data = json.loads(request.body)
        username = (data.get('username') or '').strip()
        task_id = data.get('task_id')
        reason = (data.get('reason') or '').strip()
    except Exception:
        return JsonResponse({'code': 400, 'message': '请求参数错误'})

    if not username or not task_id:
        return JsonResponse({'code': 400, 'message': '缺少必要参数'})
    if not reason:
        return JsonResponse({'code': 400, 'message': '请填写终止原因'})

    with transaction.atomic():
        task = Task.objects.select_for_update().filter(id=task_id).select_related('creator', 'worker').first()
        if not task:
            return JsonResponse({'code': 404, 'message': '任务不存在'})

        if not can_user_request_termination(username, task):
            return JsonResponse({'code': 403, 'message': '当前状态不允许发起终止'})

        task.status = 'terminating_pending_peer'
        task.terminate_requested_by = username
        task.terminate_reason = reason
        task.terminate_agreed_by = None
        task.terminate_reject_reason = None
        task.terminate_creator_points = None
        task.terminate_worker_points = None
        task.terminated_at = None
        task.save(update_fields=[
            'status', 'terminate_requested_by', 'terminate_reason', 'terminate_agreed_by',
            'terminate_reject_reason', 'terminate_creator_points', 'terminate_worker_points',
            'terminated_at', 'updated_at'
        ])
    actor = User.objects.filter(username=username).first()
    log_audit(action='request_terminate_task', actor=actor, target_type='task', target_id=task_id, detail=reason)

    return JsonResponse({'code': 200, 'message': '已发起终止申请，等待对方同意'})


@csrf_exempt
def respond_terminate_task(request):
    if request.method != 'POST':
        return JsonResponse({'code': 405, 'message': '只支持POST'})

    try:
        data = json.loads(request.body)
        username = (data.get('username') or '').strip()
        task_id = data.get('task_id')
        agree = bool(data.get('agree'))
        reason = (data.get('reason') or '').strip()
    except Exception:
        return JsonResponse({'code': 400, 'message': '请求参数错误'})

    if not username or not task_id:
        return JsonResponse({'code': 400, 'message': '缺少必要参数'})

    with transaction.atomic():
        task = Task.objects.select_for_update().filter(id=task_id).select_related('creator', 'worker').first()
        if not task:
            return JsonResponse({'code': 404, 'message': '任务不存在'})
        if task.status != 'terminating_pending_peer':
            return JsonResponse({'code': 400, 'message': '当前任务不在待对方确认终止状态'})

        if not task.worker:
            return JsonResponse({'code': 400, 'message': '任务暂无接单方，无法执行终止流程'})

        requester = task.terminate_requested_by
        if requester not in {task.creator.username, task.worker.username}:
            return JsonResponse({'code': 400, 'message': '终止申请记录异常'})
        if username == requester:
            return JsonResponse({'code': 403, 'message': '发起人不能重复确认，请等待对方处理'})

        if username not in {task.creator.username, task.worker.username}:
            return JsonResponse({'code': 403, 'message': '你没有该任务终止操作权限'})

        # 新规则：
        # 1) 对方同意终止 => 直接终止（默认全额退回发单方，接单方 0）
        # 2) 对方不同意终止 => 转管理员复审
        if agree:
            creator_points = int(task.reward_points or 0)
            worker_points = 0
            if creator_points > 0:
                task.creator.points = F('points') + creator_points
                task.creator.save(update_fields=['points'])
                PointTransaction.objects.create(
                    user=task.creator,
                    change=creator_points,
                    reason=f'双方同意终止任务退回积分：{task.title}'
                )

            task.status = 'terminated'
            task.terminate_agreed_by = username
            task.terminate_reject_reason = None
            task.terminate_creator_points = creator_points
            task.terminate_worker_points = worker_points
            task.terminated_at = now()
            task.save(update_fields=[
                'status', 'terminate_agreed_by', 'terminate_reject_reason',
                'terminate_creator_points', 'terminate_worker_points', 'terminated_at', 'updated_at'
            ])
            actor = User.objects.filter(username=username).first()
            log_audit(
                action='respond_terminate_task',
                actor=actor,
                target_type='task',
                target_id=task_id,
                detail=f'同意终止，直接结案：发单方 {creator_points} / 接单方 {worker_points}'
            )
            return JsonResponse({'code': 200, 'message': '双方已同意终止，任务已终止并完成结算'})

        task.status = 'terminating_admin_review'
        task.terminate_agreed_by = None
        task.terminate_reject_reason = reason or '对方不同意终止'
        task.save(update_fields=['status', 'terminate_agreed_by', 'terminate_reject_reason', 'updated_at'])
        actor = User.objects.filter(username=username).first()
        log_audit(
            action='respond_terminate_task',
            actor=actor,
            target_type='task',
            target_id=task_id,
            detail=f'不同意终止，转管理员复审: {reason or "未填写"}'
        )
        return JsonResponse({'code': 200, 'message': '对方未同意终止，已转交管理员复审'})


# users/views.py
import json
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from .models import Task, User


@csrf_exempt
def get_audit_tasks(request):
    """管理员专用：获取待初审、待复审、待终止审核的任务"""
    auto_finish_overdue_submitted_tasks()

    tasks = Task.objects.filter(
        status__in=['auditing', 'intervention', 'terminating_admin_review']
    ).order_by('-created_at')

    data = []
    for t in tasks:
        data.append({
            'id': t.id,
            'title': t.title,
            'category': t.category,
            'content': t.content,
            'status': t.status,
            'creator': t.creator.username,
            'worker': t.worker.username if t.worker else "暂无",
            'result_desc': t.result_desc,  # 达人提交的成果描述
            'reward_points': t.reward_points,
            'terminate_requested_by': t.terminate_requested_by,
            'terminate_reason': t.terminate_reason,
            'terminate_agreed_by': t.terminate_agreed_by,
            'terminate_reject_reason': t.terminate_reject_reason,
            'terminate_creator_points': t.terminate_creator_points,
            'terminate_worker_points': t.terminate_worker_points,
            'created_at': t.created_at.strftime('%Y-%m-%d %H:%M')
        })
    return JsonResponse({'code': 200, 'tasks': data})


@csrf_exempt
def update_user_points(request):
    if request.method != 'POST':
        return JsonResponse({'code': 405, 'message': '只支持POST'})

    try:
        data = json.loads(request.body)
        admin_username = data.get('admin_username')
        user_id = data.get('user_id')
        points = int(data.get('points'))
    except Exception:
        return JsonResponse({'code': 400, 'message': '请求参数错误'})

    admin = User.objects.filter(username=admin_username).first()
    if not admin or admin.role != 'admin':
        return JsonResponse({'code': 403, 'message': '只有管理员可以修改积分'})

    user = User.objects.filter(id=user_id).first()
    if not user:
        return JsonResponse({'code': 404, 'message': '目标用户不存在'})

    old_points = user.points
    user.points = points
    user.save(update_fields=['points'])

    PointTransaction.objects.create(
        user=user,
        change=points - old_points,
        reason=f'管理员调整积分：{admin_username}'
    )
    log_audit(
        action='update_user_points',
        actor=admin,
        target_type='user',
        target_id=user.id,
        detail=f'积分从 {old_points} 调整为 {points}'
    )

    return JsonResponse({'code': 200, 'message': '积分修改成功', 'points': user.points})


@csrf_exempt
def blacklist_user(request):
    if request.method != 'POST':
        return JsonResponse({'code': 405, 'message': '只支持POST'})
    try:
        data = json.loads(request.body)
        admin_username = (data.get('admin_username') or '').strip()
        user_id = data.get('user_id')
        reason = (data.get('reason') or '').strip()
        days = int(data.get('days', 30))
    except Exception:
        return JsonResponse({'code': 400, 'message': '请求参数错误'})

    admin = User.objects.filter(username=admin_username, role='admin').first()
    if not admin:
        return JsonResponse({'code': 403, 'message': '只有管理员可以拉黑用户'})
    user = User.objects.filter(id=user_id).first()
    if not user:
        return JsonResponse({'code': 404, 'message': '目标用户不存在'})

    user.is_blacklisted = True
    user.blacklist_reason = reason or '违反平台规则'
    user.blacklist_until = now() + timedelta(days=max(1, days))
    user.save(update_fields=['is_blacklisted', 'blacklist_reason', 'blacklist_until'])
    log_audit(
        action='blacklist_user',
        actor=admin,
        target_type='user',
        target_id=user.id,
        detail=f'原因: {user.blacklist_reason}, 截止: {user.blacklist_until}'
    )
    return JsonResponse({'code': 200, 'message': '用户已加入黑名单'})


@csrf_exempt
def unblacklist_user(request):
    if request.method != 'POST':
        return JsonResponse({'code': 405, 'message': '只支持POST'})
    try:
        data = json.loads(request.body)
        admin_username = (data.get('admin_username') or '').strip()
        user_id = data.get('user_id')
    except Exception:
        return JsonResponse({'code': 400, 'message': '请求参数错误'})

    admin = User.objects.filter(username=admin_username, role='admin').first()
    if not admin:
        return JsonResponse({'code': 403, 'message': '只有管理员可以操作'})
    user = User.objects.filter(id=user_id).first()
    if not user:
        return JsonResponse({'code': 404, 'message': '目标用户不存在'})

    user.is_blacklisted = False
    user.blacklist_reason = None
    user.blacklist_until = None
    user.save(update_fields=['is_blacklisted', 'blacklist_reason', 'blacklist_until'])
    log_audit(action='unblacklist_user', actor=admin, target_type='user', target_id=user.id, detail='解除黑名单')
    return JsonResponse({'code': 200, 'message': '已解除黑名单'})


@csrf_exempt
def submit_blacklist_appeal(request):
    if request.method != 'POST':
        return JsonResponse({'code': 405, 'message': '只支持POST'})
    try:
        data = json.loads(request.body)
        username = (data.get('username') or '').strip()
        reason = (data.get('reason') or '').strip()
    except Exception:
        return JsonResponse({'code': 400, 'message': '请求参数错误'})
    if not username or not reason:
        return JsonResponse({'code': 400, 'message': '缺少必要参数'})
    user = User.objects.filter(username=username).first()
    if not user:
        return JsonResponse({'code': 404, 'message': '用户不存在'})
    BlacklistAppeal.objects.create(user=user, reason=reason)
    log_audit(action='submit_blacklist_appeal', actor=user, target_type='user', target_id=user.id, detail=reason)
    return JsonResponse({'code': 200, 'message': '申诉已提交'})


@csrf_exempt
def list_blacklist_appeals(request):
    if request.method != 'GET':
        return JsonResponse({'code': 405, 'message': '只支持GET'})
    admin_username = (request.GET.get('admin_username') or '').strip()
    admin = User.objects.filter(username=admin_username, role='admin').first()
    if not admin:
        return JsonResponse({'code': 403, 'message': '只有管理员可以查看申诉'})
    rows = []
    for item in BlacklistAppeal.objects.select_related('user').all()[:200]:
        rows.append({
            'id': item.id,
            'username': item.user.username,
            'reason': item.reason,
            'status': item.status,
            'review_note': item.review_note,
            'created_at': item.created_at.strftime('%Y-%m-%d %H:%M:%S'),
            'reviewed_at': item.reviewed_at.strftime('%Y-%m-%d %H:%M:%S') if item.reviewed_at else None
        })
    return JsonResponse({'code': 200, 'appeals': rows})


@csrf_exempt
def handle_blacklist_appeal(request):
    if request.method != 'POST':
        return JsonResponse({'code': 405, 'message': '只支持POST'})
    try:
        data = json.loads(request.body)
        admin_username = (data.get('admin_username') or '').strip()
        appeal_id = data.get('appeal_id')
        action = (data.get('action') or '').strip()
        note = (data.get('note') or '').strip()
    except Exception:
        return JsonResponse({'code': 400, 'message': '请求参数错误'})
    admin = User.objects.filter(username=admin_username, role='admin').first()
    if not admin:
        return JsonResponse({'code': 403, 'message': '只有管理员可以处理申诉'})
    appeal = BlacklistAppeal.objects.select_related('user').filter(id=appeal_id).first()
    if not appeal:
        return JsonResponse({'code': 404, 'message': '申诉不存在'})
    if appeal.status != 'pending':
        return JsonResponse({'code': 400, 'message': '该申诉已处理'})
    if action == 'approve':
        appeal.status = 'approved'
        appeal.user.is_blacklisted = False
        appeal.user.blacklist_reason = None
        appeal.user.blacklist_until = None
        appeal.user.save(update_fields=['is_blacklisted', 'blacklist_reason', 'blacklist_until'])
    else:
        appeal.status = 'rejected'
    appeal.review_note = note or None
    appeal.reviewed_at = now()
    appeal.save(update_fields=['status', 'review_note', 'reviewed_at'])
    log_audit(
        action='handle_blacklist_appeal',
        actor=admin,
        target_type='appeal',
        target_id=appeal.id,
        detail=f'{action}: {note}'
    )
    return JsonResponse({'code': 200, 'message': '处理成功'})


@csrf_exempt
def get_audit_logs(request):
    if request.method != 'GET':
        return JsonResponse({'code': 405, 'message': '只支持GET'})
    admin_username = (request.GET.get('admin_username') or '').strip()
    admin = User.objects.filter(username=admin_username, role='admin').first()
    if not admin:
        return JsonResponse({'code': 403, 'message': '只有管理员可以查看审计日志'})
    limit = min(max(int(request.GET.get('limit', 50)), 1), 200)
    logs = AuditLog.objects.select_related('actor').all()[:limit]
    data = [{
        'id': l.id,
        'actor': l.actor.username if l.actor else 'system',
        'action': l.action,
        'target_type': l.target_type,
        'target_id': l.target_id,
        'detail': l.detail,
        'created_at': l.created_at.strftime('%Y-%m-%d %H:%M:%S')
    } for l in logs]
    return JsonResponse({'code': 200, 'logs': data})


@csrf_exempt
def create_task_quote(request):
    if request.method != 'POST':
        return JsonResponse({'code': 405, 'message': '只支持POST'})
    try:
        data = json.loads(request.body)
        username = (data.get('username') or '').strip()
        task_id = data.get('task_id')
        amount_points = int(data.get('amount_points'))
        message = (data.get('message') or '').strip()
    except Exception:
        return JsonResponse({'code': 400, 'message': '请求参数错误'})
    user = User.objects.filter(username=username).first()
    if not user:
        return JsonResponse({'code': 404, 'message': '用户不存在'})
    if is_user_blacklisted(user):
        return JsonResponse({'code': 403, 'message': '你已被限制交易，请先申诉或联系管理员'})
    if not (user.is_expert or user.is_provider):
        return JsonResponse({'code': 403, 'message': '仅邻里达人或认证服务者可报价'})
    task = Task.objects.select_related('creator').filter(id=task_id).first()
    if not task:
        return JsonResponse({'code': 404, 'message': '任务不存在'})
    if task.status != 'pending':
        return JsonResponse({'code': 400, 'message': '该任务当前不可报价'})
    if task.creator_id == user.id:
        return JsonResponse({'code': 400, 'message': '不能给自己发布的任务报价'})
    if amount_points < 0:
        return JsonResponse({'code': 400, 'message': '报价不能为负数'})
    quote, created = TaskQuote.objects.get_or_create(
        task=task,
        quoter=user,
        defaults={'amount_points': amount_points, 'message': message}
    )
    if not created:
        quote.amount_points = amount_points
        quote.message = message
        quote.status = 'pending'
        quote.save(update_fields=['amount_points', 'message', 'status', 'updated_at'])
    log_audit(
        action='create_task_quote',
        actor=user,
        target_type='task',
        target_id=task.id,
        detail=f'报价 {amount_points}'
    )
    return JsonResponse({'code': 200, 'message': '报价已提交'})


@csrf_exempt
def get_task_quotes(request):
    if request.method != 'GET':
        return JsonResponse({'code': 405, 'message': '只支持GET'})
    username = (request.GET.get('username') or '').strip()
    task_id = request.GET.get('task_id')
    user = User.objects.filter(username=username).first()
    task = Task.objects.select_related('creator').filter(id=task_id).first()
    if not user or not task:
        return JsonResponse({'code': 404, 'message': '用户或任务不存在'})
    if user.role != 'admin' and user.username != task.creator.username and not TaskQuote.objects.filter(task=task, quoter=user).exists():
        return JsonResponse({'code': 403, 'message': '无权限查看该任务报价'})
    quotes = TaskQuote.objects.filter(task=task).select_related('quoter').order_by('amount_points', 'created_at')
    data = [{
        'id': q.id,
        'quoter': q.quoter.username,
        'amount_points': q.amount_points,
        'message': q.message,
        'status': q.status,
        'created_at': q.created_at.strftime('%Y-%m-%d %H:%M:%S')
    } for q in quotes]
    return JsonResponse({'code': 200, 'quotes': data})


@csrf_exempt
def choose_task_quote(request):
    if request.method != 'POST':
        return JsonResponse({'code': 405, 'message': '只支持POST'})
    try:
        data = json.loads(request.body)
        username = (data.get('username') or '').strip()
        task_id = data.get('task_id')
        quote_id = data.get('quote_id')
    except Exception:
        return JsonResponse({'code': 400, 'message': '请求参数错误'})
    task = Task.objects.select_related('creator').filter(id=task_id).first()
    if not task:
        return JsonResponse({'code': 404, 'message': '任务不存在'})
    if task.creator.username != username:
        return JsonResponse({'code': 403, 'message': '只有发布人可选择报价'})
    if task.status != 'pending':
        return JsonResponse({'code': 400, 'message': '当前任务状态不可选报价'})
    quote = TaskQuote.objects.select_related('quoter').filter(id=quote_id, task=task).first()
    if not quote:
        return JsonResponse({'code': 404, 'message': '报价不存在'})

    with transaction.atomic():
        creator = task.creator
        old_reward = int(task.reward_points or 0)
        new_reward = int(quote.amount_points or 0)
        diff = new_reward - old_reward

        # 报价高于原悬赏时，需要补扣差额积分
        if diff > 0:
            creator.refresh_from_db(fields=['points'])
            if creator.points < diff:
                return JsonResponse({'code': 400, 'message': f'积分不足，无法选择该报价（还需 {diff} 积分）'})
            creator.points = F('points') - diff
            creator.save(update_fields=['points'])
            PointTransaction.objects.create(
                user=creator,
                change=-diff,
                reason=f'选择更高报价补扣积分：{task.title}'
            )
        # 报价低于原悬赏时，立即退回差额积分
        elif diff < 0:
            refund = -diff
            creator.points = F('points') + refund
            creator.save(update_fields=['points'])
            PointTransaction.objects.create(
                user=creator,
                change=refund,
                reason=f'选择较低报价退回积分：{task.title}'
            )

        TaskQuote.objects.filter(task=task).exclude(id=quote.id).update(status='rejected')
        quote.status = 'selected'
        quote.save(update_fields=['status', 'updated_at'])
        task.worker = quote.quoter
        task.status = 'accepted'
        task.accepted_at = now()
        task.reward_points = new_reward
        task.save(update_fields=['worker', 'status', 'accepted_at', 'reward_points', 'updated_at'])
    actor = User.objects.filter(username=username).first()
    log_audit(
        action='choose_task_quote',
        actor=actor,
        target_type='task',
        target_id=task.id,
        detail=f'选择报价人 {quote.quoter.username}, 报价 {quote.amount_points}'
    )
    return JsonResponse({'code': 200, 'message': '已选择服务者并进入进行中'})


@csrf_exempt
def create_task_review(request):
    if request.method != 'POST':
        return JsonResponse({'code': 405, 'message': '只支持POST'})
    try:
        data = json.loads(request.body)
        username = (data.get('username') or '').strip()
        task_id = data.get('task_id')
        rating = int(data.get('rating', 5))
        comment = (data.get('comment') or '').strip()
        tags = data.get('tags') or []
    except Exception:
        return JsonResponse({'code': 400, 'message': '请求参数错误'})
    if rating < 1 or rating > 5:
        return JsonResponse({'code': 400, 'message': '评分必须为 1-5'})
    task = Task.objects.select_related('creator', 'worker').filter(id=task_id).first()
    if not task:
        return JsonResponse({'code': 404, 'message': '任务不存在'})
    if task.creator.username != username:
        return JsonResponse({'code': 403, 'message': '只有发布人可以评价'})
    if task.status not in {'finished', 'terminated'}:
        return JsonResponse({'code': 400, 'message': '当前任务尚不可评价'})
    if not task.worker:
        return JsonResponse({'code': 400, 'message': '任务无接单方，无法评价'})
    if TaskReview.objects.filter(task=task).exists():
        return JsonResponse({'code': 400, 'message': '该任务已评价'})
    tags_text = ','.join(tags) if isinstance(tags, list) else str(tags)
    TaskReview.objects.create(
        task=task,
        reviewer=task.creator,
        reviewee=task.worker,
        rating=rating,
        comment=comment,
        tags=tags_text
    )
    log_audit(
        action='create_task_review',
        actor=task.creator,
        target_type='task',
        target_id=task.id,
        detail=f'评分 {rating}, 标签 {tags_text}'
    )
    return JsonResponse({'code': 200, 'message': '评价提交成功'})


@csrf_exempt
def get_provider_reviews(request):
    if request.method != 'GET':
        return JsonResponse({'code': 405, 'message': '只支持GET'})
    username = (request.GET.get('username') or '').strip()
    user = User.objects.filter(username=username).first()
    if not user:
        return JsonResponse({'code': 404, 'message': '用户不存在'})
    reviews = TaskReview.objects.filter(reviewee=user).select_related('reviewer', 'task')[:100]
    data = [{
        'id': r.id,
        'task_id': r.task.id,
        'task_title': r.task.title,
        'reviewer': r.reviewer.username,
        'rating': r.rating,
        'comment': r.comment,
        'tags': r.tags,
        'created_at': r.created_at.strftime('%Y-%m-%d %H:%M:%S')
    } for r in reviews]
    avg_rating = round(sum([r.rating for r in reviews]) / len(reviews), 2) if reviews else 0
    return JsonResponse({'code': 200, 'avg_rating': avg_rating, 'reviews': data})


@csrf_exempt
def list_verified_providers(request):
    if request.method != 'GET':
        return JsonResponse({'code': 405, 'message': '只支持GET'})

    keyword = (request.GET.get('keyword') or '').strip().lower()
    direction = (request.GET.get('direction') or '').strip()
    time_slot = (request.GET.get('time_slot') or '').strip()

    users = User.objects.filter(is_provider=True).order_by('username')
    applications = ExpertApplication.objects.filter(
        apply_type='provider',
        status='approved',
        username__in=list(users.values_list('username', flat=True))
    ).order_by('username', '-reviewed_at', '-created_at')

    latest_by_username = {}
    for app in applications:
        if app.username not in latest_by_username:
            latest_by_username[app.username] = app

    rows = []
    for provider in users:
        app = latest_by_username.get(provider.username)
        directions = parse_multi_tags(app.provider_service_directions if app else '')
        times = parse_multi_tags(app.provider_service_times if app else '')
        min_price, max_price = parse_price_range(app.provider_price_range if app else '')

        if keyword and keyword not in provider.username.lower():
            continue
        if direction and direction not in directions:
            continue
        if time_slot and time_slot not in times:
            continue

        rows.append({
            'username': provider.username,
            'avatar_text': (provider.username[:1] or 'P').upper(),
            'service_directions': directions,
            'service_times': times,
            'price_range': f'{min_price}元-{max_price}元' if min_price is not None and max_price is not None else '面议',
            'price_range_min': min_price,
            'price_range_max': max_price,
            'service_scope': app.service_scope if app else None,
            'provider_intro': app.provider_intro if app else None,
        })

    return JsonResponse({'code': 200, 'providers': rows})


@csrf_exempt
def get_provider_profile(request):
    if request.method != 'POST':
        return JsonResponse({'code': 405, 'message': '只支持POST'})
    try:
        data = json.loads(request.body)
        username = (data.get('username') or '').strip()
    except Exception:
        return JsonResponse({'code': 400, 'message': '请求数据格式错误'})

    user = User.objects.filter(username=username).first()
    if not user:
        return JsonResponse({'code': 404, 'message': '用户不存在'})
    if not user.is_provider:
        return JsonResponse({'code': 403, 'message': '你还不是认证服务者'})

    app = ExpertApplication.objects.filter(
        username=username,
        apply_type='provider',
        status='approved'
    ).order_by('-reviewed_at', '-created_at').first()
    if not app:
        app = ExpertApplication.objects.filter(
            username=username,
            apply_type='provider'
        ).order_by('-created_at').first()
    if not app:
        return JsonResponse({'code': 404, 'message': '未找到认证服务者资料'})

    return JsonResponse({
        'code': 200,
        'profile': {
            'service_scope': app.service_scope or '',
            'provider_service_directions': parse_multi_tags(app.provider_service_directions),
            'provider_service_times': parse_multi_tags(app.provider_service_times),
            'provider_price_range': app.provider_price_range or '',
            'provider_price_min': parse_price_range(app.provider_price_range)[0],
            'provider_price_max': parse_price_range(app.provider_price_range)[1],
            'provider_intro': app.provider_intro or '',
        }
    })


@csrf_exempt
def update_provider_profile(request):
    if request.method != 'POST':
        return JsonResponse({'code': 405, 'message': '只支持POST'})
    try:
        data = json.loads(request.body)
        username = (data.get('username') or '').strip()
        service_scope = (data.get('service_scope') or '').strip()
        provider_price_min = data.get('provider_price_min')
        provider_price_max = data.get('provider_price_max')
        provider_intro = (data.get('provider_intro') or '').strip()
        provider_service_directions = parse_multi_tags(data.get('provider_service_directions'))
        provider_service_times = parse_multi_tags(data.get('provider_service_times'))
    except Exception:
        return JsonResponse({'code': 400, 'message': '请求数据格式错误'})

    user = User.objects.filter(username=username).first()
    if not user:
        return JsonResponse({'code': 404, 'message': '用户不存在'})
    if not user.is_provider:
        return JsonResponse({'code': 403, 'message': '你还不是认证服务者'})
    if not provider_service_directions:
        return JsonResponse({'code': 400, 'message': '请至少选择一个服务方向'})
    if not provider_service_times:
        return JsonResponse({'code': 400, 'message': '请至少选择一个服务时间'})
    invalid_directions = [x for x in provider_service_directions if x not in PROVIDER_SERVICE_DIRECTIONS]
    invalid_times = [x for x in provider_service_times if x not in PROVIDER_SERVICE_TIME_BLOCKS]
    if invalid_directions or invalid_times:
        return JsonResponse({'code': 400, 'message': '服务方向或服务时间标签不合法'})
    min_price = None
    max_price = None
    if provider_price_min not in (None, '') or provider_price_max not in (None, ''):
        if str(provider_price_min).strip().isdigit() and str(provider_price_max).strip().isdigit():
            min_price = int(provider_price_min)
            max_price = int(provider_price_max)
            if min_price > max_price:
                min_price, max_price = max_price, min_price
        else:
            return JsonResponse({'code': 400, 'message': '价格区间只允许填写数字'})

    app = ExpertApplication.objects.filter(
        username=username,
        apply_type='provider',
        status='approved'
    ).order_by('-reviewed_at', '-created_at').first()
    if not app:
        return JsonResponse({'code': 404, 'message': '未找到已通过的认证服务者资料'})

    app.service_scope = service_scope or app.service_scope
    app.provider_price_range = serialize_price_range(min_price, max_price)
    app.provider_intro = provider_intro or None
    app.provider_service_directions = ','.join(provider_service_directions)
    app.provider_service_times = ','.join(provider_service_times)
    app.save(update_fields=[
        'service_scope', 'provider_price_range', 'provider_intro',
        'provider_service_directions', 'provider_service_times'
    ])

    log_audit(
        action='update_provider_profile',
        actor=user,
        target_type='expert_application',
        target_id=app.id,
        detail='认证服务者更新个人服务资料'
    )

    return JsonResponse({'code': 200, 'message': '认证服务者资料更新成功'})


@csrf_exempt
def admin_dashboard_stats(request):
    if request.method != 'GET':
        return JsonResponse({'code': 405, 'message': '只支持GET'})
    admin_username = (request.GET.get('admin_username') or '').strip()
    admin = User.objects.filter(username=admin_username, role='admin').first()
    if not admin:
        return JsonResponse({'code': 403, 'message': '只有管理员可以查看统计'})

    total_users = User.objects.count()
    blacklisted_users = User.objects.filter(is_blacklisted=True).count()
    total_tasks = Task.objects.count()
    finished_tasks = Task.objects.filter(status='finished').count()
    dispute_statuses = ['intervention', 'terminating_pending_peer', 'terminating_admin_review']
    dispute_tasks = Task.objects.filter(status__in=dispute_statuses).count()
    terminated_tasks = Task.objects.filter(status='terminated').count()
    total_posts = Post.objects.count()
    flagged_posts = Post.objects.filter(risk_flagged=True).count()
    flagged_tasks = Task.objects.filter(risk_flagged=True).count()
    completion_rate = round((finished_tasks / total_tasks) * 100, 2) if total_tasks else 0

    today = now().date()
    trend = []
    for i in range(6, -1, -1):
        d = today - timedelta(days=i)
        created = Task.objects.filter(created_at__date=d).count()
        finished = Task.objects.filter(updated_at__date=d, status='finished').count()
        trend.append({'date': d.strftime('%m-%d'), 'created': created, 'finished': finished})

    today_published = Task.objects.filter(created_at__date=today).count()
    today_finished = Task.objects.filter(updated_at__date=today, status='finished').count()
    today_disputed = Task.objects.filter(updated_at__date=today, status__in=dispute_statuses).count()
    today_terminated = Task.objects.filter(terminated_at__date=today).count()

    status_distribution = {
        '待审核': Task.objects.filter(status='auditing').count(),
        '招募中': Task.objects.filter(status='pending').count(),
        '进行中': Task.objects.filter(status='accepted').count(),
        '待确认': Task.objects.filter(status='submitted').count(),
        '纠纷中': Task.objects.filter(status__in=dispute_statuses).count(),
        '已完成': Task.objects.filter(status='finished').count(),
        '已终止': Task.objects.filter(status='terminated').count(),
    }

    return JsonResponse({
        'code': 200,
        'stats': {
            'total_users': total_users,
            'blacklisted_users': blacklisted_users,
            'total_tasks': total_tasks,
            'finished_tasks': finished_tasks,
            'terminated_tasks': terminated_tasks,
            'dispute_tasks': dispute_tasks,
            'completion_rate': completion_rate,
            'total_posts': total_posts,
            'flagged_posts': flagged_posts,
            'flagged_tasks': flagged_tasks,
            'point_transactions': PointTransaction.objects.count()
        },
        'today_stats': {
            'published': today_published,
            'finished': today_finished,
            'disputed': today_disputed,
            'terminated': today_terminated
        },
        'status_distribution': status_distribution,
        'trend_7d': trend
    })


@csrf_exempt
def admin_handle_review(request):
    """管理员审批接口：处理初审和复审"""
    if request.method == 'POST':
        data = json.loads(request.body)
        task_id = data.get('taskId')
        action = data.get('action')  # 'approve' 或 'reject'
        reason = data.get('reason')  # 理由/评语
        creator_points = data.get('creator_points')
        worker_points = data.get('worker_points')

        try:
            with transaction.atomic():
                task = Task.objects.select_for_update().select_related('creator', 'worker').get(id=task_id)

                # --- 情况 A：初审阶段 (auditing) ---
                if task.status == 'auditing':
                    if action == 'approve':
                        task.status = 'pending'  # 审核通过，进入市场
                        task.audit_reason = "审核通过"
                    else:
                        if not reason:
                            return JsonResponse({'code': 400, 'message': '拒绝发布必须填写原因'})
                        task.status = 'rejected'  # 拒绝发布
                        task.audit_reason = reason

                # --- 情况 B：复审/仲裁阶段 (intervention) ---
                elif task.status == 'intervention':
                    if not reason:
                        return JsonResponse({'code': 400, 'message': '仲裁必须填写判定理由'})

                    task.intervention_decision = reason
                    if action == 'approve':
                        task.status = 'finished'
                    else:
                        task.status = 'pending'
                        task.worker = None
                        task.accepted_at = None
                        task.submitted_at = None

                # --- 情况 C：终止任务审核阶段 (terminating_admin_review) ---
                elif task.status == 'terminating_admin_review':
                    if action == 'approve':
                        if not task.worker:
                            return JsonResponse({'code': 400, 'message': '任务接单方缺失，无法终止结算'})
                        try:
                            creator_points_val = int(creator_points)
                            worker_points_val = int(worker_points)
                        except (TypeError, ValueError):
                            return JsonResponse({'code': 400, 'message': '请填写有效的积分分配数值'})

                        if creator_points_val < 0 or worker_points_val < 0:
                            return JsonResponse({'code': 400, 'message': '积分分配不能为负数'})
                        if creator_points_val + worker_points_val != task.reward_points:
                            return JsonResponse({'code': 400, 'message': f'积分总和必须等于悬赏积分 {task.reward_points}'})

                        if creator_points_val > 0:
                            task.creator.points = F('points') + creator_points_val
                            task.creator.save(update_fields=['points'])
                            PointTransaction.objects.create(
                                user=task.creator,
                                change=creator_points_val,
                                reason=f'任务终止返还积分：{task.title}'
                            )
                        if worker_points_val > 0:
                            task.worker.points = F('points') + worker_points_val
                            task.worker.save(update_fields=['points'])
                            PointTransaction.objects.create(
                                user=task.worker,
                                change=worker_points_val,
                                reason=f'任务终止结算积分：{task.title}'
                            )

                        task.status = 'terminated'
                        task.terminate_creator_points = creator_points_val
                        task.terminate_worker_points = worker_points_val
                        task.terminated_at = now()
                        task.terminate_reject_reason = None
                    else:
                        if not reason:
                            return JsonResponse({'code': 400, 'message': '驳回终止需填写原因'})
                        task.status = 'accepted'
                        task.terminate_reject_reason = reason
                else:
                    return JsonResponse({'code': 400, 'message': '当前任务状态不支持该审核操作'})

                task.save()
                log_audit(
                    action='admin_handle_review',
                    actor=None,
                    target_type='task',
                    target_id=task.id,
                    detail=f'action={action}, reason={reason or ""}'
                )
            return JsonResponse({'code': 200, 'message': '审批操作已记录'})

        except Task.DoesNotExist:
            return JsonResponse({'code': 404, 'message': '找不到该任务'})


@csrf_exempt
def get_admin_all_tasks(request):
    """管理员获取所有参与过审核或仲裁的任务"""
    auto_finish_overdue_submitted_tasks()

    # 排除掉还在“招募中”或“进行中”且未发生争议的任务，只看跟管理员有关的
    tasks = Task.objects.exclude(status='accepted').order_by('-created_at')

    data = []
    for t in tasks:
        data.append({
            'id': t.id,
            'title': t.title,
            'content': t.content,
            'status': t.status,  # 原始状态
            'creator': t.creator.username,
            'category': t.category,
            'audit_reason': t.audit_reason,  # 初审理由
            'intervention_decision': t.intervention_decision,  # 复审理由
            'created_at': t.created_at.strftime('%Y-%m-%d %H:%M')
        })
    return JsonResponse({'code': 200, 'tasks': data})

from math import radians, cos, sin, asin, sqrt

def haversine_distance(lat1, lon1, lat2, lon2):
    """
    计算两个经纬度之间的地球表面距离（单位：公里）
    """
    # 将十进制度数转化为弧度
    lon1, lat1, lon2, lat2 = map(radians, [float(lon1), float(lat1), float(lon2), float(lat2)])

    # Haversine 公式
    dlon = lon2 - lon1
    dlat = lat2 - lat1
    a = sin(dlat/2)**2 + cos(lat1) * cos(lat2) * sin(dlon/2)**2
    c = 2 * asin(sqrt(a))
    r = 6371 # 地球平均半径，单位为公里
    return c * r



def get_nearby_tasks(user_lat, user_lng, radius=3):
    """
    获取指定半径（公里）内的任务
    """
    # 这是一个基础的过滤逻辑，实际高性能场景建议使用 PostGIS
    all_tasks = CommunityTask.objects.filter(is_completed=False)
    nearby_tasks = []

    for task in all_tasks:
        # 计算距离 (单位: km)
        dist = haversine_distance(user_lat, user_lng, task.latitude, task.longitude)
        if dist <= radius:
            nearby_tasks.append(task)
    return nearby_tasks


@require_POST
@transaction.atomic
def complete_task(request):
    """
    确认完成任务：将积分从系统/冻结状态转入接单人账户
    """
    try:
        data = json.loads(request.body)
        task_id = data.get('task_id')

        # 1. 获取任务，并锁定该行数据防止并发冲突
        # select_for_update() 确保在事务结束前，其他人不能修改这个任务
        task = Task.objects.select_for_update().get(id=task_id)

        if task.status == 'finished':
            return JsonResponse({'status': 'error', 'message': '任务已完成，请勿重复操作'}, status=400)

        if task.status != 'submitted':
            return JsonResponse({'status': 'error', 'message': '当前任务状态不可确认完成'}, status=400)

        if not task.worker:
            return JsonResponse({'status': 'error', 'message': '该任务尚未有人接单，无法完成'}, status=400)

        # 2. 给接单者增加积分
        worker = task.worker
        worker.points = F('points') + task.reward_points
        worker.save(update_fields=['points'])

        # 3. 记录积分流水
        PointTransaction.objects.create(
            user=worker,
            change=task.reward_points,
            reason=f"完成互助任务: {task.title}"
        )

        # 4. 修改任务状态
        task.status = 'finished'
        task.save(update_fields=['status', 'updated_at'])

        return JsonResponse({
            'status': 'success',
            'message': f'任务已确认完成，{task.reward_points} 积分已发放至接单人账户'
        })

    except Task.DoesNotExist:
        return JsonResponse({'status': 'error', 'message': '找不到该任务'}, status=404)
    except Exception as e:
        # transaction.atomic 会在这里捕获异常并自动回滚所有数据库操作
        return JsonResponse({'status': 'error', 'message': str(e)}, status=500)

print("views loaded")


# Create your views here.
