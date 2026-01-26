from rest_framework import routers
from .views import ProductViewSet, CartViewSet, CartItemViewSet


router = routers.DefaultRouter()
router.register(r'products', ProductViewSet, basename='products')
router.register(r'cart', CartViewSet, basename='cart')
router.register(r'cart-item', CartItemViewSet, basename='cartitem')
urlpatterns = router.urls

