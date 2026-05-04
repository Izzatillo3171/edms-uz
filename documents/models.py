# filepath: backend/documents/models.py
from django.db import models
from django.contrib.auth.models import AbstractUser
from django.utils import timezone
from datetime import timedelta


class User(AbstractUser):
    """
    Custom user model with role-based access control.
    Roles: Citizen, Secretary, Head, Executor, Admin
    """
    ROLE_CHOICES = [
        ('citizen', 'Гражданин'),
        ('secretary', 'Секретарь'),
        ('head', 'Руководитель'),
        ('executor', 'Исполнитель'),
        ('admin', 'Администратор'),
    ]
    
    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default='citizen')
    full_name = models.CharField(max_length=255, blank=True)
    phone = models.CharField(max_length=20, blank=True)
    department = models.ForeignKey(
        'Department', 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True,
        related_name='users'
    )
    
    class Meta:
        verbose_name = 'Пользователь'
        verbose_name_plural = 'Пользователи'
    
    def __str__(self):
        return f"{self.username} ({self.get_role_display()})"
    
    def is_head(self):
        return self.role == 'head'
    
    def is_secretary(self):
        return self.role == 'secretary'
    
    def is_executor(self):
        return self.role == 'executor'
    
    def is_admin(self):
        return self.role == 'admin'
    
    def is_citizen(self):
        return self.role == 'citizen'


class Institution(models.Model):
    """Government institution model (Министерство, Агентство, Хокимият)"""
    INSTITUTION_TYPE_CHOICES = [
        ('ministry', 'Министерство'),
        ('agency', 'Агентство'),
        ('committee', 'Комитет'),
        ('hokimiyat', 'Хокимият'),
        ('other', 'Другое учреждение'),
    ]
    
    name = models.CharField(max_length=255, unique=True)
    institution_type = models.CharField(max_length=20, choices=INSTITUTION_TYPE_CHOICES)
    code = models.CharField(max_length=20, unique=True, blank=True)
    description = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        verbose_name = 'Государственное учреждение'
        verbose_name_plural = 'Государственные учреждения'
        ordering = ['name']
    
    def __str__(self):
        return f"{self.name} ({self.get_institution_type_display()})"


class Department(models.Model):
    """Department model for organizing users within institutions"""
    DEPARTMENT_TYPE_CHOICES = [
        ('chancellery', 'Канцелярия'),
        ('hr', 'Отдел кадров'),
        ('legal', 'Юридический отдел'),
        ('finance', 'Финансовый отдел'),
        ('it', 'Отдел ИКТ'),
        ('press', 'Пресс-служба'),
        ('appeals', 'Отдел по работе с обращениями'),
        ('other', 'Другой отдел'),
    ]
    
    name = models.CharField(max_length=255)
    code = models.CharField(max_length=20, unique=True)
    institution = models.ForeignKey(
        Institution,
        on_delete=models.CASCADE,
        related_name='departments',
        null=True,
        blank=True
    )
    department_type = models.CharField(
        max_length=20,
        choices=DEPARTMENT_TYPE_CHOICES,
        default='other'
    )
    description = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        verbose_name = 'Отдел'
        verbose_name_plural = 'Отделы'
        unique_together = ['code', 'institution']
        ordering = ['institution', 'name']
    
    def __str__(self):
        if self.institution:
            return f"{self.name} ({self.institution.name})"
        return f"{self.name}"


