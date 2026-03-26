from django.urls import path
from .views import login,register,user_list,create_post,post_list,apply_expert,approve_expert,application_list

urlpatterns = [
    path('login/', login),
    path('register/', register),
    path('users/', user_list),  # 新增用户列表接口
    path('post/create/', create_post),   # 发帖
    path('post/list/', post_list),       # 获取帖子
    path('apply/', apply_expert),   #申请邻里达人
    path('approve/', approve_expert),  #管理员审核邻里达人
    path('applications/', application_list),
]