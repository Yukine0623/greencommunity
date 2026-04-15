from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('users', '0026_alter_task_status_length'),
    ]

    operations = [
        migrations.AddField(
            model_name='expertapplication',
            name='apply_type',
            field=models.CharField(choices=[('expert', '邻里达人'), ('provider', '认证服务者')], default='expert', max_length=20),
        ),
        migrations.AddField(
            model_name='expertapplication',
            name='pricing_note',
            field=models.CharField(blank=True, max_length=120, null=True, verbose_name='定价参考'),
        ),
        migrations.AddField(
            model_name='expertapplication',
            name='service_scope',
            field=models.CharField(blank=True, max_length=100, null=True, verbose_name='服务范围'),
        ),
    ]

