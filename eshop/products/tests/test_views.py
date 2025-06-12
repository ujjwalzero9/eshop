from rest_framework.test import APITestCase
from django.urls import reverse
from products.models import Product, Category


class ProductAPITest(APITestCase):

    def setUp(self):
        self.cat = Category.objects.create(name="Books")

        self.product = Product.objects.create(
            name="Book A",
            price=150.0,
            stock=10,  # ✅ Required field added
            category=self.cat,
            description="Nice book"
        )

    def test_list_products(self):
        url = reverse("product-list")
        response = self.client.get(url, {"page": 1})
        self.assertEqual(response.status_code, 200)

    def test_get_product(self):
        url = reverse("product-detail", args=[self.product.id])
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["data"]["name"], "Book A")

    def test_create_product(self):
        url = reverse("product-list")
        payload = {
            "name": "New Book",
            "price": 250.0,
            "stock": 5,  # ✅ Required field added
            "description": "Cool book",
            "category": str(self.cat.id)  # ✅ Use category ID, not name
        }
        response = self.client.post(url, payload, format="json")
        self.assertEqual(response.status_code, 201)
        self.assertEqual(response.data["name"], "New Book")
