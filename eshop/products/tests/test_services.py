from django.test import TestCase
from products.models import Product, Category
from products.services.product_service import (
    list_products, get_product_by_id,
    create_product, update_product, delete_product
)


class ProductServiceTest(TestCase):
    def setUp(self):
        self.category = Category.objects.create(name="Books")
        self.product = Product.objects.create(
            name="Book 1",
            price=200.0,
            stock=10,
            description="Desc",
            category=self.category
        )

    def test_get_product_by_id(self):
        data, cache_hit = get_product_by_id(self.product.pk)
        self.assertEqual(data["name"], self.product.name)
        self.assertFalse(cache_hit)

    def test_list_products(self):
        params = {"category": "Books", "page": "1", "page_size": "10"}
        data, cache_hit = list_products(params)
        self.assertEqual(data["results"][0]["name"], self.product.name)
        self.assertFalse(cache_hit)

    def test_create_product(self):
        payload = {
            "name": "Book 2",
            "price": 150.0,
            "stock": 5,
            "description": "Another book",
            "category": "Books"
        }
        product = create_product(payload)
        self.assertIsNotNone(product)
        self.assertEqual(product.name, "Book 2")

    def test_update_product(self):
        updated_data = {
            "name": "Book 1 Updated",
            "price": 250.0,
            "stock": 15,
            "description": "Updated Desc",
            "category": "Books"
        }
        updated_product, cache_hit = update_product(self.product.pk, updated_data)
        self.assertEqual(updated_product.name, "Book 1 Updated")

    def test_delete_product(self):
        delete_product(self.product.pk)
        self.assertFalse(Product.objects.filter(pk=self.product.pk).exists())
