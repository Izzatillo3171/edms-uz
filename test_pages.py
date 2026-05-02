import os
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'sed_project.settings')

import django
django.setup()

from django.test import Client

# Use Django test client to avoid CSRF issues
client = Client()

# Try logging in
print("Testing login...")
resp = client.post('/login/', {'username': 'head1', 'password': 'head123'}, follow=True)
print('Login response status:', resp.status_code)
print('User authenticated:', '_auth_user_id' in client.session)

# Try dashboard
print("\nTesting dashboard...")
dashboard = client.get('/dashboard/', follow=True)
print('Dashboard status:', dashboard.status_code)
content = dashboard.content.decode('utf-8', errors='ignore')
print('Dashboard has heading:', 'Главная' in content or 'dashboard' in content.lower())
if dashboard.status_code != 200:
    print('First 500 chars:', content[:500])

# Try documents
print("\nTesting documents...")
docs = client.get('/documents/', follow=True)
print('Documents status:', docs.status_code)
docs_content = docs.content.decode('utf-8', errors='ignore')
print('Documents has content:', 'Документы' in docs_content)

# Try appeal form
print("\nTesting appeal form...")
appeal = client.get('/appeal/', follow=True)
print('Appeal status:', appeal.status_code)

print("\n✅ All main pages tested!")
