"""
API ViewSet for CRUD operations on Product with Redis caching support.
Handles redis failures, product-not-found, and validation errors.
"""
import logging

from django.core.exceptions import ValidationError
from django.http import Http404
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import status, viewsets
from rest_framework.response import Response

from .models import Product
from .serializers import ProductSerializer
from .filters import ProductFilter
from .services.product_service import (
    list_products,
    get_product_by_id,
    create_product,
    update_product,
    delete_product,
)

logger = logging.getLogger(__name__)


class ProductViewSet(viewsets.ModelViewSet):
    """
    ViewSet for Products.

    list:        GET  /products/           → paginated list, Redis-cached  
    retrieve:    GET  /products/{id}/      → single item, Redis-cached  
    create:      POST /products/           → create with category by name  
    update:      PUT  /products/{id}/      → full replace with category by name  
    destroy:     DELETE /products/{id}/    → delete and invalidate cache  

    Uses ProductFilter for filtering, and logs validation or server errors.
    """
    queryset = Product.objects.all()
    serializer_class = ProductSerializer
    filter_backends = [DjangoFilterBackend]
    filterset_class = ProductFilter

    def list(self, request, *args, **kwargs):
        """
        GET /products/
        Returns a paginated, optionally filtered product list from cache or DB.
        Response JSON: { data: {...}, cache_hit: bool }.
        """
        try:
            params = request.query_params
            data, cache_hit = list_products(params)
            return Response({"data": data, "cache_hit": cache_hit},
                            status=status.HTTP_200_OK)
        except ValidationError as ve:
            logger.warning("Validation error in list: %s", ve)
            return Response({"detail": str(ve)},
                            status=status.HTTP_400_BAD_REQUEST)
        except Exception:
            logger.exception("Internal error in list_products")
            return Response({"detail": "Failed to list products due to server error."},
                            status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    def retrieve(self, request, *args, **kwargs):
        """
        GET /products/{id}/
        Returns a single product detail, fetching from cache if available.
        Response JSON: { data: {...}, cache_hit: bool } or 404 if not found.
        """
        try:
            pk = kwargs.get("pk")
            data, cache_hit = get_product_by_id(pk)
            if not data:
                return Response({"detail": "Product not found."},
                                status=status.HTTP_200_OK)
            return Response({"data": data, "cache_hit": cache_hit},
                            status=status.HTTP_200_OK)
        except Http404 as e:
            logger.warning("Product not found: %s", e)
            return Response({"detail": str(e)},
                            status=status.HTTP_404_NOT_FOUND)
        except Exception:
            logger.exception("Failed to retrieve product with ID %s", kwargs.get("pk"))
            return Response({"detail": "Failed to retrieve product due to server error."},
                            status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    def create(self, request, *args, **kwargs):
        """
        POST /products/
        Creates a new product. Expects 'category' in JSON as category name,
        which will be get_or_created in the service layer.
        """
        try:
            data = request.data.copy()
            category_name = data.get("category")
            if not category_name:
                raise ValidationError("The 'category' field is required.")

            data_for_serializer = data.copy()
            data_for_serializer.pop("category", None)

            serializer = self.get_serializer(data=data_for_serializer)
            serializer.is_valid(raise_exception=True)

            payload = serializer.validated_data.copy()
            payload["category"] = category_name

            product = create_product(payload)
            output = self.get_serializer(product).data
            return Response(output, status=status.HTTP_201_CREATED)
        except ValidationError as ve:
            logger.warning("Validation failed in create: %s", ve)
            return Response({"detail": str(ve)},
                            status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            logger.exception("Internal error while creating product: %s", e)
            return Response(
                {"detail": "Product creation failed due to server error.", "msg": str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    def update(self, request, *args, **kwargs):
        """
        PUT /products/{id}/
        Fully replaces a product. Expects 'category' in JSON as category name.
        """
        pk = kwargs.get("pk")
        instance = self.get_object()

        data = request.data.copy()
        if "category" not in data:
            raise ValidationError({"category": "This field is required."})

        cat_name = data.pop("category")

        serializer = self.get_serializer(instance, data=data)
        serializer.is_valid(raise_exception=True)
        valid_data = serializer.validated_data.copy()
        valid_data["category"] = cat_name

        try:
            updated_product, cache_hit = update_product(pk, valid_data)
        except Http404 as e:
            logger.warning("Product not found for update: %s", e)
            return Response({"detail": str(e)},
                            status=status.HTTP_404_NOT_FOUND)
        except Exception:
            logger.exception("Internal error while updating product %s", pk)
            return Response(
                {"detail": "Failed to update product due to server error."},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

        return Response(self.get_serializer(updated_product).data,
                        status=status.HTTP_200_OK)

    def destroy(self, request, *args, **kwargs):
        """
        DELETE /products/{id}/
        Deletes a product by ID, invalidates Redis caches, and returns 204.
        """
        pk = kwargs.get("pk")
        try:
            _, cache_hit = delete_product(pk)
            return Response(
                {"detail": "Delete successful", "cache_hit": cache_hit},
                status=status.HTTP_204_NO_CONTENT
            )
        except Http404 as e:
            logger.warning("Product not found for delete: %s", e)
            return Response({"detail": str(e)},
                            status=status.HTTP_404_NOT_FOUND)
        except ValidationError as ve:
            logger.warning("Validation error in delete: %s", ve)
            return Response({"detail": str(ve)},
                            status=status.HTTP_400_BAD_REQUEST)
        except Exception:
            logger.exception("Unhandled error deleting product %s", pk)
            return Response(
                {"detail": "Product deletion failed due to server error."},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
