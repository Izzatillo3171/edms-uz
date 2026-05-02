# filepath: backend/documents/forms.py
from django import forms
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from .models import User, Document, Resolution, Department


class UserRegistrationForm(UserCreationForm):
    """Form for user registration"""
    role = forms.ChoiceField(
        choices=User.ROLE_CHOICES,
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    full_name = forms.CharField(
        max_length=255,
        required=False,
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'ФИО'})
    )
    phone = forms.CharField(
        max_length=20,
        required=False,
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Телефон'})
    )
    department = forms.ModelChoiceField(
        queryset=Department.objects.all(),
        required=False,
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    
    class Meta:
        model = User
        fields = ('username', 'email', 'password1', 'password2', 
                  'role', 'full_name', 'phone', 'department')
        widgets = {
            'username': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Логин'}),
            'email': forms.EmailInput(attrs={'class': 'form-control', 'placeholder': 'Email'}),
        }
    
    def __init__(self, *args, **kwargs):
        self.admin_mode = kwargs.pop('admin_mode', False)
        super().__init__(*args, **kwargs)

        if not self.admin_mode:
            # Remove admin role from choices for non-admin users
            self.fields['role'].choices = [
                choice for choice in User.ROLE_CHOICES 
                if choice[0] != 'admin'
            ]
            self.fields['role'].initial = 'citizen'

        self.fields['password1'].widget = forms.PasswordInput(attrs={
            'class': 'form-control', 
            'placeholder': 'Пароль',
            'id': 'id_password1'
        })
        self.fields['password2'].widget = forms.PasswordInput(attrs={
            'class': 'form-control', 
            'placeholder': 'Повторите пароль',
            'id': 'id_password2'
        })

    def clean_role(self):
        role = self.cleaned_data.get('role')
        if role == 'admin' and not self.admin_mode:
            raise forms.ValidationError('Роль администратора может назначить только существующий администратор.')
        return role


class UserLoginForm(AuthenticationForm):
    """Form for user login"""
    username = forms.CharField(
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Логин'})
    )
    password = forms.CharField(
        widget=forms.PasswordInput(attrs={'class': 'form-control', 'placeholder': 'Пароль'})
    )


class DocumentForm(forms.ModelForm):
    """Form for creating/editing documents"""
    class Meta:
        model = Document
        fields = ('title', 'doc_type', 'content', 'file', 
                  'sender_org', 'sender_person', 'assigned_to')
        widgets = {
            'title': forms.TextInput(attrs={'class': 'form-control'}),
            'doc_type': forms.Select(attrs={'class': 'form-select'}),
            'content': forms.Textarea(attrs={'class': 'form-control', 'rows': 5}),
            'file': forms.FileInput(attrs={'class': 'form-control'}),
            'sender_org': forms.TextInput(attrs={'class': 'form-control'}),
            'sender_person': forms.TextInput(attrs={'class': 'form-control'}),
            'assigned_to': forms.Select(attrs={'class': 'form-select'}),
        }


class IncomingDocumentForm(forms.ModelForm):
    """Form specifically for registering incoming documents (Secretary)"""
    class Meta:
        model = Document
        fields = ('title', 'content', 'file', 'sender_org', 'sender_person')
        widgets = {
            'title': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Название документа'}),
            'content': forms.Textarea(attrs={'class': 'form-control', 'rows': 5, 'placeholder': 'Содержание'}),
            'file': forms.FileInput(attrs={'class': 'form-control'}),
            'sender_org': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Организация-отправитель'}),
            'sender_person': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'ФИО отправителя'}),
        }


class CitizenAppealForm(forms.ModelForm):
    """Form for citizen appeals submission"""
    destination_department = forms.ModelChoiceField(
        queryset=Department.objects.all(),
        widget=forms.Select(attrs={
            'class': 'form-select',
            'id': 'id_destination_department'
        }),
        label='Отдел-получатель',
        required=True
    )
    destination_person = forms.ModelChoiceField(
        queryset=User.objects.filter(role__in=['secretary', 'head', 'executor']),
        widget=forms.Select(attrs={
            'class': 'form-select',
            'id': 'id_destination_person',
            'data-department': ''  # Will be filled by JavaScript
        }),
        label='Ответственное лицо',
        required=True
    )
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Add department info to person choices
        person_field = self.fields['destination_person']
        person_choices = [(u.id, f"{u.full_name or u.username} ({u.department.name if u.department else 'Без отдела'})")
                          for u in User.objects.filter(role__in=['secretary', 'head', 'executor']).select_related('department')]
        person_field.choices = [('', '---------')] + person_choices
    
    class Meta:
        model = Document
        fields = ('title', 'content', 'sender_person', 'destination_org', 'destination_department', 'destination_person')
        labels = {
            'title': 'Тема обращения',
            'content': 'Содержание обращения',
            'sender_person': 'Ваше ФИО',
            'destination_org': 'Государственное учреждение',
        }
        widgets = {
            'title': forms.TextInput(attrs={
                'class': 'form-control', 
                'placeholder': 'Тема обращения'
            }),
            'content': forms.Textarea(attrs={
                'class': 'form-control', 
                'rows': 6, 
                'placeholder': 'Опишите вашу проблему или обращение...'
            }),
            'sender_person': forms.TextInput(attrs={
                'class': 'form-control', 
                'placeholder': 'Ваше ФИО'
            }),
            'destination_org': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Государственное учреждение (напр. МВД, МЗ)'
            }),
        }


