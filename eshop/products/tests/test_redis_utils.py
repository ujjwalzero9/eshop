from django.test import TestCase
from eshop.cache.redis_utils import set_cached, get_cached, invalidate

class RedisUtilsTest(TestCase):
    def test_set_and_get_cached(self):
        key = "test:key"
        value = {"name": "RedisBook", "price": 299}
        success = set_cached(key, value, ex=10)
        self.assertTrue(success)

        cached_value = get_cached(key)
        self.assertEqual(cached_value, value)

    def test_invalidate_cached(self):
        key = "test:delete"
        value = {"x": 1}
        set_cached(key, value)
        deleted_count = invalidate("test:*")
        self.assertGreaterEqual(deleted_count, 1)

        self.assertIsNone(get_cached(key))
