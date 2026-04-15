from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('users', '0025_task_termination_fields'),
    ]

    operations = [
        migrations.AlterField(
            model_name='task',
            name='status',
            field=models.CharField(default='auditing', max_length=40),
        ),
    ]

