from django.db import migrations, models

class Migration(migrations.Migration):

    dependencies = [
        ('core', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='certificado',
            name='archivo',
            field=models.FileField(default='', upload_to='certificados/emitidos/'),
            preserve_default=False,
        ),
    ]