from django.core.management.base import BaseCommand
from documents.models import Institution, Department


class Command(BaseCommand):
    help = 'Create sample government institutions and departments'

    def handle(self, *args, **options):
        institutions_data = [
            {
                'name': 'Министерство цифровых технологий',
                'institution_type': 'ministry',
                'code': 'MIN-CIFRA',
                'description': 'Ведомство, отвечающее за цифровую трансформацию',
            },
            {
                'name': 'Министерство внутренних дел',
                'institution_type': 'ministry',
                'code': 'MIN-MVD',
                'description': 'Ведомство внутренних дел Узбекистана',
            },
            {
                'name': 'Министерство здравоохранения',
                'institution_type': 'ministry',
                'code': 'MIN-HEALTH',
                'description': 'Ведомство здравоохранения Узбекистана',
            },
            {
                'name': 'Министерство образования',
                'institution_type': 'ministry',
                'code': 'MIN-EDU',
                'description': 'Министерство высшего образования, науки и инноваций',
            },
            {
                'name': 'Агентство государственных услуг',
                'institution_type': 'agency',
                'code': 'AGENCY-SERVICE',
                'description': 'Центр оказания государственных услуг',
            },
            {
                'name': 'Налоговый комитет',
                'institution_type': 'committee',
                'code': 'COMMITTEE-TAX',
                'description': 'Государственный налоговый комитет',
            },
        ]

        departments_data = [
            {
                'name': 'Канцелярия',
                'code': 'DEP-CHANCELLERY',
                'institution': 'MIN-CIFRA',
                'department_type': 'chancellery',
                'description': 'Департамент делопроизводства',
            },
            {
                'name': 'Отдел кадров',
                'code': 'DEP-HR',
                'institution': 'MIN-CIFRA',
                'department_type': 'hr',
                'description': 'Управление человеческими ресурсами',
            },
            {
                'name': 'Юридический отдел',
                'code': 'DEP-LEGAL',
                'institution': 'MIN-CIFRA',
                'department_type': 'legal',
                'description': 'Отдел правового обеспечения',
            },
            {
                'name': 'Финансовый отдел',
                'code': 'DEP-FINANCE',
                'institution': 'MIN-CIFRA',
                'department_type': 'finance',
                'description': 'Управление финансами и учета',
            },
            {
                'name': 'Отдел ИКТ',
                'code': 'DEP-IT',
                'institution': 'MIN-CIFRA',
                'department_type': 'it',
                'description': 'Управление информационных технологий',
            },
            {
                'name': 'Отдел по работе с обращениями',
                'code': 'DEP-APPEALS',
                'institution': 'MIN-CIFRA',
                'department_type': 'appeals',
                'description': 'Отдел по работе с обращениями физических и юридических лиц',
            },
            {
                'name': 'Пресс-служба',
                'code': 'DEP-PRESS',
                'institution': 'MIN-CIFRA',
                'department_type': 'press',
                'description': 'Управление по связям с общественностью',
            },
            {
                'name': 'Канцелярия',
                'code': 'DEP-CHANCELLERY-MVD',
                'institution': 'MIN-MVD',
                'department_type': 'chancellery',
                'description': 'Канцелярия МВД',
            },
            {
                'name': 'Отдел по работе с обращениями',
                'code': 'DEP-APPEALS-MVD',
                'institution': 'MIN-MVD',
                'department_type': 'appeals',
                'description': 'Виртуальная приемная МВД',
            },
        ]

        # Create institutions
        for inst_data in institutions_data:
            institution, created = Institution.objects.get_or_create(
                code=inst_data['code'],
                defaults={
                    'name': inst_data['name'],
                    'institution_type': inst_data['institution_type'],
                    'description': inst_data['description'],
                }
            )
            if created:
                self.stdout.write(
                    self.style.SUCCESS(f'Created institution: {institution.name}')
                )
            else:
                self.stdout.write(
                    self.style.WARNING(f'Institution already exists: {institution.name}')
                )

        # Create departments
        for dep_data in departments_data:
            try:
                institution = Institution.objects.get(code=dep_data['institution'])
                department, created = Department.objects.get_or_create(
                    code=dep_data['code'],
                    defaults={
                        'name': dep_data['name'],
                        'institution': institution,
                        'department_type': dep_data['department_type'],
                        'description': dep_data['description'],
                    }
                )
                if created:
                    self.stdout.write(
                        self.style.SUCCESS(f'Created department: {department.name}')
                    )
                else:
                    self.stdout.write(
                        self.style.WARNING(f'Department already exists: {department.name}')
                    )
            except Institution.DoesNotExist:
                self.stdout.write(
                    self.style.ERROR(f'Institution {dep_data["institution"]} not found')
                )

        self.stdout.write(
            self.style.SUCCESS('Successfully created institutions and departments')
        )
