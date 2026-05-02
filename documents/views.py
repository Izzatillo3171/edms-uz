# filepath: backend/documents/views.py
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, logout, authenticate
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib import messages
from django.utils import timezone
from django.db.models import Q, Count
from django.http import HttpResponse
from datetime import timedelta
import json
try:
    from openpyxl import Workbook
    from openpyxl.styles import Font, PatternFill, Alignment, Border, Side
    OPENPYXL_AVAILABLE = True
except ImportError:
    OPENPYXL_AVAILABLE = False
from .models import (
    User, Document, Resolution, DocumentHistory, 
    Notification, Department
)
from .forms import (
    UserRegistrationForm, UserLoginForm, DocumentForm,
    IncomingDocumentForm, CitizenAppealForm, ResolutionForm,
    ResolutionUpdateForm, DepartmentForm, DocumentStatusForm,
    DocumentSearchForm, UserProfileForm, PasswordChangeFormCustom
)


# ==================== Authentication Views ====================

def user_login(request):
    """User login view"""
    if request.method == 'POST':
        form = UserLoginForm(request, data=request.POST)
        if form.is_valid():
            username = form.cleaned_data['username']
            password = form.cleaned_data['password']
            user = authenticate(username=username, password=password)
            if user is not None:
                login(request, user)
                return redirect('dashboard')
        messages.error(request, 'Неверный логин или пароль')
    else:
        form = UserLoginForm()
    return render(request, 'registration/login.html', {'form': form})


def user_logout(request):
    """User logout view"""
    logout(request)
    return redirect('login')


def register(request):
    """User registration view"""
    admin_mode = request.user.is_authenticated and request.user.is_admin()

    if request.method == 'POST':
        form = UserRegistrationForm(request.POST, admin_mode=admin_mode)
        if form.is_valid():
            user = form.save(commit=False)
            user.full_name = form.cleaned_data.get('full_name', '')
            if not admin_mode:
                user.role = 'citizen'
            user.save()
            messages.success(request, 'Регистрация успешна! Теперь вы можете войти.')
            return redirect('login')
    else:
        form = UserRegistrationForm(admin_mode=admin_mode)
    return render(request, 'registration/register.html', {
        'form': form,
        'admin_mode': admin_mode
    })


# ==================== Dashboard Views ====================

def public_status_check(request):
    """Public page to check appeal status without login"""
    document = None
    error = None
    
    if request.method == 'POST' or request.GET.get('reg_number'):
        reg_number = request.POST.get('reg_number') or request.GET.get('reg_number')
        if reg_number:
            try:
                document = Document.objects.get(reg_number=reg_number, doc_type='APP')
            except Document.DoesNotExist:
                error = f'Обращение с номером "{reg_number}" не найдено'
    
    return render(request, 'documents/public_status_check.html', {
        'document': document,
        'error': error
    })


@login_required
def get_statistics_api(request):
    """API endpoint for getting system statistics as JSON"""
    user = request.user
    stats = {}
    
    # Basic stats
    stats['total_documents'] = Document.objects.count()
    stats['total_users'] = User.objects.count()
    stats['total_departments'] = Department.objects.count()
    
    # Status distribution
    stats['status_distribution'] = {}
    for status_key, status_label in Document.STATUS_CHOICES:
        stats['status_distribution'][status_key] = Document.objects.filter(status=status_key).count()
    
    # Document type distribution
    stats['type_distribution'] = {}
    for type_key, type_label in Document.DOC_TYPE_CHOICES:
        stats['type_distribution'][type_key] = Document.objects.filter(doc_type=type_key).count()
    
    # User role distribution
    stats['role_distribution'] = {
        'admin': User.objects.filter(role='admin').count(),
        'head': User.objects.filter(role='head').count(),
        'secretary': User.objects.filter(role='secretary').count(),
        'executor': User.objects.filter(role='executor').count(),
        'citizen': User.objects.filter(role='citizen').count(),
    }
    
    # Overdue documents
    today = timezone.now().date()
    stats['overdue_documents'] = Document.objects.filter(
        status__in=['IN_PROGRESS', 'RESOLUTION'],
        deadline__lt=today
    ).count()
    
    # Role-specific stats
    if user.is_executor():
        my_docs = Document.objects.filter(assigned_to=user)
        stats['my_stats'] = {
            'assigned': my_docs.count(),
            'in_progress': my_docs.filter(status='IN_PROGRESS').count(),
            'completed': my_docs.filter(status='DONE').count(),
            'overdue': my_docs.filter(status='IN_PROGRESS', deadline__lt=today).count(),
        }
    
    return HttpResponse(
        json.dumps(stats, ensure_ascii=False, indent=2),
        content_type='application/json; charset=utf-8'
    )


