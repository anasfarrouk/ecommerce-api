from rest_framework import serializers
from .models import ProductModel, CartModel, CartItemModel, OrderModel
from typing import List, Dict, Any


class ProductSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProductModel
        fields = '__all__'

class CartItemSerializer(serializers.ModelSerializer):
    product = ProductSerializer(read_only=True)
    product_id = serializers.PrimaryKeyRelatedField(required=False, write_only=True, source="product", queryset=ProductModel.objects.all())

    class Meta:
        model = CartItemModel
        fields = ["id", "cart", "product", "product_id", "quantity", "added_at", "last_modified"]
        read_only_fields = ["id", "cart", "added_at", "last_modified"]

    def create(self, valideted_data):
        return CartItemModel.objects.create(**validated_data)

class CartSerializer(serializers.ModelSerializer):
    items = CartItemSerializer(source="cartitemmodel_set", many=True, read_only=True)
    total = serializers.SerializerMethodField()
    user = serializers.PrimaryKeyRelatedField(read_only=True)

    class Meta:
        model = CartModel
        fields = ["id", "user", "checked_out", "items", "total"]
        read_only_fields = ["id", "user", "items", "total"]

    def get_total(self, obj) -> str:
        return str(obj.total())

class OrderSerializer(serializers.ModelSerializer):
    items = serializers.SerializerMethodField()
    amount = serializers.DecimalField(max_digits=12, decimal_places=2, read_only=True)
    user = serializers.PrimaryKeyRelatedField(read_only=True)
    stripe_session_id = serializers.CharField(read_only=True)
    paid = serializers.BooleanField(read_only=True)
    created_at = serializers.DateTimeField(read_only=True)

    class Meta:
        model = OrderModel
        fields = ["id", "user", "cart", "items", "amount", "stripe_session_id", "paid", "created_at"]
        read_only_fields = ["id", "user", "items", "amount", "stripe_session_id", "paid", "created_at"]

    def get_items(self, order) -> List[Dict[str, Any]]:
        # load cart items for the order's cart
        qs = CartItemModel.objects.filter(cart=order.cart).select_related("product")
        return CartItemSerializer(qs, many=True).data


