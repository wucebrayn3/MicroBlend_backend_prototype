from uuid import uuid4

from django import forms
from django.contrib.auth.forms import ReadOnlyPasswordHashField

from common.constants import ROLE_ADMIN, ROLE_STAFF

from .models import User


class UserAdminCreationForm(forms.ModelForm):
    username = forms.CharField(required=False, help_text="Optional. Leave blank to auto-generate a username.")
    password1 = forms.CharField(label="Password", strip=False, widget=forms.PasswordInput)
    password2 = forms.CharField(label="Password confirmation", strip=False, widget=forms.PasswordInput)

    class Meta:
        model = User
        fields = (
            "username",
            "first_name",
            "last_name",
            "email",
            "phone",
            "role",
            "staff_role",
            "registered_device_id",
            "is_active",
        )

    def clean(self):
        cleaned_data = super().clean()
        password1 = cleaned_data.get("password1")
        password2 = cleaned_data.get("password2")
        role = cleaned_data.get("role")
        staff_role = cleaned_data.get("staff_role")
        email = cleaned_data.get("email")
        phone = cleaned_data.get("phone")

        if password1 and password2 and password1 != password2:
            self.add_error("password2", "The two password fields didn't match.")

        if not email and not phone:
            raise forms.ValidationError("Email or mobile number is required.")

        if role == ROLE_STAFF and not staff_role:
            self.add_error("staff_role", "Staff accounts require a staff subdivision.")

        if role != ROLE_STAFF:
            cleaned_data["staff_role"] = None

        return cleaned_data

    def save(self, commit=True):
        user = super().save(commit=False)
        user.username = self.cleaned_data.get("username") or f"user_{uuid4().hex[:12]}"
        user.set_password(self.cleaned_data["password1"])

        if user.role == ROLE_ADMIN:
            user.is_staff = True

        if commit:
            user.save()
        return user


class UserAdminChangeForm(forms.ModelForm):
    password = ReadOnlyPasswordHashField(required=False)

    class Meta:
        model = User
        fields = "__all__"

    def clean(self):
        cleaned_data = super().clean()
        role = cleaned_data.get("role")
        staff_role = cleaned_data.get("staff_role")
        email = cleaned_data.get("email")
        phone = cleaned_data.get("phone")

        if not email and not phone:
            raise forms.ValidationError("Email or mobile number is required.")

        if role == ROLE_STAFF and not staff_role:
            self.add_error("staff_role", "Staff accounts require a staff subdivision.")

        if role != ROLE_STAFF:
            cleaned_data["staff_role"] = None

        if role == ROLE_ADMIN:
            cleaned_data["is_staff"] = True

        return cleaned_data