@login_required
def dashboard(request):
    """Main dashboard with statistics based on user role"""
    user = request.user
    context = {}
    
    # Common statistics
    total_docs = Document.objects.count()
    context['total_documents'] = total_docs
    context['user'] = user

    # Tasks assigned directly to this user
    assigned_tasks = Document.objects.filter(assigned_to=user)
    context['my_tasks'] = assigned_tasks
    context['pending_tasks'] = assigned_tasks.filter(status__in=['IN_PROGRESS', 'RESOLUTION'])
    context['completed_tasks'] = assigned_tasks.filter(status='DONE')
    context['overdue_tasks'] = assigned_tasks.filter(
        status__in=['IN_PROGRESS', 'RESOLUTION'],
        deadline__lt=timezone.now().date()
    )
    
    # Role-based statistics with detailed analytics
    if user.is_head() or user.is_admin():
        # Statistics for Head and Admin
        all_docs = Document.objects.all()
        
        # Status breakdown
        context['status_breakdown'] = {
            'DRAFT': all_docs.filter(status='DRAFT').count(),
            'REGISTERED': all_docs.filter(status='REGISTERED').count(),
            'SENT': all_docs.filter(status='SENT').count(),
            'RECEIVED': all_docs.filter(status='RECEIVED').count(),
            'RESOLUTION': all_docs.filter(status='RESOLUTION').count(),
            'IN_PROGRESS': all_docs.filter(status='IN_PROGRESS').count(),
            'DONE': all_docs.filter(status='DONE').count(),
        }
        
        # Document type breakdown
        context['type_breakdown'] = {
            'IN': all_docs.filter(doc_type='IN').count(),
            'OUT': all_docs.filter(doc_type='OUT').count(),
            'INT': all_docs.filter(doc_type='INT').count(),
            'APP': all_docs.filter(doc_type='APP').count(),
        }
        
        # Time-based metrics
        overdue = all_docs.filter(
            status__in=['IN_PROGRESS', 'RESOLUTION'],
            deadline__lt=timezone.now().date()
        ).count()
        
        in_progress = all_docs.filter(status='IN_PROGRESS').count()
        done = all_docs.filter(status='DONE').count()
        pending = all_docs.filter(status='RESOLUTION').count()
        
        context['overdue'] = overdue
        context['in_progress'] = in_progress
        context['done'] = done
        context['pending'] = pending
        
        # Acceptance statistics for incoming documents
        incoming = all_docs.filter(doc_type='IN')
        context['incoming_stats'] = {
            'total': incoming.count(),
            'accepted': incoming.filter(acceptance_status='accepted').count(),
            'rejected': incoming.filter(acceptance_status='rejected').count(),
            'pending': incoming.filter(acceptance_status='pending').count(),
        }
        
        # Recent documents
        context['recent_documents'] = all_docs.order_by('-created_at')[:10]
        
        # Monthly statistics
        from datetime import datetime, timedelta
        today = timezone.now().date()
        month_start = today.replace(day=1)
        context['month_documents'] = all_docs.filter(
            created_at__date__gte=month_start
        ).count()
        
    elif user.is_executor():
        # Tasks assigned to executor
        my_tasks = Document.objects.filter(assigned_to=user)
        context['my_tasks'] = my_tasks
        context['pending_tasks'] = my_tasks.filter(status='IN_PROGRESS')
        context['completed_tasks'] = my_tasks.filter(status='DONE')
        context['overdue_tasks'] = my_tasks.filter(
            status='IN_PROGRESS',
            deadline__lt=timezone.now().date()
        )
        context['task_count'] = my_tasks.count()
        
    elif user.is_secretary():
        # Documents registered by secretary
        incoming_today = Document.objects.filter(
            doc_type='IN',
            created_at__date=timezone.now().date()
        ).count()
        outgoing_today = Document.objects.filter(
            doc_type='OUT',
            created_at__date=timezone.now().date()
        ).count()
        
        context['incoming_today'] = incoming_today
        context['outgoing_today'] = outgoing_today
        
        # Today's statistics
        today_docs = Document.objects.filter(
            created_at__date=timezone.now().date()
        ).count()
        context['total_today'] = today_docs
        
    elif user.is_citizen():
        # Citizen's appeals
        appeals = Document.objects.filter(
            doc_type='APP',
            author=user
        )
        context['my_appeals'] = appeals
        context['pending_appeals'] = appeals.exclude(status='DONE')
        context['completed_appeals'] = appeals.filter(status='DONE')
        context['appeal_count'] = appeals.count()
    
    # Notifications
    context['notifications'] = Notification.objects.filter(
        user=user, 
        is_read=False
    )[:5]
    context['unread_count'] = Notification.objects.filter(
        user=user,
        is_read=False
    ).count()
    
    return render(request, 'dashboard.html', context)


