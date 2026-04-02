from django.contrib import admin
from .models import Post

@admin.register(Post)
class PostAdmin(admin.ModelAdmin):
    # 后台列表显示哪些列
    list_display = ('title', 'author', 'status', 'created_at')
    # 哪些列可以直接在列表页点击修改
    list_editable = ('status',)
    # 搜索字段
    search_fields = ('title', 'author')
