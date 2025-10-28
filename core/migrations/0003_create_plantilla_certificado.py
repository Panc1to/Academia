from django.db import migrations, models

class Migration(migrations.Migration):

    dependencies = [
        ('core', '0002_add_certificado_archivo'),
    ]

    operations = [
        migrations.CreateModel(
            name='PlantillaCertificado',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('nombre', models.CharField(max_length=100)),
                ('descripcion', models.TextField(blank=True)),
                ('archivo', models.FileField(upload_to='certificados/plantillas/')),
                ('fecha_creacion', models.DateTimeField(auto_now_add=True)),
            ],
            options={
                'ordering': ['-fecha_creacion'],
            },
        ),
    ]