# ==================== Document Views ====================

@login_required
def document_list(request):
    """List all documents with filtering"""
    documents = Document.objects.all().order_by('-created_at')
    form = DocumentSearchForm(request.GET)
    
    if form.is_valid():
        search = form.cleaned_data.get('search')
        doc_type = form.cleaned_data.get('doc_type')
        status = form.cleaned_data.get('status')
        date_from = form.cleaned_data.get('date_from')
        date_to = form.cleaned_data.get('date_to')
        
        if search:
            documents = documents.filter(
                Q(reg_number__icontains=search) | 
                Q(title__icontains=search) |
                Q(sender_person__icontains=search)
            )
        if doc_type:
            documents = documents.filter(doc_type=doc_type)
        if status:
            documents = documents.filter(status=status)
        if date_from:
            documents = documents.filter(created_at__date__gte=date_from)
        if date_to:
            documents = documents.filter(created_at__date__lte=date_to)
    
    # Filter by role
    user = request.user
    if user.is_executor():
        documents = documents.filter(assigned_to=user)
    elif user.is_citizen():
        documents = documents.filter(author=user, doc_type='APP')
    
    # Pagination
    from django.core.paginator import Paginator
    paginator = Paginator(documents, 25)
    page_number = request.GET.get('page')
    documents = paginator.get_page(page_number)
    
    context = {
        'documents': documents,
        'form': form,
    }
    return render(request, 'documents/document_list.html', context)


@login_required
def document_detail(request, pk):
    """View document details"""
    document = get_object_or_404(Document, pk=pk)
    resolutions = document.resolutions.all()
    history = document.history.all()
    
    context = {
        'document': document,
        'resolutions': resolutions,
        'history': history,
    }
    return render(request, 'documents/document_detail.html', context)


@login_required
@user_passes_test(lambda u: u.is_secretary() or u.is_head() or u.is_admin())
def document_create(request):
    """Create new document"""
    if request.method == 'POST':
        form = DocumentForm(request.POST, request.FILES)
        if form.is_valid():
            doc = form.save(commit=False)
            doc.author = request.user
            doc.status = 'REGISTERED'
            doc.save()
            
            # Create history entry
            DocumentHistory.objects.create(
                document=doc,
                action='REGISTERED',
                performed_by=request.user,
                notes='Документ зарегистрирован'
            )
            
            messages.success(request, f'Документ {doc.reg_number} успешно создан')
            return redirect('document_detail', pk=doc.pk)
    else:
        form = DocumentForm()
    
    return render(request, 'documents/document_form.html', {'form': form, 'title': 'Создание документа'})