class ResolutionForm(forms.ModelForm):
    """Form for creating resolutions (Head)"""
    class Meta:
        model = Resolution
        fields = ('executor', 'text', 'due_date')
        labels = {
            'executor': 'Исполнитель',
            'text': 'Текст резолюции',
            'due_date': 'Срок исполнения',
        }
        widgets = {
            'executor': forms.Select(attrs={'class': 'form-select'}),
            'text': forms.Textarea(attrs={'class': 'form-control', 'rows': 4, 'placeholder': 'Текст резолюции'}),
            'due_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
        }


class ResolutionUpdateForm(forms.ModelForm):
    """Form for executor to complete/resolution"""
    class Meta:
        model = Resolution
        fields = ('completion_note',)
        labels = {
            'completion_note': 'Отчет о выполнении',
        }
        widgets = {
            'completion_note': forms.Textarea(attrs={
                'class': 'form-control', 
                'rows': 3, 
                'placeholder': 'Отчет о выполнении...'
            }),
        }


class DepartmentForm(forms.ModelForm):
    """Form for creating departments"""
    class Meta:
        model = Department
        fields = ('name', 'code', 'description')
        labels = {
            'name': 'Название отдела',
            'code': 'Код отдела',
            'description': 'Описание',
        }
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Название отдела'}),
            'code': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Например: IT, HR'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'Описание отдела'}),
        }


class DocumentStatusForm(forms.ModelForm):
    """Form for updating document status"""
    class Meta:
        model = Document
        fields = ('status',)
        labels = {
            'status': 'Статус документа',
        }
        widgets = {
            'status': forms.Select(attrs={'class': 'form-select'}),
        }


class DocumentSearchForm(forms.Form):
    """Form for searching and filtering documents"""
    search = forms.CharField(
        max_length=100, 
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control', 
            'placeholder': 'Поиск по номеру или названию...'
        })
    )
    doc_type = forms.ChoiceField(
        choices=[('', 'Все типы')] + list(Document.DOC_TYPE_CHOICES),
        required=False,
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    status = forms.ChoiceField(
        choices=[('', 'Все статусы')] + list(Document.STATUS_CHOICES),
        required=False,
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    date_from = forms.DateField(
        required=False,
        widget=forms.DateInput(attrs={
            'class': 'form-control',
            'type': 'date'
        })
    )
    date_to = forms.DateField(
        required=False,
        widget=forms.DateInput(attrs={
            'class': 'form-control',
            'type': 'date'
        })
    )


class UserProfileForm(forms.ModelForm):
    """Form for editing user profile"""
    class Meta:
        model = User
        fields = ('username', 'email', 'first_name', 'last_name', 'full_name', 'phone', 'department')
        labels = {
            'username': 'Логин',
            'email': 'Электронная почта',
            'first_name': 'Имя',
            'last_name': 'Фамилия',
            'full_name': 'Полное имя (ФИО)',
            'phone': 'Телефон',
            'department': 'Отдел',
        }
        widgets = {
            'username': forms.TextInput(attrs={'class': 'form-control', 'readonly': 'readonly'}),
            'email': forms.EmailInput(attrs={'class': 'form-control', 'placeholder': 'Электронная почта'}),
            'first_name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Имя'}),
            'last_name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Фамилия'}),
            'full_name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'ФИО'}),
            'phone': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Телефон'}),
            'department': forms.Select(attrs={'class': 'form-select'}),
        }


class PasswordChangeFormCustom(forms.Form):
    """Form for changing password with validation"""
    old_password = forms.CharField(
        label='Текущий пароль',
        widget=forms.PasswordInput(attrs={'class': 'form-control'}),
        strip=False
    )
    new_password1 = forms.CharField(
        label='Новый пароль',
        widget=forms.PasswordInput(attrs={'class': 'form-control'}),
        strip=False,
        help_text='Минимум 8 символов'
    )
    new_password2 = forms.CharField(
        label='Повторите новый пароль',
        widget=forms.PasswordInput(attrs={'class': 'form-control'}),
        strip=False
    )
    
    def clean_new_password1(self):
        password = self.cleaned_data.get('new_password1')
        if password and len(password) < 8:
            raise forms.ValidationError('Пароль должен быть минимум 8 символов')
        return password
    
    def clean(self):
        cleaned_data = super().clean()
        password1 = cleaned_data.get('new_password1')
        password2 = cleaned_data.get('new_password2')
        
        if password1 and password2:
            if password1 != password2:
                raise forms.ValidationError('Пароли не совпадают')
        
        return cleaned_data