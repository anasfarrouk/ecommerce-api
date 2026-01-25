from django.contrib.auth.models import AbstractBaseUser, PermissionsMixin, BaseUserManager
from django.conf import settings
from django.db import models
from django.core.exceptions import ValidationError
from decimal import Decimal, ROUND_HALF_UP


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
    
class SelectedProductModel(models.Model):
    product = models.OneToOneField(ProductModel,
                                   on_delete=models.CASCADE,
                                   primary_key=True,
                                   related_name="selected_by")
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    quantity_selected = models.PositiveIntegerField()
    selling_price = models.DecimalField(max_digits=5, decimal_places=2, editable=False)

    class Meta:
        constraints = [models.UniqueConstraint(fields=['user', 'product'], name='unique_user_product')]

    def clean(self):
        if self.quantity_selected is None or self.quantity_selected < 0:
            raise ValidationError({'quantity_selected': 'Must be a non-negative integer.'})
        if not hasattr(self.product, 'unit_price') or self.product.unit_price is None:
            raise ValidationError({'product': 'Related product must have a unit_price.'})

    def save(self, *args, **kwargs):
        # Ensure product is loaded (handle unsaved product instance)
        unit_price = getattr(self.product, 'unit_price', None)
        if unit_price is None:
            # Try to fetch from DB if product is a FK and not fully loaded
            if self.product_id:
                unit_price = ProductModel.objects.filter(pk=self.product_id).values_list('unit_price', flat=True).first()
        if unit_price is None:
            raise ValueError('product.unit_price is required to calculate selling_price.')

        # Use Decimal arithmetic
        q = Decimal(self.quantity_selected)
        up = Decimal(unit_price)
        total = (q * up).quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)
        self.selling_price = total

        # Run full clean (optional) to enforce constraints
        self.full_clean(exclude=['selling_price'])

        super().save(*args, **kwargs)

