from rest_framework_simplejwt.tokens import AccessToken
from rest_framework.test import APIClient, APITestCase
from django.contrib.auth import get_user_model
from django.test import TestCase
from .models import CategoryModel, ProductModel, CartModel, CartItemModel, OrderModel
from .hook import stripe_webhook
import json


# Include an appropriate `Authorization:` header on all requests.
User = get_user_model()

class JWTTests(APITestCase):
    def setUp(self):
        self.user = User.objects.create_user(email="test@domain.com", password="testpass")
        self.client = APIClient()

    def test_jwt_flow(self):
        resp1 = self.client.post("/auth/jwt/create", {"email":"test@domain.com", "password":"testpass"}, format="json")
        assert resp1.status_code == 200, resp1.content
        data = resp1.json()
        access = data["access"]
        refresh = data["refresh"]

        self.client.credentials(HTTP_AUTHORIZATION=f"JWT {access}")
        resp2 = self.client.post("/auth/jwt/verify", {"token": access}, format="json")
        assert resp2.status_code == 200, resp2.content

        resp3 = self.client.post("/auth/jwt/refresh", {"refresh":refresh}, format="json")
        assert resp3.status_code == 200, resp3.content
        assert "access" in resp3.json()

class ProductTests(APITestCase):
    @classmethod
    def setUpTestData(cls):
        cls.user = User.objects.create_user(email="test@domain.com", password="testpass")
        cls.category = CategoryModel.objects.create(name="accessories")
        cls.product = ProductModel.objects.create(
            stripe_product_id="prod_Trxv6SU8dRM0Hd",
            name="watch",
            category=cls.category,
            description="none",
            unit_price=10,
            stripe_price_id="price_1SuDzx7y5k9qV41PNpu83NJt",
            stock_quantity=100,
        )

    def setUp(self):
        self.client = APIClient()
        self.client.force_authenticate(user=self.user)

    def test_products_listing(self):
        resp1 = self.client.get("/api/products/" + "?ordering=unit_price", format="json")
        assert resp1.status_code == 200, (resp1.status_code, resp1.content)
        resp2 = self.client.get(f"/api/products/{self.product.id}/", format="json")
        assert resp2.status_code == 200, (resp2.status_code, resp2.content)

    def test_shopping_flow(self):
        resp1 = self.client.post("/api/cart-item/", {"product_id":self.product.id, "quantity":2}, format="json")
        assert resp1.status_code == 201, (resp1.status_code, resp1.content)
        item_id = resp1.json()["id"]
        resp2 = self.client.put(f"/api/cart-item/{item_id}/", {"quantity":5}, format="json")
        assert resp2.status_code == 200, (resp2.status_code, resp2.content)
        data = resp2.json()
        assert data["quantity"] == 5, data["quantity"]
        resp3 = self.client.get("/api/cart/me/", format="json")
        assert resp3.status_code == 200, (resp3.status_code, resp3.content)
        resp5 = self.client.post("/api/cart/checkout/", format="json")
        assert resp5.status_code == 200, (resp5.status_code, resp5.content)
        resp6 = self.client.get("/api/orders/", format="json")
        assert resp6.status_code == 200, (resp6.status_code, resp6.content)

