from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('users', '0024_merge_20260415_1150'),
    ]

    operations = [
        migrations.AddField(
            model_name='task',
            name='terminate_agreed_by',
            field=models.CharField(blank=True, max_length=50, null=True, verbose_name='终止申请同意人'),
        ),
        migrations.AddField(
            model_name='task',
            name='terminate_creator_points',
            field=models.IntegerField(blank=True, null=True, verbose_name='终止结算发单方积分'),
        ),
        migrations.AddField(
            model_name='task',
            name='terminate_reason',
            field=models.TextField(blank=True, null=True, verbose_name='终止申请原因'),
        ),
        migrations.AddField(
            model_name='task',
            name='terminate_reject_reason',
            field=models.TextField(blank=True, null=True, verbose_name='终止申请拒绝/驳回原因'),
        ),
        migrations.AddField(
            model_name='task',
            name='terminate_requested_by',
            field=models.CharField(blank=True, max_length=50, null=True, verbose_name='终止申请发起人'),
        ),
        migrations.AddField(
            model_name='task',
            name='terminate_worker_points',
            field=models.IntegerField(blank=True, null=True, verbose_name='终止结算接单方积分'),
        ),
        migrations.AddField(
            model_name='task',
            name='terminated_at',
            field=models.DateTimeField(blank=True, null=True, verbose_name='终止时间'),
        ),
    ]

