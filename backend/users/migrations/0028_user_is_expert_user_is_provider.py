from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('users', '0027_expertapplication_apply_type_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='user',
            name='is_expert',
            field=models.BooleanField(default=False, verbose_name='邻里达人资格'),
        ),
        migrations.AddField(
            model_name='user',
            name='is_provider',
            field=models.BooleanField(default=False, verbose_name='认证服务者资格'),
        ),
    ]

