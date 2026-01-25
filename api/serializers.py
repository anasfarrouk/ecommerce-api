from rest_framework import serializers
from .models import ProductModel, SelectedProductModel


class ProductSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProductModel
        fields = '__all__'

class SelectedProductSerializer(serializers.ModelSerializer):
    class Meta:
        model = SelectedProductModel
        fields = '__all__'
        read_only_fields = ['user', 'selling_price']


    def validate(self, attrs):
        request = self.context.get('request')
        user = request.user if request else attrs.get('user')
        product = attrs.get('product') or getattr(self.instance, 'product', None)

        # For create: instance is None
        if self.instance is None:
            if SelectedProductModel.objects.filter(user=user, product=product).exists():
                raise serializers.ValidationError('You already have a selected product for this product.')
        else:
            # For update: ensure changing product or user doesn't create a duplicate
            new_user = user or self.instance.user
            new_product = product or self.instance.product
            qs = SelectedProductModel.objects.filter(user=new_user, product=new_product).exclude(product=self.instance.product)
            if qs.exists():
                raise serializers.ValidationError('Another selected product with this product already exists for this user.')
        return attrs

    def create(self, validated_data):
        # ensure user is set from request
        request = self.context.get('request')
        if request and not validated_data.get('user'):
            validated_data['user'] = request.user
        return super().create(validated_data)

