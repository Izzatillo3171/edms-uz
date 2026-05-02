from django.core.management.base import BaseCommand
from django.utils import timezone
from documents.models import User, Department, Document, Resolution, Notification
from datetime import timedelta


class Command(BaseCommand):
    help = 'Create sample data for testing the document management system'

    def handle(self, *args, **options):
        self.stdout.write('Creating sample data...')
        
        # Create departments
        dept_it, _ = Department.objects.get_or_create(
            code='IT',
            defaults={'name': 'IT Department', 'description': 'Information Technology'}
        )
        dept_hr, _ = Department.objects.get_or_create(
            code='HR',
            defaults={'name': 'Human Resources', 'description': 'Human Resources Department'}
        )
        dept_finance, _ = Department.objects.get_or_create(
            code='FIN',
            defaults={'name': 'Finance', 'description': 'Finance Department'}
        )
        
        self.stdout.write(self.style.SUCCESS('✓ Departments created'))
        
        # Create test users
        users = {}
        
        # Secretary
        secretary, _ = User.objects.get_or_create(
            username='secretary1',
            defaults={
                'email': 'secretary@example.com',
                'full_name': 'Секретарь Первый',
                'role': 'secretary',
                'department': dept_it,
                'phone': '+998901234567',
            }
        )
        if not secretary.password or secretary.password == '':
            secretary.set_password('secretary123')
            secretary.save()
        users['secretary'] = secretary
        
        # Head
        head, _ = User.objects.get_or_create(
            username='head1',
            defaults={
                'email': 'head@example.com',
                'full_name': 'Руководитель Отдела',
                'role': 'head',
                'department': dept_it,
                'phone': '+998901234568',
            }
        )
        if not head.password or head.password == '':
            head.set_password('head123')
            head.save()
        users['head'] = head
        
        # Executor
        executor, _ = User.objects.get_or_create(
            username='executor1',
            defaults={
                'email': 'executor@example.com',
                'full_name': 'Исполнитель Задач',
                'role': 'executor',
                'department': dept_it,
                'phone': '+998901234569',
            }
        )
        if not executor.password or executor.password == '':
            executor.set_password('executor123')
            executor.save()
        users['executor'] = executor
        
        # Citizen
        citizen, _ = User.objects.get_or_create(
            username='citizen1',
            defaults={
                'email': 'citizen@example.com',
                'full_name': 'Гражданин Узбекистана',
                'role': 'citizen',
                'phone': '+998901234570',
            }
        )
        if not citizen.password or citizen.password == '':
            citizen.set_password('citizen123')
            citizen.save()
        users['citizen'] = citizen
        
        self.stdout.write(self.style.SUCCESS('✓ Test users created'))
        
        # Create sample documents
        doc1, _ = Document.objects.get_or_create(
            reg_number='IN-20260425-0001',
            defaults={
                'title': 'Входящий документ о согласовании бюджета',
                'doc_type': 'IN',
                'content': 'Содержание входящего документа...',
                'sender_org': 'Министерство финансов',
                'sender_person': 'Иван Петров',
                'author': secretary,
                'status': 'REGISTERED',
                'created_at': timezone.now(),
            }
        )
        
        doc2, _ = Document.objects.get_or_create(
            reg_number='APP-20260425-0001',
            defaults={
                'title': 'Обращение о получении справки',
                'doc_type': 'APP',
                'content': 'Прошу выдать справку об отсутствии задолженности...',
                'author': citizen,
                'status': 'REGISTERED',
                'deadline': timezone.now().date() + timedelta(days=15),
                'created_at': timezone.now(),
            }
        )
        
        self.stdout.write(self.style.SUCCESS('✓ Sample documents created'))
        
        self.stdout.write(self.style.SUCCESS('Sample data created successfully!'))
        self.stdout.write('\nTest credentials:')
        self.stdout.write('- Secretary: secretary1 / secretary123')
        self.stdout.write('- Head: head1 / head123')
        self.stdout.write('- Executor: executor1 / executor123')
        self.stdout.write('- Citizen: citizen1 / citizen123')
        self.stdout.write('- Admin: admin / admin')
