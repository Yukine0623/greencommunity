# seed.py
import os
import django
import sys
import random
from pathlib import Path

# 🚀 第一步：获取当前脚本所在目录的上一级（即项目根目录）
# Path(__file__).resolve() 是当前文件的绝对路径
# .parent.parent 就是往上跳两级，到达包含 manage.py 的那个目录
BASE_DIR = Path(__file__).resolve().parent.parent

# 🚀 第二步：把根目录添加到 Python 的搜索路径中
sys.path.append(str(BASE_DIR))

# 🚀 第三步：设置环境变量（保持不变，因为它现在能找到 backend 文件夹了）
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'backend.settings')

# 🚀 第四步：启动 Django
django.setup()

from users.models import Task, User


def create_test_data():
    print("开始生成测试数据...")

    # 1. 获取或创建测试用户（密码都是 123456）
    # 注意：如果你的 User 模型有自定义字段，请在此补充
    admin, _ = User.objects.get_or_create(username='admin_test', defaults={'role': 'admin'})
    admin.password = '123456'
    admin.save()

    requester, _ = User.objects.get_or_create(username='user_test', defaults={'role': 'user'})
    requester.password = '123456'
    requester.save()

    expert, _ = User.objects.get_or_create(username='expert_test', defaults={'role': 'expert'})
    expert.password = '123456'
    expert.save()

    # 2. 定义各种状态的任务场景
    task_scenarios = [
        {'title': '帮买午饭', 'status': 'auditing', 'category': 'errand'},
        {'title': '宿舍水龙头漏水', 'status': 'pending', 'category': 'repair'},
        {'title': '楼下喂小狗', 'status': 'accepted', 'category': 'pet', 'worker': expert},
        {'title': '翻译英语文献', 'status': 'submitted', 'category': 'other', 'worker': expert,
         'result_desc': '已经翻译完成，请查收附件。'},
        {'title': '代取快递结果丢了', 'status': 'intervention', 'category': 'errand', 'worker': expert,
         'result_desc': '快递站关门了，我放门口了。'},
    ]

    for item in task_scenarios:
        Task.objects.create(
            title=item['title'],
            content=f"这是关于 {item['title']} 的详细描述内容，用于联调测试。",
            status=item['status'],
            category=item['category'],
            creator=requester,
            worker=item.get('worker'),
            result_desc=item.get('result_desc', ''),
            reward_points=random.choice([10, 20, 50])
        )

    print(f"✅ 成功！已创建 {len(task_scenarios)} 条不同状态的任务。")


if __name__ == '__main__':
    create_test_data()
