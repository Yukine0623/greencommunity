from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('users', '0022_chatmessage_task'),
    ]

    operations = [
        migrations.AddField(
            model_name='task',
            name='accepted_at',
            field=models.DateTimeField(blank=True, null=True, verbose_name='接单时间'),
        ),
        migrations.AddField(
            model_name='task',
            name='submitted_at',
            field=models.DateTimeField(blank=True, null=True, verbose_name='提交成果时间'),
        ),
    ]
