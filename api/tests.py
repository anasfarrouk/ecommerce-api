from rest_framework_simplejwt.tokens import AccessToken
from rest_framework.test import APIClient
from django.contrib.auth import get_user_model
from django.test import TestCase

# Include an appropriate `Authorization:` header on all requests.
User = get_user_model()

class ProtectedEndpointTests(TestCase):
    def setUp(self):
        user = User.objects.create_user(username="testuser", password='testpass')
        token = str(AccessToken.for_user(user))
        client = APIClient()
        client.credentials(HTTP_AUTHORIZATION=f'JWT {token}')

    def test_protected_endpoint(self):
        url = "/auth/jwt/verify" 
        resp = self.client.get(url)
        self.assertEqual(resp.status_code, 200)
