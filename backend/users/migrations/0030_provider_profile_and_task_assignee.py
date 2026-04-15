from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('users', '0029_trade_governance_and_insights'),
    ]

    operations = [
        migrations.AddField(
            model_name='expertapplication',
            name='provider_price_range',
            field=models.CharField(blank=True, max_length=120, null=True, verbose_name='认证服务者价格区间'),
        ),
        migrations.AddField(
            model_name='expertapplication',
            name='provider_service_directions',
            field=models.CharField(blank=True, max_length=255, null=True, verbose_name='认证服务者服务方向标签'),
        ),
        migrations.AddField(
            model_name='expertapplication',
            name='provider_service_times',
            field=models.CharField(blank=True, max_length=120, null=True, verbose_name='认证服务者服务时间标签'),
        ),
        migrations.AddField(
            model_name='task',
            name='assignee_type',
            field=models.CharField(choices=[('any', '不指定'), ('expert', '邻里达人'), ('provider', '认证服务者')], default='any', max_length=20, verbose_name='指定接单身份'),
        ),
        migrations.AddField(
            model_name='task',
            name='invited_provider',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='provider_invited_tasks', to='users.user', verbose_name='定向邀约认证服务者'),
        ),
    ]
