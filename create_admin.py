import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'sed_project.settings')
django.setup()

from documents.models import User

# Create or update admin user
admin, created = User.objects.get_or_create(
    username='admin_test',
    defaults={
        'email': 'admin@test.com',
        'full_name': 'Test Admin',
        'role': 'admin'
    }
)

if created:
    admin.set_password('AdminTest123')
    admin.save()
    print(f"Admin created: {admin.username}")
else:
    admin.set_password('AdminTest123')
    admin.save()
    print(f"Admin updated: {admin.username}")
