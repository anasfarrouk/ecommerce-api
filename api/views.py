from django.conf import settings
from .models import ProductModel, CartModel, CartItemModel, OrderModel
from .serializers import ProductSerializer, CartSerializer, CartItemSerializer, OrderSerializer
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import viewsets, filters, mixins, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import AllowAny, IsAuthenticated
import stripe


# Create your views here.
stripe.api_key = settings.STRIPE_SECRET_KEY
FRONTEND_SUCCESS_URL = settings.FRONTEND_SUCCESS_URL
FRONTEND_CANCEL_URL = settings.FRONTEND_CANCEL_URL

def get_user_cart(user):
    cart, created = CartModel.objects.get_or_create(user=user, checked_out=False)
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
        return get_user_cart(self.request.user)

    @action(detail=False, methods=["get"])
    def me(self, request):
        cart = self.get_object()
        return Response(self.get_serializer(cart).data)

    @action(detail=False, methods=["post"])
    def checkout(self, request):
        cart = self.get_object()

        if cart.checked_out:
            return Response({"detail": "Cart already checked out."}, status=status.HTTP_400_BAD_REQUEST)

        items = CartItemModel.objects.filter(cart=cart).select_related("product")
        if not items.exists():
            return Response({"detail": "Cart is empty."}, status=status.HTTP_400_BAD_REQUEST)

        # Create order and mark cart checked_out atomically using your classmethod
        try:
            with transaction.atomic():
                order = OrderModel.create_from_cart(cart=cart, user=request.user)
        except ValueError as exc:
            return Response({"detail": str(exc)}, status=status.HTTP_400_BAD_REQUEST)

        # Build Stripe line items (use saved stripe_price_id when present)
        line_items = []
        for item in items:
            prod = item.product
            unit_amount_cents = int(prod.unit_price * Decimal("100"))
            if prod.stripe_price_id:
                line_items.append({"price": prod.stripe_price_id, "quantity": item.quantity})
            else:
                line_items.append({
                    "price_data": {
                        "currency": "usd",
                        "product_data": {"name": prod.name},
                        "unit_amount": unit_amount_cents,
                    },
                    "quantity": item.quantity,
                })

        try:
            session = stripe.checkout.Session.create(
                payment_method_types=["card"],
                mode="payment",
                line_items=line_items,
                success_url=settings.FRONTEND_SUCCESS_URL + "?session_id={CHECKOUT_SESSION_ID}",
                cancel_url=settings.FRONTEND_CANCEL_URL,
                metadata={"order_id": str(order.id)},
            )
            order.stripe_session_id = session.id
            order.save(update_fields=["stripe_session_id"])
            return Response({"checkout_url": session.url, "order_id": order.id}, status=status.HTTP_200_OK)

        except stripe.error.StripeError as e:
            # rollback: delete order and un-checkout cart
            with transaction.atomic():
                order.delete()
                cart.checked_out = False
                cart.save(update_fields=["checked_out"])
            return Response({"detail": "Stripe error", "error": str(e)}, status=status.HTTP_502_BAD_GATEWAY)

#class CartViewSet(viewsets.GenericViewSet, mixins.RetrieveModelMixin):
#    queryset = CartModel.objects.all()
#    serializer_class = CartSerializer
#    permission_classes = [IsAuthenticated]
#
#    def get_object(self):
#        # always return the current user's active cart
#        return get_user_cart(self.request.user)
#
#    @action(detail=False, methods=["get"])
#    def me(self, request):
#        cart = self.get_object()
#        return Response(self.get_serializer(cart).data)
#
#    @action(detail=False, methods=["post"])
#    def checkout(self, request):
#        cart = self.get_object()
#        order = Order.objects.create(
#                user = self.request.user,
#                stripe_session_id = '',
#                paid = False
#        cart.checked_out = True
#        cart.save()
#        return Response({"status": "checked_out"}, status=status.HTTP_200_OK)

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

class OrderViewSet(viewsets.GenericViewSet, mixins.ListModelMixin, mixins.RetrieveModelMixin):
    queryset = OrderModel.objects.all()
    serializer_class = OrderSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        # only allow users to see their own orders
        return OrderModel.objects.filter(user=self.request.user).order_by("-created_at")

    
