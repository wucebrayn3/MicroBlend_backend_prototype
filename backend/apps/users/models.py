from uuid import uuid4

from django.contrib.auth.models import AbstractUser, UserManager
from django.core.exceptions import ValidationError
from django.db import models

from common.constants import ROLE_CHOICES, ROLE_CUSTOMER, ROLE_STAFF, STAFF_ROLE_CHOICES
from common.models import BaseModel
from common.utils import normalize_optional_text


class CustomUserManager(UserManager):
    use_in_migrations = True

    def _create_user(self, username, email, password, **extra_fields):
        email = self.normalize_email(email) if email else None
        phone = normalize_optional_text(extra_fields.get("phone"))
        if not email and not phone:
            raise ValueError("A user requires either an email or mobile number.")

        if not username:
            username = f"user_{uuid4().hex[:12]}"
        extra_fields["phone"] = phone
        user = self.model(username=username, email=email, **extra_fields)
        user.set_password(password)
        user.full_clean()
        user.save(using=self._db)
        return user

    def create_user(self, username=None, email=None, password=None, **extra_fields):
        extra_fields.setdefault("role", ROLE_CUSTOMER)
        extra_fields.setdefault("is_staff", False)
        extra_fields.setdefault("is_superuser", False)
        return self._create_user(username, email, password, **extra_fields)

    def create_superuser(self, username=None, email=None, password=None, **extra_fields):
        extra_fields.setdefault("role", "admin")
        extra_fields.setdefault("is_staff", True)
        extra_fields.setdefault("is_superuser", True)
        return self._create_user(username, email, password, **extra_fields)


class User(AbstractUser, BaseModel):
    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default=ROLE_CUSTOMER)
    staff_role = models.CharField(max_length=20, choices=STAFF_ROLE_CHOICES, blank=True, null=True)
    phone = models.CharField(max_length=20, unique=True, blank=True, null=True)
    email = models.EmailField(unique=True, blank=True, null=True)
    registered_device_id = models.CharField(max_length=128, unique=True, blank=True, null=True)
    is_deleted = models.BooleanField(default=False)

    REQUIRED_FIELDS = ["email"]
    objects = CustomUserManager()

    def clean(self):
        super().clean()
        self.phone = normalize_optional_text(self.phone)
        if self.email:
            self.email = self.__class__.objects.normalize_email(self.email)

        if not self.email and not self.phone:
            raise ValidationError("Email or mobile number is required.")

        if self.role == ROLE_STAFF and not self.staff_role:
            raise ValidationError("Staff accounts require a staff subdivision.")

        if self.role != ROLE_STAFF:
            self.staff_role = None

    @property
    def display_name(self):
        full_name = self.get_full_name().strip()
        return full_name or self.username or self.email or self.phone

    def __str__(self):
        return self.display_name
