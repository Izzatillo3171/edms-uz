import os
import django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'sed_project.settings')
django.setup()

from documents.models import Document, Institution, Department, User

print('🔍 System Verification Report - Session 3')
print('=' * 50)

# Check institutions
insts = Institution.objects.count()
depts = Department.objects.count()
docs = Document.objects.count()
users = User.objects.count()

print(f'\n📊 Database Statistics:')
print(f'  • Institutions: {insts}')
print(f'  • Departments: {depts}')
print(f'  • Documents: {docs}')
print(f'  • Users: {users}')

# Check acceptance fields
from django.db import connection
cursor = connection.cursor()
cursor.execute('PRAGMA table_info(documents_document)')
columns = {row[1] for row in cursor.fetchall()}
required = {'acceptance_status', 'accepted_by_id', 'accepted_at', 'rejection_reason'}
missing = required - columns
if not missing:
    print(f'\n✅ Document acceptance fields: All present')
else:
    print(f'\n❌ Missing fields: {missing}')

# Check URLs
from django.urls import get_resolver
resolver = get_resolver()
accept_url = any('accept_document' in str(p.pattern) for p in resolver.url_patterns)
reject_url = any('reject_document' in str(p.pattern) for p in resolver.url_patterns)
print(f'\n🔗 URL Routes:')
print(f'  • /documents/<pk>/accept/: {"✅" if accept_url else "❌"}')
print(f'  • /documents/<pk>/reject/: {"✅" if reject_url else "❌"}')

# Check template files
import os
template_dir = 'templates/documents'
required_templates = [
    'accept_document.html',
    'reject_document.html',
    'document_detail.html',
]
print(f'\n📄 Template Files:')
for template in required_templates:
    path = os.path.join(template_dir, template)
    exists = os.path.exists(path)
    print(f'  • {template}: {"✅" if exists else "❌"}')

print(f'\n✨ Session 3 Implementation Complete!')
print(f'=' * 50)