@login_required
@user_passes_test(lambda u: u.is_secretary())
def register_incoming(request):
    """Register incoming document (Secretary only)"""
    if request.method == 'POST':
        form = IncomingDocumentForm(request.POST, request.FILES)
        if form.is_valid():
            doc = form.save(commit=False)
            doc.doc_type = 'IN'
            doc.author = request.user
            doc.status = 'REGISTERED'
            
            # Generate registration number
            today = timezone.now().date()
            count = Document.objects.filter(
                doc_type='IN',
                created_at__date=today
            ).count() + 1
            doc.reg_number = f"IN-{today.strftime('%Y%m%d')}-{count:04d}"
            
            doc.save()
            
            # Create history
            DocumentHistory.objects.create(
                document=doc,
                action='REGISTERED',
                performed_by=request.user,
                notes='Входящий документ зарегистрирован'
            )
            
            messages.success(request, f'Входящий документ {doc.reg_number} зарегистрирован')
            return redirect('document_detail', pk=doc.pk)
    else:
        form = IncomingDocumentForm()
    
    return render(request, 'documents/document_form.html', {
        'form': form, 
        'title': 'Регистрация входящего документа'
    })


def citizen_appeal(request):
    """Submit citizen appeal"""
    if request.method == 'POST':
        form = CitizenAppealForm(request.POST)
        if form.is_valid():
            doc = form.save(commit=False)
            doc.doc_type = 'APP'
            doc.author = request.user if request.user.is_authenticated else None
            if doc.destination_person:
                doc.status = 'IN_PROGRESS'
                doc.assigned_to = doc.destination_person
            else:
                doc.status = 'REGISTERED'
            # Deadline auto-calculated in model save()
            doc.save()
            
            if doc.destination_person:
                DocumentHistory.objects.create(
                    document=doc,
                    action='IN_PROGRESS',
                    performed_by=request.user if request.user.is_authenticated else None,
                    notes=f'Обращение назначено ответственному: {doc.destination_person}'
                )
            
            # Create notifications for all relevant users in the destination department
            relevant_users = User.objects.filter(
                department=doc.destination_department,
                role__in=['secretary', 'head', 'executor']
            )
            
            for user in relevant_users:
                Notification.objects.create(
                    user=user,
                    notification_type='NEW_DOCUMENT',
                    title=f'Новое обращение: {doc.title}',
                    message=f'Поступило новое обращение от {doc.sender_person}. Рег. номер: {doc.reg_number}',
                    document=doc
                )
            
            # Also notify the specific destination person if not already included
            if doc.destination_person and doc.destination_person not in relevant_users:
                Notification.objects.create(
                    user=doc.destination_person,
                    notification_type='NEW_DOCUMENT',
                    title=f'Новое обращение: {doc.title}',
                    message=f'На вас поступило обращение от {doc.sender_person}. Рег. номер: {doc.reg_number}',
                    document=doc
                )
            
            messages.success(request, f'Ваше обращение принято! ID: {doc.reg_number}')
            return redirect('appeal_status', reg_number=doc.reg_number)
    else:
        form = CitizenAppealForm()
    
    return render(request, 'documents/appeal_form.html', {'form': form})


def appeal_status(request, reg_number):
    """Check appeal status by registration number"""
    document = get_object_or_404(Document, reg_number=reg_number, doc_type='APP')
    return render(request, 'documents/appeal_status.html', {'document': document})


@login_required
@user_passes_test(lambda u: u.is_secretary() or u.is_head() or u.is_admin())
@login_required
@user_passes_test(lambda u: u.is_secretary() or u.is_head() or u.is_admin())
def accept_document(request, pk):
    """Accept incoming document"""
    document = get_object_or_404(Document, pk=pk, doc_type='IN')
    
    if request.method == 'POST':
        document.acceptance_status = 'accepted'
        document.accepted_by = request.user
        document.accepted_at = timezone.now()
        document.save()
        
        # Create audit log entry
        DocumentHistory.objects.create(
            document=document,
            action='ACCEPTED',
            performed_by=request.user,
            notes=f'Документ принят пользователем {request.user.get_full_name() or request.user.username}'
        )
        
        messages.success(request, f'Документ {document.reg_number} принят успешно')
        return redirect('document_detail', pk=document.pk)
    
    return render(request, 'documents/accept_document.html', {'document': document})


