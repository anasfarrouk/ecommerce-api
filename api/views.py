from django.shortcuts import render
from .models import ProductModel, SelectedProductModel
from .serializers import ProductSerializer, SelectedProductSerializer
from rest_framework import viewsets, filters, mixins
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.permissions import AllowAny, IsAuthenticated


# Create your views here.
class ProductViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = ProductModel.objects.all()
    permission_classes = [AllowAny]
    serializer_class = ProductSerializer
    filter_backends = [DjangoFilterBackend ,filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['category', 'unit_price']
    ordering_fields = ['unit_price',]
    search_fields = ['name', 'description']

class SelectedProductViewSet(mixins.CreateModelMixin,
                             mixins.UpdateModelMixin,
                             mixins.DestroyModelMixin,
                             viewsets.GenericViewSet):
    queryset = SelectedProductModel.objects.all()
    permission_classes = [IsAuthenticated]
    serializer_class = SelectedProductSerializer
    lookup_field = "product"

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)



