import uuid
import logging
from django.core.paginator import Paginator, EmptyPage
from django.db import transaction
from django.core.exceptions import ValidationError
from django.http import Http404

from ..models import Product, Category
from eshop.cache.redis_utils import get_cached, set_cached, invalidate
from eshop.services.metrics import PRODUCT_CACHE, PRODUCT_LATENCY
from eshop.services.perf import log_timing

logger = logging.getLogger("eshop.services.product_service")
logger.info("🎉 Product service logger initialized")

LIST_TTL = 600


def _listing_key(params):
    """Build the Redis key for product list caches based on query parameters."""
    category = params.get("category", "all")
    page = params.get("page", "1")
    page_size = params.get("page_size", "10")
    return f"products:list:category={category}:page={page}:size={page_size}"


def _detail_key(pk):
    """Build the Redis key for a single-product cache entry."""
    return f"products:detail:{pk}"


@log_timing
def list_products(params):
    """
    Retrieve a paginated list of products, applying optional filters, and cache the result.
    Returns a tuple (result_dict, cache_hit: bool).
    """
    try:
        key = _listing_key(params)
        cached = get_cached(key)
        if cached:
            return cached, True

        qs = Product.objects.all()
        if "category" in params:
            qs = qs.filter(category__name=params["category"])

        page = int(params.get("page", 1))
        page_size = int(params.get("page_size", 10))
        paginator = Paginator(qs.values(), page_size)

        try:
            page_obj = paginator.get_page(page)
        except EmptyPage:
            raise ValidationError("Invalid page number.")

        product_list = []
        for obj in page_obj:
            record = {
                k: str(v) if isinstance(v, uuid.UUID) else v
                for k, v in obj.items()
            }
            product_list.append(record)

        if "price_min" in params:
            min_price = float(params["price_min"])
            product_list = [p for p in product_list if float(p["price"]) >= min_price]

        if "price_max" in params:
            max_price = float(params["price_max"])
            product_list = [p for p in product_list if float(p["price"]) <= max_price]

        result = {
            "results": product_list,
            "count": paginator.count,
            "total_pages": paginator.num_pages,
            "page": page,
            "page_size": page_size,
        }

        set_cached(key, result, ex=LIST_TTL)
        return result, False

    except (ValueError, TypeError) as e:
        logger.error(f"Invalid parameter in list_products: {e}")
        raise ValidationError("Invalid query parameters.")
    except Exception as e:
        logger.exception(f"Unhandled error in list_products {e}")
        raise


@log_timing
def get_product_by_id(pk):
    """
    Retrieve a single product by primary key, cache its serialized dict, and return (data, cache_hit).
    If not found, returns (None, False).
    """
    try:
        key = _detail_key(pk)
        cached = get_cached(key)
        if cached:
            return cached, True

        obj = Product.objects.filter(pk=pk).values().first()
        if not obj:
            return None, False

        for field, value in obj.items():
            if isinstance(value, uuid.UUID):
                obj[field] = str(value)

        set_cached(key, obj, None)
        return obj, False

    except Http404 as e:
        logger.warning(e)
        return None, False
    except Exception:
        logger.exception(f"Unhandled error in get_product_by_id for id={pk}")
        return None, False


def _invalidate_listings():
    """Invalidate all cached product-list keys."""
    try:
        invalidate("products:list:*")
    except Exception as e:
        logger.warning("Could not invalidate listings cache: %s", e)


def create_product(payload):
    """
    Create a new Product from a dict of validated fields.
    Expects payload['category'] to be the category name string.
    """
    try:
        category_name = payload.pop("category")
        category_obj, _ = Category.objects.get_or_create(name=category_name)
        payload["category"] = category_obj
        return Product.objects.create(**payload)
    except Exception as e:
        logger.exception("Error creating product: %s", e)
        return None


@log_timing
def update_product(pk, data):
    """
    Update an existing Product by primary key with given data dict.
    If 'category' is present, it's treated as a category-name and get_or_created.
    Returns (updated Product instance, cache_hit=False).
    """
    with transaction.atomic():
        if "category" in data:
            cat_name = data.pop("category")
            category_obj, _ = Category.objects.get_or_create(name=cat_name)
            data["category"] = category_obj

        updated_count = Product.objects.filter(pk=pk).update(**data)
        if updated_count == 0:
            raise Http404(f"Product with id {pk} not found")

        invalidate(_detail_key(pk))
        _invalidate_listings()

        product = Product.objects.get(pk=pk)

    return product, False


@log_timing
def delete_product(pk):
    """
    Delete the Product with given primary key, invalidate caches, and return (None, cache_hit=False).
    Raises Http404 if not found.
    """
    with transaction.atomic():
        try:
            product = Product.objects.get(pk=pk)
        except Product.DoesNotExist:
            raise Http404(f"Product with id {pk} not found")

        product.delete()
        invalidate(_detail_key(pk))
        _invalidate_listings()

    return None, False
