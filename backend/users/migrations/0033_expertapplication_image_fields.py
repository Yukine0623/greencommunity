from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('users', '0032_merge_20260416_0001'),
    ]

    operations = [
        migrations.AddField(
            model_name='expertapplication',
            name='application_image_data',
            field=models.TextField(blank=True, null=True, verbose_name='申请附件图片Base64'),
        ),
        migrations.AddField(
            model_name='expertapplication',
            name='application_image_name',
            field=models.CharField(blank=True, max_length=255, null=True, verbose_name='申请附件图片名'),
        ),
    ]
