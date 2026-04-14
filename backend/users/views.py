from django.db.models import Q
from django.views.decorators.csrf import csrf_exempt
from django.http import JsonResponse
from .models import User, Post, ExpertApplication, PostHistory,Task
from django.utils.timezone import now
from math import radians, cos, sin, asin, sqrt
from .models import CommunityTask

import json


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

        if user.password != password:
            return JsonResponse({'code': 401, 'message': '密码错误'})

        # 🔥 关键：返回 role
        return JsonResponse({
            'code': 200,
            'message': '登录成功',
            'role': user.role   # 👈 就是这里！！
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
            password=password
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
        user_data = [
            {
                'id': user.id,
                'username': user.username,
                'role': user.role,
                'phone': user.phone,
                'created_at': user.created_at.strftime('%Y-%m-%d %H:%M:%S')
            }
            for user in users
        ]
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
        Post.objects.create(
            title=data.get('title'),
            content=data.get('content'),
            author=data.get('author'),
            status='pending' # 初始状态必须是待审核
        )
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

    post.title = data.get('title')
    post.content = data.get('content')
    post.status = 'pending'
    post.reject_reason = None
    post.reviewed_at = None

    post.save()

    return JsonResponse({'message': '已重新提交审核'})


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
        reason = data.get('reason')

        # 参数校验
        if not username or not reason:
            return JsonResponse({
                'code': 400,
                'message': '参数不完整'
            })

        # 用户是否存在
        try:
            user = User.objects.get(username=username)
        except User.DoesNotExist:
            return JsonResponse({
                'code': 400,
                'message': '用户不存在'
            })

        # 是否已经是达人
        if user.role == '达人':
            return JsonResponse({
                'code': 400,
                'message': '你已经是邻里达人，无需申请'
            })

        # 是否已有未处理申请
        if ExpertApplication.objects.filter(username=username, status='pending').exists():
            return JsonResponse({
                'code': 400,
                'message': '你已经提交过申请，请等待审核'
            })

        # 创建申请
        ExpertApplication.objects.create(
            username=username,
            reason=reason,
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

        app = ExpertApplication.objects.filter(
            username=username
        ).order_by('-created_at').first()   #-created_at按时间倒序   .first取最新一条

        if not app:
            return JsonResponse({
                'code': 200,
                'status': 'none'   # 👈 没申请
            })

        return JsonResponse({
            'code': 200,
            'status': app.status,
            'reason': app.reason
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
        username = data.get('username')

        if not username:
            return JsonResponse({'code': 400, 'message': '缺少用户名'})

        # 找到待审核申请
        app = ExpertApplication.objects.filter(
            username=username,
            status='pending'
        ).first()

        if not app:
            return JsonResponse({'code': 404, 'message': '申请不存在或已处理'})

        # ✅ 修改申请状态
        app.status = 'approved'
        app.reviewed_at = now()
        app.save()

        # ✅ 同时把用户角色改成 expert
        user = User.objects.filter(username=username).first()
        if user:
            user.role = 'expert'
            user.save()

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
        username = data.get('username')
        reason = data.get('reason')

        if not username:
            return JsonResponse({'code': 400, 'message': '缺少用户名'})

        # 找到待审核申请
        app = ExpertApplication.objects.filter(
            username=username,
            status='pending'
        ).first()

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
            'reason': item.reason,
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

        return JsonResponse({
            'code': 200,
            'username': user.username,
            'role': user.role
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

    apps = ExpertApplication.objects.filter(
        username=username
    ).order_by('-created_at')

    result = []
    for item in apps:
        result.append({
            'id': item.id,
            'status': item.status,
            'created_at': item.created_at.strftime('%Y-%m-%d %H:%M:%S'),
            'reviewed_at': item.reviewed_at.strftime('%Y-%m-%d %H:%M:%S') if item.reviewed_at else None,
            'reject_reason': item.reject_reason
        })

    return JsonResponse({
        'code': 200,
        'data': result
    })


@csrf_exempt
def get_tasks(request):
    """获取所有待接单的任务"""
    # 只展示状态为 pending（招募中）的任务
    tasks = Task.objects.filter(status='pending').order_by('-created_at')
    task_list = []
    for t in tasks:
        task_list.append({
            'id': t.id,
            'title': t.title,
            'category': t.category,
            'content': t.content,
            'creator': t.creator.username,
            'created_at': t.created_at.strftime('%Y-%m-%d %H:%M')
        })
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

            # 3. 🚀 修复跳过审核的关键：在这里强制设为 'auditing'
            new_task = Task.objects.create(
                title=data.get('title'),
                content=data.get('content'),
                category=data.get('category'),
                reward=int(data.get('reward', 10)),  # 确保是数字
                creator=user,  # 直接关联用户对象
                status='auditing'  # 🔒 锁死状态！哪怕前端传 pending，这里也存 auditing
            )

            return JsonResponse({
                'code': 200,
                'message': '提交成功！任务已进入待审核队列，通过后将发布到市场。'
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

        # 更新任务状态和接单人
        task.worker = worker_user
        task.status = 'accepted'
        task.save()
        return JsonResponse({'code': 200, 'message': '接单成功！'})


@csrf_exempt
def get_my_tasks(request):
    """获取与当前用户相关的任务"""
    username = request.GET.get('username')
    user = User.objects.get(username=username)

    # 我发布的
    my_posted = Task.objects.filter(creator=user).order_by('-created_at')
    # 我接手的
    my_accepted = Task.objects.filter(worker=user).order_by('-created_at')

    # 序列化逻辑（建议封装成函数，这里为了演示直接写）
    def serialize(queryset):
        return [{
            'id': t.id,
            'title': t.title,
            'status': t.status,
            'worker': t.worker.username if t.worker else None,
            'creator': t.creator.username,
            'content': t.content,
            'category': t.category,
            'created_at': t.created_at.strftime('%Y-%m-%d %H:%M')
        } for t in queryset]

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
            task.save()
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

            task.save()
            return JsonResponse({'code': 200, 'message': '已放弃任务，任务已重回市场'})
        except Task.DoesNotExist:
            return JsonResponse({'code': 404, 'message': '任务不存在'})

# users/views.py

@csrf_exempt
def finish_task(request):
    """发布人确认任务已圆满完成"""
    if request.method == 'POST':
        data = json.loads(request.body)
        try:
            task = Task.objects.get(id=data.get('task_id'))
            # 🚀 将状态改为：已完成
            task.status = 'finished'
            task.save()
            return JsonResponse({'code': 200, 'message': '任务已完结，感谢您的互助！'})
        except Task.DoesNotExist:
            return JsonResponse({'code': 404, 'message': '任务不存在'})


# users/views.py
import json
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from .models import Task, User


@csrf_exempt
def get_audit_tasks(request):
    """管理员专用：获取待初审(auditing)和待复审(intervention)的任务"""
    # 只要是需要管理员操心的，全查出来
    tasks = Task.objects.filter(status__in=['auditing', 'intervention']).order_by('-created_at')

    data = []
    for t in tasks:
        data.append({
            'id': t.id,
            'title': t.title,
            'content': t.content,
            'status': t.status,
            'creator': t.creator.username,
            'worker': t.worker.username if t.worker else "暂无",
            'result_desc': t.result_desc,  # 达人提交的成果描述
            'created_at': t.created_at.strftime('%Y-%m-%d %H:%M')
        })
    return JsonResponse({'code': 200, 'tasks': data})


@csrf_exempt
def admin_handle_review(request):
    """管理员审批接口：处理初审和复审"""
    if request.method == 'POST':
        data = json.loads(request.body)
        task_id = data.get('taskId')
        action = data.get('action')  # 'approve' 或 'reject'
        reason = data.get('reason')  # 理由/评语

        try:
            task = Task.objects.get(id=task_id)

            # --- 情况 A：初审阶段 (auditing) ---
            if task.status == 'auditing':
                if action == 'approve':
                    task.status = 'pending'  # 审核通过，进入市场
                    task.audit_reason = "审核通过"
                else:
                    if not reason: return JsonResponse({'code': 400, 'message': '拒绝发布必须填写原因'})
                    task.status = 'rejected'  # 拒绝发布
                    task.audit_reason = reason

            # --- 情况 B：复审/仲裁阶段 (intervention) ---
            elif task.status == 'intervention':
                if not reason: return JsonResponse({'code': 400, 'message': '仲裁必须填写判定理由'})

                task.intervention_decision = reason
                if action == 'approve':
                    # 判定达人胜诉：强制结项，结算积分
                    task.status = 'finished'
                    # 这里可以顺手写积分逻辑：
                    # task.worker.points += 10; task.worker.save()
                else:
                    # 判定用户胜诉：任务回退到招募中，或直接撤销
                    task.status = 'pending'
                    task.worker = None  # 踢掉当前的接单达人

            task.save()
            return JsonResponse({'code': 200, 'message': '审批操作已记录'})

        except Task.DoesNotExist:
            return JsonResponse({'code': 404, 'message': '找不到该任务'})


@csrf_exempt
def get_admin_all_tasks(request):
    """管理员获取所有参与过审核或仲裁的任务"""
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


print("views loaded")


# Create your views here.
