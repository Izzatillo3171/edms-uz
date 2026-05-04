import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'sed_project.settings')
django.setup()

from documents.models import User, Department

# Get or create a department
dept, _ = Department.objects.get_or_create(
    name='Тестовый отдел',
    defaults={'description': 'Отдел для тестирования'}
)

# Create or update manager user
manager, created = User.objects.get_or_create(
    username='manager_test',
    defaults={
        'email': 'manager@test.com',
        'full_name': 'Test Manager',
        'role': 'head',
        'department': dept
    }
)

if created:
    manager.set_password('ManagerTest123')
    manager.save()
    print(f"Manager created: {manager.username}")
else:
    manager.role = 'head'
    manager.set_password('ManagerTest123')
    manager.save()
    print(f"Manager updated: {manager.username}")