from django.db import migrations, models
import django.core.validators

class Migration(migrations.Migration):

    dependencies = [
        ('core', '0006_orderitem'),  # Make sure this matches your last migration
    ]

    operations = [
        migrations.CreateModel(
            name='Coupon',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('code', models.CharField(max_length=50, unique=True)),
                ('discount_type', models.CharField(choices=[('percentage', 'Percentage'), ('fixed', 'Fixed Amount')], max_length=10)),
                ('discount_value', models.DecimalField(decimal_places=2, max_digits=10, validators=[django.core.validators.MinValueValidator(0)])),
                ('minimum_purchase', models.DecimalField(decimal_places=2, default=0, max_digits=10)),
                ('valid_from', models.DateTimeField()),
                ('valid_to', models.DateTimeField()),
                ('active', models.BooleanField(default=True)),
                ('usage_limit', models.IntegerField(default=0)),
                ('times_used', models.IntegerField(default=0)),
            ],
        ),
    ]