@login_required
@user_passes_test(lambda u: u.is_secretary() or u.is_head() or u.is_admin())
def reject_document(request, pk):
    """Reject incoming document"""
    document = get_object_or_404(Document, pk=pk, doc_type='IN')
    
    if request.method == 'POST':
        reason = request.POST.get('reason', '')
        
        document.acceptance_status = 'rejected'
        document.accepted_by = request.user
        document.accepted_at = timezone.now()
        document.rejection_reason = reason
        document.save()
        
        # Create audit log entry
        DocumentHistory.objects.create(
            document=document,
            action='REJECTED',
            performed_by=request.user,
            notes=f'Документ отклонен. Причина: {reason}'
        )
        
        messages.success(request, f'Документ {document.reg_number} отклонен')
        return redirect('document_list')
    
    return render(request, 'documents/reject_document.html', {'document': document})


# ==================== Resolution Views ====================

@login_required
@user_passes_test(lambda u: u.is_head())
def create_resolution(request, document_id):
    """Create resolution for a document (Head only)"""
    document = get_object_or_404(Document, pk=document_id)
    
    if request.method == 'POST':
        form = ResolutionForm(request.POST)
        if form.is_valid():
            resolution = form.save(commit=False)
            resolution.document = document
            resolution.author = request.user
            resolution.save()
            
            # Update document status
            document.status = 'IN_PROGRESS'
            document.assigned_to = resolution.executor
            document.save()
            
            # Create history
            DocumentHistory.objects.create(
                document=document,
                action='IN_PROGRESS',
                performed_by=request.user,
                notes=f'Резолюция назначена исполнителю: {resolution.executor}'
            )
            
            # Create notification
            Notification.objects.create(
                user=resolution.executor,
                notification_type='RESOLUTION',
                title='Новая резолюция',
                message=f'Вам назначен документ: {document.reg_number}',
                document=document
            )
            
            messages.success(request, 'Резолюция создана')
            return redirect('document_detail', pk=document.pk)
    else:
        form = ResolutionForm()
    
    return render(request, 'documents/resolution_form.html', {
        'form': form,
        'document': document
    })


@login_required
@user_passes_test(lambda u: u.is_executor())
def complete_resolution(request, resolution_id):
    """Complete a resolution (Executor only)"""
    resolution = get_object_or_404(Resolution, pk=resolution_id, executor=request.user)
    
    if request.method == 'POST':
        form = ResolutionUpdateForm(request.POST)
        if form.is_valid():
            resolution.is_completed = True
            resolution.completion_note = form.cleaned_data['completion_note']
            resolution.completed_at = timezone.now()
            resolution.save()
            
            # Update document status
            document = resolution.document
            document.status = 'DONE'
            document.save()
            
            # Create history
            DocumentHistory.objects.create(
                document=document,
                action='DONE',
                performed_by=request.user,
                notes='Задача выполнена'
            )
            
            # Notify head
            if document.author:
                Notification.objects.create(
                    user=document.author,
                    notification_type='COMPLETED',
                    title='Задача выполнена',
                    message=f'Документ {document.reg_number} выполнен',
                    document=document
                )
            
            messages.success(request, 'Задача выполнена')
            return redirect('document_detail', pk=document.pk)
    else:
        form = ResolutionUpdateForm()
    
    return render(request, 'documents/resolution_complete.html', {
        'form': form,
        'resolution': resolution
    })


# ==================== Admin Views ====================

@login_required
@user_passes_test(lambda u: u.is_admin())
def user_list(request):
    """List all users (Admin only)"""
    users = User.objects.all().select_related('department')
    return render(request, 'admin/user_list.html', {'users': users})


@login_required
@user_passes_test(lambda u: u.is_admin())
def department_list(request):
    """List all departments"""
    departments = Department.objects.all()
    return render(request, 'admin/department_list.html', {'departments': departments})


@login_required
@user_passes_test(lambda u: u.is_admin())
def department_create(request):
    """Create new department"""
    if request.method == 'POST':
        form = DepartmentForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'Отдел создан')
            return redirect('department_list')
    else:
        form = DepartmentForm()
    
    return render(request, 'admin/department_form.html', {'form': form})


