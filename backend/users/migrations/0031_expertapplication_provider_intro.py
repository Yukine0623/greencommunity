from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('users', '0030_provider_profile_and_task_assignee'),
    ]

    operations = [
        migrations.AddField(
            model_name='expertapplication',
            name='provider_intro',
            field=models.TextField(blank=True, null=True, verbose_name='认证服务者简介'),
        ),
    ]
