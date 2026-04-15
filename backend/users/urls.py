from django.urls import path

from users.views import login, register, user_list, get_posts, create_post, update_post, apply_expert, \
    get_my_application, approve_expert, reject_expert, application_list, get_user_info, my_application_history, \
    all_pending_posts, review_post, get_post_history, get_audit_history, get_tasks, create_task, accept_task, \
    get_my_tasks, submit_task, abandon_task, finish_task, get_audit_tasks, admin_handle_review, get_admin_all_tasks, \
    complete_task, get_announcements, create_announcement, delete_announcement, update_user_points, update_task, \
    update_announcement, \
    delete_task, request_terminate_task, respond_terminate_task, finish_task_with_settlement, create_task_quote, \
    get_task_quotes, choose_task_quote, create_task_review, get_provider_reviews, blacklist_user, unblacklist_user, \
    submit_blacklist_appeal, list_blacklist_appeals, handle_blacklist_appeal, get_audit_logs, admin_dashboard_stats, \
    my_point_transactions, admin_point_transactions, export_admin_point_transactions_csv, admin_backfill_task_locations, list_verified_providers, \
    get_provider_profile, update_provider_profile, geocode_debug
from users.views import get_chat_messages, send_chat_message

urlpatterns = [
    path('login/', login),  #登录
    path('register/', register),    #注册
    path('users/', user_list),  # 新增用户列表
    path('update_user_points/', update_user_points),
    path('admin_point_transactions/', admin_point_transactions),
    path('admin_point_transactions/export_csv/', export_admin_point_transactions_csv),
    path('posts/', get_posts),
    path('create_post/', create_post),
    path('update_post/', update_post),
    path('apply/', apply_expert),   #申请邻里达人
    path('my_application/', get_my_application),    #查询邻里达人申请状态
    path('approve/', approve_expert),
    path('reject/', reject_expert),
    path('audit_history/', get_audit_history),
    path('all_pending_posts/', all_pending_posts), # 对应前端的 fetchAuditPosts
    path('review_post/', review_post),           # 对应前端的审批操作
    path('post_history/', get_post_history),
    path('announcements/', get_announcements),
    path('create_announcement/', create_announcement),
    path('delete_announcement/', delete_announcement),
    path('update_announcement/', update_announcement),
    path('chat/messages/', get_chat_messages),
    path('chat/send/', send_chat_message),
    path('applications/', application_list),    #获取申请列表
    path('user_info/', get_user_info), #获取当前用户role
    path('my_application_history/', my_application_history),    #获取历史用户信息
    path('my_point_transactions/', my_point_transactions),
    path('get_tasks/', get_tasks),
    path('create_task/', create_task),
    path('accept_task/', accept_task),
    path('my_tasks/',get_my_tasks),
    path('submit_task/', submit_task),
    path('abandon_task/', abandon_task),
    path('finish_task/',finish_task),
    path('finish_task_with_settlement/', finish_task_with_settlement),
    path('update_task/', update_task),
    path('delete_task/', delete_task),
    path('task_quote/create/', create_task_quote),
    path('task_quote/list/', get_task_quotes),
    path('task_quote/choose/', choose_task_quote),
    path('task_review/create/', create_task_review),
    path('task_review/provider/', get_provider_reviews),
    path('providers/', list_verified_providers),
    path('provider_profile/', get_provider_profile),
    path('provider_profile/update/', update_provider_profile),
    path('request_terminate_task/', request_terminate_task),
    path('respond_terminate_task/', respond_terminate_task),
    path('blacklist_user/', blacklist_user),
    path('unblacklist_user/', unblacklist_user),
    path('blacklist_appeal/submit/', submit_blacklist_appeal),
    path('blacklist_appeal/list/', list_blacklist_appeals),
    path('blacklist_appeal/handle/', handle_blacklist_appeal),
    path('audit_logs/', get_audit_logs),
    path('admin_dashboard_stats/', admin_dashboard_stats),
    path('admin_backfill_task_locations/', admin_backfill_task_locations),
    path('get_audit_tasks/', get_audit_tasks),
    path('admin_handle_review/', admin_handle_review),
    path('get_admin_all_tasks/', get_admin_all_tasks),
    path('complete_task/',complete_task),
    path('geocode_debug/', geocode_debug),
]
