from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('users', '0021_chatmessage'),
    ]

    operations = [
        migrations.AddField(
            model_name='chatmessage',
            name='task',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='chat_messages', to='users.task'),
        ),
    ]
