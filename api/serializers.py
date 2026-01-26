from rest_framework import serializers
from .models import ProductModel, CartModel, CartItemModel


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

    class Meta:
        model = CartModel
        fields = ["id", "user", "checked_out", "items", "total"]
        read_only_fields = ["id", "user", "items", "total"]

    def get_total(self, obj):
        return str(obj.total())

