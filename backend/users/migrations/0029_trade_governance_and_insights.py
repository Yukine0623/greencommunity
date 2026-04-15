from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('users', '0028_user_is_expert_user_is_provider'),
    ]

    operations = [
        migrations.AddField(
            model_name='post',
            name='risk_flagged',
            field=models.BooleanField(default=False),
        ),
        migrations.AddField(
            model_name='post',
            name='risk_keywords',
            field=models.CharField(blank=True, max_length=255, null=True),
        ),
        migrations.AddField(
            model_name='task',
            name='refund_points',
            field=models.IntegerField(blank=True, null=True, verbose_name='退款给发单方积分'),
        ),
        migrations.AddField(
            model_name='task',
            name='risk_flagged',
            field=models.BooleanField(default=False, verbose_name='是否触发风控'),
        ),
        migrations.AddField(
            model_name='task',
            name='risk_keywords',
            field=models.CharField(blank=True, max_length=255, null=True, verbose_name='触发风控关键词'),
        ),
        migrations.AddField(
            model_name='task',
            name='settlement_points',
            field=models.IntegerField(blank=True, null=True, verbose_name='实际结算给接单方积分'),
        ),
        migrations.AddField(
            model_name='user',
            name='blacklist_reason',
            field=models.TextField(blank=True, null=True, verbose_name='拉黑原因'),
        ),
        migrations.AddField(
            model_name='user',
            name='blacklist_until',
            field=models.DateTimeField(blank=True, null=True, verbose_name='拉黑截止时间'),
        ),
        migrations.AddField(
            model_name='user',
            name='is_blacklisted',
            field=models.BooleanField(default=False, verbose_name='是否黑名单'),
        ),
        migrations.CreateModel(
            name='AuditLog',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('action', models.CharField(max_length=120)),
                ('target_type', models.CharField(blank=True, max_length=50, null=True)),
                ('target_id', models.CharField(blank=True, max_length=50, null=True)),
                ('detail', models.TextField(blank=True, null=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('actor', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='audit_logs', to='users.user')),
            ],
            options={'ordering': ['-created_at']},
        ),
        migrations.CreateModel(
            name='BlacklistAppeal',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('reason', models.TextField()),
                ('status', models.CharField(choices=[('pending', '待处理'), ('approved', '通过'), ('rejected', '拒绝')], default='pending', max_length=20)),
                ('review_note', models.TextField(blank=True, null=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('reviewed_at', models.DateTimeField(blank=True, null=True)),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='blacklist_appeals', to='users.user')),
            ],
            options={'ordering': ['-created_at']},
        ),
        migrations.CreateModel(
            name='TaskQuote',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('amount_points', models.IntegerField(default=0, verbose_name='报价积分')),
                ('message', models.CharField(blank=True, max_length=255, null=True, verbose_name='报价说明')),
                ('status', models.CharField(choices=[('pending', '待选择'), ('selected', '已中选'), ('rejected', '未中选')], default='pending', max_length=20)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('quoter', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='task_quotes', to='users.user')),
                ('task', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='quotes', to='users.task')),
            ],
            options={'ordering': ['created_at'], 'unique_together': {('task', 'quoter')}},
        ),
        migrations.CreateModel(
            name='TaskReview',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('rating', models.PositiveSmallIntegerField(default=5)),
                ('comment', models.TextField(blank=True, null=True)),
                ('tags', models.CharField(blank=True, max_length=255, null=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('reviewee', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='received_task_reviews', to='users.user')),
                ('reviewer', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='given_task_reviews', to='users.user')),
                ('task', models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, related_name='review', to='users.task')),
            ],
            options={'ordering': ['-created_at']},
        ),
    ]
