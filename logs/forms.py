from django import forms
from django.contrib.auth import password_validation
from django.contrib.auth.models import Group, User
from django.core.exceptions import ValidationError
from .models import LogEntry
from .roles import ensure_roles_exist

class SimpleRegistrationForm(forms.Form):
    ROLE_CHOICES = [
        ("User", "Regular User (View dashboard, search logs, add new logs)"),
        ("Admin", "Administrator (Full access, resolve alerts, manage settings)"),
    ]

    username = forms.CharField(
        max_length=150,
        required=True,
        label="Username",
        widget=forms.TextInput(attrs={"placeholder": "Choose a username", "class": "form-control"})
    )
    email = forms.EmailField(
        required=True,
        label="Email Address",
        widget=forms.EmailInput(attrs={"placeholder": "name@example.com", "class": "form-control"})
    )
    role = forms.ChoiceField(
        choices=ROLE_CHOICES,
        initial="User",
        required=True,
        label="Account Role",
        widget=forms.Select(attrs={"class": "form-select"})
    )
    password = forms.CharField(
        widget=forms.PasswordInput(attrs={"placeholder": "Enter password", "class": "form-control"}),
        label="Password",
        help_text="Minimum 8 characters."
    )
    confirm_password = forms.CharField(
        widget=forms.PasswordInput(attrs={"placeholder": "Re-enter password", "class": "form-control"}),
        label="Confirm Password"
    )

    def clean_username(self):
        username = self.cleaned_data.get("username", "").strip()
        if User.objects.filter(username__iexact=username).exists():
            raise ValidationError("This username is already taken. Please choose another.")
        return username

    def clean(self):
        cleaned = super().clean()
        p1 = cleaned.get("password")
        p2 = cleaned.get("confirm_password")
        if p1 and p2 and p1 != p2:
            self.add_error("confirm_password", "Passwords do not match.")
        return cleaned

    def save(self):
        ensure_roles_exist()
        role = self.cleaned_data.get("role", "User")
        is_admin = role == "Admin"

        user = User.objects.create_user(
            username=self.cleaned_data["username"].strip(),
            email=self.cleaned_data["email"].strip().lower(),
            password=self.cleaned_data["password"],
            is_staff=is_admin
        )

        group_name = "System Administrator" if is_admin else "Monitoring Officer"
        group = Group.objects.filter(name=group_name).first()
        if group:
            user.groups.add(group)

        return user

class LogEntryForm(forms.Form):
    APP_CHOICES = [
        ("Student Portal", "Student Portal"),
        ("Exam System", "Examination System"),
        ("Fee Gateway", "Fee Payment Gateway"),
        ("Auth Service", "Authentication Service"),
        ("Database Server", "Database Server"),
        ("Library System", "Library Management"),
        ("Hostel Portal", "Hostel Allocation"),
        ("Other", "Other / Custom Application"),
    ]

    SEVERITY_CHOICES = [
        ("AUTO", "⚡ Auto-classify based on content (Recommended)"),
        ("INFO", "Info (Normal event)"),
        ("WARNING", "Warning (Potential issue)"),
        ("ERROR", "Error (Application failure)"),
        ("CRITICAL", "Critical (System outage / security threat)"),
    ]

    source_application = forms.ChoiceField(
        choices=APP_CHOICES,
        initial="Student Portal",
        label="Application / Service",
        widget=forms.Select(attrs={"class": "form-select"})
    )
    custom_application = forms.CharField(
        max_length=120,
        required=False,
        label="Custom Application Name (if 'Other')",
        widget=forms.TextInput(attrs={"placeholder": "e.g. Attendance System", "class": "form-control"})
    )
    message = forms.CharField(
        widget=forms.Textarea(attrs={
            "placeholder": "Enter log message or error description (e.g. 'Database connection timed out' or 'User login succeeded')",
            "rows": 3,
            "class": "form-control"
        }),
        label="Log Message",
        help_text="Keywords like 'error', 'failed', 'warning', 'timeout', or 'login' will be automatically analyzed."
    )
    severity = forms.ChoiceField(
        choices=SEVERITY_CHOICES,
        initial="AUTO",
        label="Log Level",
        widget=forms.Select(attrs={"class": "form-select"})
    )
    ip_address = forms.CharField(
        max_length=45,
        required=False,
        label="Client IP Address (Optional)",
        widget=forms.TextInput(attrs={"placeholder": "192.168.1.10", "class": "form-control"})
    )
    status_code = forms.IntegerField(
        required=False,
        label="HTTP Status Code (Optional)",
        widget=forms.NumberInput(attrs={"placeholder": "e.g. 200, 401, 500", "class": "form-control"})
    )