# ==================== Notification Views ====================

@login_required
@login_required
def notifications(request):
    """View all notifications"""
    notifications = Notification.objects.filter(user=request.user)
    return render(request, 'notifications.html', {'notifications': notifications})


@login_required
def open_notification(request, notification_id):
    """Mark notification as read and open its related document"""
    notification = get_object_or_404(
        Notification,
        pk=notification_id,
        user=request.user
    )
    notification.is_read = True
    notification.save()

    if notification.document:
        return redirect('document_detail', pk=notification.document.pk)
    return redirect('notifications')


@login_required
def mark_notification_read(request, notification_id):
    """Mark notification as read"""
    notification = get_object_or_404(
        Notification, 
        pk=notification_id, 
        user=request.user
    )
    notification.is_read = True
    notification.save()
    return redirect('notifications')


@login_required
def mark_all_notifications_read(request):
    """Mark all notifications as read"""
    Notification.objects.filter(user=request.user, is_read=False).update(is_read=True)
    return redirect('notifications')


# ==================== Export/Print Views ====================

@login_required
def export_document_json(request, pk):
    """Export document as JSON"""
    document = get_object_or_404(Document, pk=pk)
    
    # Prepare document data
    data = {
        'reg_number': document.reg_number,
        'title': document.title,
        'type': document.get_doc_type_display(),
        'status': document.get_status_display(),
        'content': document.content,
        'created_at': document.created_at.isoformat(),
        'deadline': document.deadline.isoformat() if document.deadline else None,
        'sender_org': document.sender_org,
        'sender_person': document.sender_person,
        'author': document.author.full_name if document.author else 'Unknown',
        'resolutions': []
    }
    
    # Add resolutions
    for resolution in document.resolutions.all():
        data['resolutions'].append({
            'text': resolution.text,
            'executor': resolution.executor.full_name if resolution.executor else 'Unknown',
            'due_date': resolution.due_date.isoformat() if resolution.due_date else None,
            'is_completed': resolution.is_completed,
            'is_signed': resolution.is_signed,
        })
    
    response = HttpResponse(
        json.dumps(data, ensure_ascii=False, indent=2),
        content_type='application/json; charset=utf-8'
    )
    response['Content-Disposition'] = f'attachment; filename="document_{document.reg_number}.json"'
    return response


@login_required
def export_documents_excel(request):
    """Export documents list to Excel"""
    if not OPENPYXL_AVAILABLE:
        messages.error(request, 'Библиотека openpyxl не установлена. Пожалуйста, обратитесь к администратору.')
        return redirect('document_list')
    
    # Get filtered documents
    documents = Document.objects.all()
    doc_type = request.GET.get('doc_type')
    status = request.GET.get('status')
    search = request.GET.get('search')
    
    if doc_type:
        documents = documents.filter(doc_type=doc_type)
    if status:
        documents = documents.filter(status=status)
    if search:
        documents = documents.filter(
            Q(reg_number__icontains=search) |
            Q(title__icontains=search)
        )
    
    # Create workbook
    wb = Workbook()
    ws = wb.active
    ws.title = 'Документы'
    
    # Define styles
    header_fill = PatternFill(start_color='1a237e', end_color='1a237e', fill_type='solid')
    header_font = Font(bold=True, color='FFFFFF', size=12)
    center_alignment = Alignment(horizontal='center', vertical='center', wrap_text=True)
    border = Border(
        left=Side(style='thin'),
        right=Side(style='thin'),
        top=Side(style='thin'),
        bottom=Side(style='thin')
    )
    
    # Add headers
    headers = ['№', 'Рег. номер', 'Название', 'Тип', 'Статус', 'Автор', 'Срок исполнения', 'Дата создания']
    for col_num, header in enumerate(headers, 1):
        cell = ws.cell(row=1, column=col_num)
        cell.value = header
        cell.fill = header_fill
        cell.font = header_font
        cell.alignment = center_alignment
        cell.border = border
    
    # Add data
    for row_num, doc in enumerate(documents, 2):
        data = [
            row_num - 1,
            doc.reg_number or '—',
            doc.title,
            doc.get_doc_type_display(),
            doc.get_status_display(),
            str(doc.author) if doc.author else '—',
            doc.deadline.strftime('%d.%m.%Y') if doc.deadline else '—',
            doc.created_at.strftime('%d.%m.%Y %H:%M')
        ]
        
        for col_num, value in enumerate(data, 1):
            cell = ws.cell(row=row_num, column=col_num)
            cell.value = value
            cell.alignment = center_alignment if col_num in [1, 4, 5, 7] else Alignment(vertical='center', wrap_text=True)
            cell.border = border
    
    # Auto-adjust column widths
    column_widths = [5, 15, 30, 12, 15, 20, 18, 18]
    for i, width in enumerate(column_widths, 1):
        ws.column_dimensions[chr(64 + i)].width = width
    
    # Prepare response
    response = HttpResponse(
        content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
    )
    response['Content-Disposition'] = 'attachment; filename="documents.xlsx"'
    wb.save(response)
    return response