class Document(models.Model):
    """
    Document model representing various types of documents in the system.
    Types: IN (Incoming), OUT (Outgoing), INT (Internal), APP (Appeals/Citizen)
    """
    DOC_TYPE_CHOICES = [
        ('IN', 'Входящий'),
        ('OUT', 'Исходящий'),
        ('INT', 'Внутренний'),
        ('APP', 'Обращение гражданина'),
    ]
    
    STATUS_CHOICES = [
        ('DRAFT', 'Черновик'),
        ('REGISTERED', 'Зарегистрирован'),
        ('SENT', 'Отправлен'),
        ('RECEIVED', 'Принят'),
        ('RESOLUTION', 'На резолюции'),
        ('IN_PROGRESS', 'В работе'),
        ('DONE', 'Выполнен'),
        ('OVERDUE', 'Просрочен'),
    ]
    
    reg_number = models.CharField(max_length=50, unique=True, blank=True)
    title = models.CharField(max_length=500)
    doc_type = models.CharField(max_length=10, choices=DOC_TYPE_CHOICES)
    content = models.TextField(blank=True)
    file = models.FileField(upload_to='documents/%Y/%m/', blank=True, null=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='DRAFT')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    deadline = models.DateField(null=True, blank=True)
    
    # Relations
    author = models.ForeignKey(
        User, 
        on_delete=models.SET_NULL, 
        null=True, 
        related_name='authored_documents'
    )
    assigned_to = models.ForeignKey(
        User, 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True,
        related_name='assigned_documents'
    )
    sender_org = models.CharField(max_length=255, blank=True)
    sender_person = models.CharField(max_length=255, blank=True)
    
    # Destination fields for citizen appeals
    destination_org = models.CharField(max_length=255, blank=True, help_text='Государственное учреждение-получатель')
    destination_department = models.ForeignKey(
        'Department',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='received_documents',
        help_text='Отдел-получатель'
    )
    destination_person = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='received_appeals',
        help_text='Лицо, ответственное за обработку'
    )
    
    # Acceptance status for incoming documents
    ACCEPTANCE_STATUS_CHOICES = [
        ('pending', 'В ожидании'),
        ('accepted', 'Принято'),
        ('rejected', 'Отклонено'),
    ]
    acceptance_status = models.CharField(
        max_length=20,
        choices=ACCEPTANCE_STATUS_CHOICES,
        default='pending',
        help_text='Статус приема входящего документа'
    )
    accepted_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='accepted_documents',
        help_text='Пользователь, принявший документ'
    )
    accepted_at = models.DateTimeField(null=True, blank=True)
    rejection_reason = models.TextField(blank=True, help_text='Причина отклонения документа')
    
    class Meta:
        verbose_name = 'Документ'
        verbose_name_plural = 'Документы'
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.reg_number} - {self.title}"
    
    def is_overdue(self):
        """Check if document is overdue"""
        if self.deadline and self.status != 'DONE':
            return timezone.now().date() > self.deadline
        return False
    
    def save(self, *args, **kwargs):
        # Auto-generate registration number for citizen appeals
        if self.doc_type == 'APP' and not self.reg_number:
            today = timezone.now().date()
            count = Document.objects.filter(
                doc_type='APP',
                created_at__date=today
            ).count() + 1
            self.reg_number = f"APP-{today.strftime('%Y%m%d')}-{count:04d}"
        
        # Auto-calculate deadline for citizen appeals (15 days)
        if self.doc_type == 'APP' and not self.deadline:
            self.deadline = timezone.now().date() + timedelta(days=15)
        
        super().save(*args, **kwargs)


class Resolution(models.Model):
    """Resolution model for assigning tasks to executors."""
    document = models.ForeignKey(
        Document, 
        on_delete=models.CASCADE, 
        related_name='resolutions'
    )
    author = models.ForeignKey(
        User, 
        on_delete=models.SET_NULL, 
        null=True, 
        related_name='created_resolutions'
    )
    executor = models.ForeignKey(
        User, 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True,
        related_name='assigned_resolutions'
    )
    text = models.TextField()
    due_date = models.DateField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    is_completed = models.BooleanField(default=False)
    completion_note = models.TextField(blank=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    
    # Digital signature fields
    is_signed = models.BooleanField(default=False, help_text='Документ подписан ЭЦП')
    signed_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='signed_resolutions',
        help_text='Лицо, подписавшее документ'
    )
    signed_at = models.DateTimeField(null=True, blank=True)
    signature_data = models.TextField(blank=True, help_text='Данные цифровой подписи')
    
    class Meta:
        verbose_name = 'Резолюция'
        verbose_name_plural = 'Резолюции'
        ordering = ['-created_at']
    
    def __str__(self):
        return f"Резолюция к {self.document.reg_number}"


class DocumentHistory(models.Model):
    """Track document status changes and actions"""
    ACTION_CHOICES = [
        ('CREATED', 'Создан'),
        ('REGISTERED', 'Зарегистрирован'),
        ('SENT', 'Отправлен'),
        ('RECEIVED', 'Получен'),
        ('ACCEPTED', 'Принят'),
        ('REJECTED', 'Отклонен'),
        ('IN_PROGRESS', 'В работе'),
        ('DONE', 'Завершен'),
    ]
    
    document = models.ForeignKey(
        Document, 
        on_delete=models.CASCADE, 
        related_name='history'
    )
    action = models.CharField(max_length=20, choices=ACTION_CHOICES, default='CREATED')
    performed_by = models.ForeignKey(
        User, 
        on_delete=models.SET_NULL, 
        null=True,
        blank=True,
        related_name='performed_actions'
    )
    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        verbose_name = 'История документа'
        verbose_name_plural = 'История документов'
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.document.reg_number} - {self.get_action_display()}"


