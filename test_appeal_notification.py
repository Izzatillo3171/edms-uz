import os
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'sed_project.settings')

import django
django.setup()

from django.test import Client
from documents.models import Document, Notification, User, Department

# Get test user (responsible person)
try:
    recipient = User.objects.filter(role__in=['secretary', 'head', 'executor']).first()
    department = Department.objects.first()
    
    if not recipient or not department:
        print("❌ Error: No recipient user or department found. Create test data first.")
        print(f"   Recipients: {User.objects.filter(role__in=['secretary', 'head', 'executor']).count()}")
        print(f"   Departments: {Department.objects.count()}")
    else:
        client = Client()
        
        # Submit an appeal
        response = client.post('/appeal/', {
            'title': 'Тестовое обращение',
            'content': 'Это тестовое обращение для проверки уведомлений',
            'sender_person': 'Иван Иванов',
            'destination_org': 'МВД Узбекистана',
            'destination_department': department.id,
            'destination_person': recipient.id,
        }, follow=True)
        
        print(f"Response status: {response.status_code}")
        
        # Check if notification was created
        notification = Notification.objects.filter(
            user=recipient,
            notification_type='NEW_DOCUMENT'
        ).latest('created_at')
        
        if notification:
            print(f"✅ Notification created successfully!")
            print(f"   Title: {notification.title}")
            print(f"   Message: {notification.message}")
            print(f"   To: {notification.user.username}")
            print(f"   Document: {notification.document.reg_number}")
        else:
            print("❌ No notification found")
except Exception as e:
    print(f"❌ Error: {str(e)}")
    import traceback
    traceback.print_exc()
