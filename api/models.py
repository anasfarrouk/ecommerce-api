from django.contrib.auth.models import AbstractBaseUser, PermissionsMixin, BaseUserManager
from django.conf import settings
from django.db import models
from django.core.exceptions import ValidationError
from decimal import Decimal


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
    stock_quantity = models.PositiveIntegerField()
    is_active = models.BooleanField(default=True)

class CartModel(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    checked_out = models.BooleanField(default=False)

    class Meta:
        constraints = [models.UniqueConstraint(fields=["user"], condition=models.Q(checked_out=False), name="unique_cart"),]

    def add_or_update_item(self, prd, qty):
        item, created = CartItemModel.objects.update_or_create(cart=self, product=prd, defaults={"quantity":qty})
        return item

    def total(self):
        total = Decimal("0.00")
        items = CartItemModel.objects.filter(cart=self).select_related("product")
        for item in items:
            total += (item.product.unit_price * item.quantity)
        return total

class CartItemModel(models.Model):
    cart = models.ForeignKey(CartModel, on_delete=models.CASCADE)
    product = models.ForeignKey(ProductModel, on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField(blank=False)
    added_at = models.DateTimeField(auto_now_add=True)
    last_modified = models.DateTimeField(auto_now=True)

    class Meta:
        constraints = [models.UniqueConstraint(fields=["cart", "product"], name="unique_product"),]
