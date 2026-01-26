from rest_framework_simplejwt.tokens import AccessToken
from rest_framework.test import APIClient, APITestCase
from django.contrib.auth import get_user_model
from django.test import TestCase
from .models import CategoryModel, ProductModel, CartModel, CartItemModel

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
            name="watch",
            category=cls.category,
            description="none",
            unit_price=10,
            stock_quantity=100,
        )
        # create cart and item directly in DB so other tests see it
        cls.cart = CartModel.objects.create(user=cls.user)
        cls.item = CartItemModel.objects.create(cart=cls.cart, product=cls.product, quantity=2)

    def setUp(self):
        self.client = APIClient()
        self.client.force_authenticate(user=self.user)

    def test_products_listing(self):
        response = self.client.get("/api/products/" + "?ordering=unit_price", format="json")
        assert response.status_code == 200, (response.status_code, response.content)

    def test_retrieving_item(self):
        response = self.client.get(f"/api/cart-item/{self.item.id}/", format="json")
        assert response.status_code == 200, (response.status_code, response.content)

    def test_updating_item(self):
        response = self.client.put(f"/api/cart-item/{self.item.id}/", {"quantity":5}, format="json")
        assert response.status_code == 200, (response.status_code, response.content)
        data = response.json()
        assert data["quantity"] == 5, data["quantity"]

    def test_retrieving_cart(self):
        response = self.client.get("/api/cart/me/", format="json")
        assert response.status_code == 200, (response.status_code, response.content)

    def test_removing_item(self):
        response = self.client.delete(f"/api/cart-item/{self.item.id}/", format="json")
        assert response.status_code == 204, (response.status_code, response.content)


