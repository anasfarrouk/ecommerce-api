from rest_framework import routers
from .views import ProductViewSet, SelectedProductViewSet


router = routers.SimpleRouter()
router.register(r'products', ProductViewSet)
router.register(r'selected-products', SelectedProductViewSet)
urlpatterns = router.urls