class Notification(models.Model):
    """User notifications for document assignments"""
    NOTIFICATION_TYPE_CHOICES = [
        ('NEW_DOCUMENT', 'Новый документ'),
        ('RESOLUTION', 'Резолюция'),
        ('DEADLINE', 'Напоминание о сроке'),
        ('OVERDUE', 'Документ просрочен'),
        ('COMPLETED', 'Задача выполнена'),
    ]
    
    user = models.ForeignKey(
        User, 
        on_delete=models.CASCADE, 
        related_name='notifications'
    )
    notification_type = models.CharField(max_length=20, choices=NOTIFICATION_TYPE_CHOICES)
    title = models.CharField(max_length=255)
    message = models.TextField()
    document = models.ForeignKey(
        Document, 
        on_delete=models.CASCADE, 
        null=True, 
        blank=True,
        related_name='notifications'
    )
    is_read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        verbose_name = 'Уведомление'
        verbose_name_plural = 'Уведомления'
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.notification_type} - {self.title}"


class AuditLog(models.Model):
    """Audit trail for all system actions"""
    ACTION_CHOICES = [
        ('CREATE', 'Создание'),
        ('UPDATE', 'Обновление'),
        ('DELETE', 'Удаление'),
        ('SIGN', 'Подпись'),
        ('APPROVE', 'Одобрение'),
        ('REJECT', 'Отклонение'),
        ('EXPORT', 'Экспорт'),
        ('PRINT', 'Печать'),
    ]
    
    user = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        related_name='audit_logs'
    )
    action = models.CharField(max_length=20, choices=ACTION_CHOICES)
    object_type = models.CharField(max_length=100)  # e.g., 'Document', 'Resolution'
    object_id = models.IntegerField()
    object_str = models.CharField(max_length=255)  # String representation
    changes = models.JSONField(null=True, blank=True)  # What changed
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    user_agent = models.TextField(blank=True)
    timestamp = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        verbose_name = 'Лог аудита'
        verbose_name_plural = 'Логи аудита'
        ordering = ['-timestamp']
        indexes = [
            models.Index(fields=['timestamp']),
            models.Index(fields=['user']),
            models.Index(fields=['object_type', 'object_id']),
        ]
    
    def __str__(self):
        return f"{self.action} {self.object_type}#{self.object_id} - {self.user}"


class DocumentTransfer(models.Model):
    """
    Model for tracking document transfers between department heads.
    Allows heads to send documents to other department heads with files.
    """
    STATUS_CHOICES = [
        ('pending', 'В ожидании'),
        ('accepted', 'Принято'),
        ('rejected', 'Отклонено'),
    ]
    
    document = models.ForeignKey(
        Document,
        on_delete=models.CASCADE,
        related_name='transfers',
        help_text='Документ для передачи'
    )
    
    # From (sender)
    from_department = models.ForeignKey(
        Department,
        on_delete=models.SET_NULL,
        null=True,
        related_name='sent_transfers',
        help_text='Отдел отправителя'
    )
    from_user = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        related_name='sent_transfers',
        help_text='Руководитель-отправитель'
    )
    
    # To (receiver)
    to_department = models.ForeignKey(
        Department,
        on_delete=models.SET_NULL,
        null=True,
        related_name='received_transfers',
        help_text='Отдел получателя'
    )
    to_user = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        related_name='received_transfers',
        help_text='Руководитель-получатель'
    )
    
    # File and notes
    transfer_file = models.FileField(
        upload_to='transfers/%Y/%m/',
        blank=True,
        null=True,
        help_text='Сопроводительный документ'
    )
    transfer_note = models.TextField(
        blank=True,
        help_text='Примечание к передаче'
    )
    
    # Status tracking
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='pending',
        help_text='Статус передачи'
    )
    created_at = models.DateTimeField(auto_now_add=True)
    accepted_at = models.DateTimeField(null=True, blank=True)
    accepted_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='accepted_transfers',
        help_text='Руководитель, принявший документ'
    )
    rejection_reason = models.TextField(
        blank=True,
        help_text='Причина отклонения'
    )
    
    class Meta:
        verbose_name = 'Передача документа'
        verbose_name_plural = 'Передачи документов'
        ordering = ['-created_at']
    
    def __str__(self):
        return f"Передача {self.document.reg_number} из {self.from_department} в {self.to_department}"
