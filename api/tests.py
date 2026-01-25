from rest_framework_simplejwt.tokens import AccessToken
from rest_framework.test import APIClient
from django.contrib.auth import get_user_model
from django.test import TestCase
from .models import CategoryModel, ProductModel

# Include an appropriate `Authorization:` header on all requests.
User = get_user_model()

class JWTTests(TestCase):
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

class ProductTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(email="test@domain.com", password="testpass")
        self.category = CategoryModel.objects.create(name="accessories")
        self.product = ProductModel.objects.create(name="watch",
                                                   category=self.category,
                                                   description="none",
                                                   unit_price=10,
                                                   stock_quantity=100)
        self.client = APIClient()
        self.client.force_authenticate(user=self.user)

    def test_products_listing(self):
        response = self.client.get("/api/products/", format="json")
        assert response.status_code == 200, response.content

    def test_selecting_product(self):
        resp1 = self.client.post("/api/selected-products/", {"product":self.product.id, "quantity_selected":2}, format="json")
        assert resp1.status_code == 201, (resp1.status_code, resp1.content)
        

        resp2 = self.client.put(f"/api/selected-products/{self.product.id}/", {"product":self.product.id, "quantity_selected":10}, format="json")
        assert resp2.status_code == 200, (resp2.status_code, resp2.content)
        
        resp3 = self.client.delete(f"/api/selected-products/{self.product.id}/", format="json")
        assert resp3.status_code == 204, (resp3.status_code, resp3.content)
        

