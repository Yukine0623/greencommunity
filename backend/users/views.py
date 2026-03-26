from django.views.decorators.csrf import csrf_exempt
from django.utils.timezone import localtime
from django.http import JsonResponse
from .models import User, Post , ExpertApplication
import json


# 登录接口
@csrf_exempt
def login(request):
    if request.method == 'POST':
        data = json.loads(request.body)

        username = data.get('username')
        password = data.get('password')

        try:
            user = User.objects.get(username=username)

            if user.password == password:
                return JsonResponse({
                    'code': 200,
                    'message': '登录成功'
                })
            else:
                return JsonResponse({
                    'code': 400,
                    'message': '密码错误'
                })

        except User.DoesNotExist:
            return JsonResponse({
                'code': 400,
                'message': '用户不存在'
            })

    return JsonResponse({'code': 405, 'message': '只支持POST'})

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

        Post.objects.create(
            title=title,
            content=content,
            author=author
        )

        return JsonResponse({
            'code': 200,
            'message': '发布成功'
        })

    return JsonResponse({'code': 405, 'message': '只支持POST'})

#获取帖子列表
def post_list(request):
    posts = Post.objects.all().order_by('-created_at')
    data = []
    for post in posts:
        data.append({
            'id': post.id,
            'title': post.title,
            'content': post.content,
            'author': post.author,
            'created_at': localtime(post.created_at).strftime('%Y-%m-%d %H:%M:%S')
        })
    return JsonResponse({'code': 200, 'posts': data})

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

#管理员审核接口
@csrf_exempt
def approve_expert(request):
    if request.method == 'POST':
        data = json.loads(request.body)

        username = data.get('username')

        try:
            app = ExpertApplication.objects.get(username=username, status='pending')
            app.status = 'approved'
            app.save()

            user = User.objects.get(username=username)
            user.role = 'expert'
            user.save()

            return JsonResponse({
                'code': 200,
                'message': '审核通过'
            })

        except ExpertApplication.DoesNotExist:
            return JsonResponse({
                'code': 400,
                'message': '没有找到申请'
            })

    return JsonResponse({'code': 405})

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

print("views loaded")
from django.shortcuts import render

# Create your views here.