@login_required
def document_print(request, pk):
    """Print document view"""
    document = get_object_or_404(Document, pk=pk)
    resolutions = document.resolutions.all()
    history = document.history.all()
    
    context = {
        'document': document,
        'resolutions': resolutions,
        'history': history,
        'print_mode': True,
    }
    return render(request, 'documents/document_print.html', context)


@login_required
@user_passes_test(lambda u: u.is_head())
def sign_resolution(request, resolution_id):
    """Sign resolution with digital signature (Head only)"""
    resolution = get_object_or_404(Resolution, pk=resolution_id, author=request.user)
    
    if request.method == 'POST':
        confirm = request.POST.get('confirm_signature')
        if confirm:
            resolution.is_signed = True
            resolution.signed_by = request.user
            resolution.signed_at = timezone.now()
            # In a real system, this would contain actual digital signature data
            resolution.signature_data = f"Подписано: {request.user.full_name} в {timezone.now().isoformat()}"
            resolution.save()
            
            # Create notification
            if resolution.executor:
                Notification.objects.create(
                    user=resolution.executor,
                    notification_type='RESOLUTION',
                    title='Резолюция подписана',
                    message=f'Резолюция к документу {resolution.document.reg_number} подписана',
                    document=resolution.document
                )
            
            messages.success(request, 'Резолюция подписана ЭЦП')
            return redirect('document_detail', pk=resolution.document.pk)
        else:
            messages.error(request, 'Вы должны подтвердить подпись')
    
    return render(request, 'documents/resolution_sign.html', {'resolution': resolution})


# ==================== User Profile Views ====================

@login_required
def profile(request):
    """User profile page"""
    return render(request, 'profile.html', {'user': request.user})


@login_required
def change_password(request):
    """Change user password"""
    if request.method == 'POST':
        form = PasswordChangeFormCustom(request.POST)
        if form.is_valid():
            # Check if old password is correct
            old_password = form.cleaned_data.get('old_password')
            if not request.user.check_password(old_password):
                form.add_error('old_password', 'Текущий пароль неверный')
            else:
                # Set new password
                new_password = form.cleaned_data.get('new_password1')
                request.user.set_password(new_password)
                request.user.save()
                messages.success(request, 'Пароль успешно изменен')
                # Optionally, log the user out and require re-login
                # auth_logout(request)
                # return redirect('login')
                return redirect('user_profile')
    else:
        form = PasswordChangeFormCustom()
    
    return render(request, 'documents/change_password.html', {'form': form})


def get_users_by_department(request):
    """AJAX endpoint to get users filtered by department"""
    department_id = request.GET.get('department_id')
    if department_id:
        users = User.objects.filter(
            department_id=department_id,
            role__in=['secretary', 'head', 'executor']
        ).values('id', 'full_name', 'username')
        return HttpResponse(
            json.dumps(list(users), ensure_ascii=False),
            content_type='application/json; charset=utf-8'
        )
    return HttpResponse(
        json.dumps([]),
        content_type='application/json; charset=utf-8'
    )
