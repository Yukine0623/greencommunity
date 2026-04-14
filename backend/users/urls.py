from django.urls import path

from users.views import login, register, user_list, get_posts, create_post, update_post, apply_expert, \
    get_my_application, approve_expert, reject_expert, application_list, get_user_info, my_application_history, \
    all_pending_posts, review_post, get_post_history, get_audit_history, get_tasks, create_task, accept_task, \
    get_my_tasks, submit_task, abandon_task, finish_task, get_audit_tasks, admin_handle_review, get_admin_all_tasks

urlpatterns = [
    path('login/', login),  #登录
    path('register/', register),    #注册
    path('users/', user_list),  # 新增用户列表
    path('posts/', get_posts),
    path('create_post/', create_post),
    path('update_post/', update_post),
    path('apply/', apply_expert),   #申请邻里达人
    path('my_application/', get_my_application),    #查询邻里达人申请状态
    path('audit_history/', get_audit_history),
    path('all_pending_posts/', all_pending_posts), # 对应前端的 fetchAuditPosts
    path('review_post/', review_post),           # 对应前端的审批操作
    path('post_history/', get_post_history),
    path('applications/', application_list),    #获取申请列表
    path('user_info/', get_user_info), #获取当前用户role
    path('my_application_history/', my_application_history),    #获取历史用户信息
    path('get_tasks/', get_tasks),
    path('create_task/', create_task),
    path('accept_task/', accept_task),
    path('my_tasks/',get_my_tasks),
    path('submit_task/', submit_task),
    path('abandon_task/', abandon_task),
    path('finish_task/',finish_task),
    path('get_audit_tasks/', get_audit_tasks),
    path('admin_handle_review/', admin_handle_review),
    path('get_admin_all_tasks/', get_admin_all_tasks),
]
