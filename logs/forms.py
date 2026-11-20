from django import forms
from django.contrib.auth import password_validation
from django.contrib.auth.models import Group, User
from django.core.exceptions import ValidationError
from .roles import ensure_roles_exist

class OfficerRegistrationForm(forms.Form):
    ROLE_CHOICES = [
        ("Monitoring Officer", "Monitoring Officer — Read-only log viewing, filters & incident tracking"),
        ("System Administrator", "System Administrator — Classification correction, alert handling & audit access"),
    ]

    first_name = forms.CharField(
        max_length=150,
        required=True,
        label="First Name",
        widget=forms.TextInput(attrs={"placeholder": "e.g., Jane", "class": "form-control"})
    )
    last_name = forms.CharField(
        max_length=150,
        required=True,
        label="Last Name",
        widget=forms.TextInput(attrs={"placeholder": "e.g., Doe", "class": "form-control"})
    )
    username = forms.CharField(
        max_length=150,
        required=True,
        label="Official Username",
        widget=forms.TextInput(attrs={"placeholder": "e.g., jdoe_gov", "class": "form-control"})
    )
    email = forms.EmailField(
        required=True,
        label="Departmental Email",
        widget=forms.EmailInput(attrs={"placeholder": "e.g., jane.doe@gov.in", "class": "form-control"})
    )
    role = forms.ChoiceField(
        choices=ROLE_CHOICES,
        initial="Monitoring Officer",
        required=True,
        label="Assigned Role",
        widget=forms.Select(attrs={"class": "form-select"})
    )
    password = forms.CharField(
        widget=forms.PasswordInput(attrs={"placeholder": "Enter strong password", "class": "form-control"}),
        label="Password",
        help_text="Must contain at least 8 characters and not be entirely numeric."
    )
    confirm_password = forms.CharField(
        widget=forms.PasswordInput(attrs={"placeholder": "Confirm password", "class": "form-control"}),
        label="Confirm Password"
    )

    def clean_username(self):
        username = self.cleaned_data.get("username", "").strip()
        if User.objects.filter(username__iexact=username).exists():
            raise ValidationError("A user with this username already exists.")
        return username

    def clean(self):
        cleaned_data = super().clean()
        password = cleaned_data.get("password")
        confirm_password = cleaned_data.get("confirm_password")

        if password and confirm_password:
            if password != confirm_password:
                self.add_error("confirm_password", "Passwords do not match.")
            else:
                user_instance = User(
                    username=cleaned_data.get("username", ""),
                    email=cleaned_data.get("email", ""),
                    first_name=cleaned_data.get("first_name", ""),
                    last_name=cleaned_data.get("last_name", "")
                )
                try:
                    password_validation.validate_password(password, user=user_instance)
                except ValidationError as error:
                    self.add_error("password", error)

        return cleaned_data

    def save(self):
        ensure_roles_exist()
        user = User.objects.create_user(
            username=self.cleaned_data["username"].strip(),
            email=self.cleaned_data["email"].strip().lower(),
            password=self.cleaned_data["password"],
            first_name=self.cleaned_data["first_name"].strip(),
            last_name=self.cleaned_data["last_name"].strip(),
        )
        role_name = self.cleaned_data.get("role", "Monitoring Officer")
        group = Group.objects.filter(name=role_name).first()
        if group:
            user.groups.add(group)
        return user
