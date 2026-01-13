from django.contrib.auth.models import AbstractBaseUser, PermissionsMixin, BaseUserManager
from django.db import models


# Create your models here.
class MyUserManager(BaseUserManager):
    def create_user(self, email, password=None, **extra_fields):
        if not email:
            raise ValueError('Email required')
        email = self.normalize_email(email)
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user
    def create_superuser(self, email, password, **extra_fields):
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        return self.create_user(email, password, **extra_fields)

class User(AbstractBaseUser, PermissionsMixin):
    first_name = models.CharField(max_length=30, default='')
    last_name = models.CharField(max_length=30, default='')
    email = models.EmailField(unique=True)
    date_joined = models.DateField(auto_now_add=True)
    shipping_address = models.TextField()
    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)

    objects = MyUserManager()
    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['shipping_address','first_name','last_name']  

class CategoryModel(models.Model):
    name = models.CharField(max_length=30, unique=True)

class ProductModel(models.Model):
    name = models.CharField(max_length=250, blank=False, null=False)
    category = models.ForeignKey(CategoryModel, on_delete=models.CASCADE)
    description = models.TextField()
    unit_price = models.DecimalField(max_digits=5, decimal_places=2)
    stock_quantity = models.IntegerField()
