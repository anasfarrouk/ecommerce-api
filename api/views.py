from django.shortcuts import render
from .models import ProductModel, CartModel, CartItemModel
from .serializers import ProductSerializer, CartSerializer, CartItemSerializer
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import viewsets, filters, mixins, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import AllowAny, IsAuthenticated


# Create your views here.
def get_user_cart(user):
    cart, _ = CartModel.objects.get_or_create(user=user, checked_out=False)
    return cart

class ProductViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = ProductModel.objects.all()
    permission_classes = [AllowAny]
    serializer_class = ProductSerializer
    filter_backends = [DjangoFilterBackend ,filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['category', 'unit_price']
    ordering_fields = ['unit_price',]
    search_fields = ['name', 'description']

class CartViewSet(viewsets.GenericViewSet, mixins.RetrieveModelMixin):
    queryset = CartModel.objects.all()
    serializer_class = CartSerializer
    permission_classes = [IsAuthenticated]

    def get_object(self):
        # always return the current user's active cart
        return get_user_cart(self.request.user)

    @action(detail=False, methods=["get"])
    def me(self, request):
        cart = self.get_object()
        return Response(self.get_serializer(cart).data)

    @action(detail=False, methods=["post"])
    def checkout(self, request):
        cart = self.get_object()
        cart.checked_out = True
        cart.save()
        return Response({"status": "checked_out"}, status=status.HTTP_200_OK)

class CartItemViewSet(viewsets.ModelViewSet):
    queryset = CartItemModel.objects.all()
    serializer_class = CartItemSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        # only allow access to items in the requesting user's active cart
        cart = get_user_cart(self.request.user)
        return CartItemModel.objects.filter(cart=cart).select_related("product")

    def perform_create(self, serializer):
        cart = get_user_cart(self.request.user)
        product = serializer.validated_data["product"]
        qty = serializer.validated_data.get("quantity", 1)
        item = cart.add_or_update_item(product, qty)
        serializer.instance = item

    def perform_update(self, serializer):
        serializer.save()

    def destroy(self, request, *args, **kwargs):
        return super().destroy(request, *args, **kwargs)

