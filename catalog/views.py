import logging
from django_filters import rest_framework as filters
from rest_framework import permissions, viewsets
from rest_framework.filters import SearchFilter, OrderingFilter
from .models import Category, Product
from .serializers import CategorySerializer, ProductSerializer

log = logging.getLogger("catalog.api")

class IsAdminOrReadOnly(permissions.BasePermission):
    """
    Allow read-only to anyone; write actions require staff.
    """
    def has_permission(self, request, view):
        if request.method in ("GET", "HEAD", "OPTIONS"):
            return True
        return bool(request.user and request.user.is_staff)

class ProductFilter(filters.FilterSet):
    price_min = filters.NumberFilter(field_name="price", lookup_expr="gte")
    price_max = filters.NumberFilter(field_name="price", lookup_expr="lte")
    category = filters.NumberFilter(field_name="category__id", lookup_expr="exact")
    category_slug = filters.CharFilter(field_name="category__slug", lookup_expr="iexact")
    in_stock = filters.BooleanFilter(method="filter_in_stock")

    class Meta:
        model = Product
        fields = ["is_active", "category", "category_slug", "in_stock"]

    def filter_in_stock(self, queryset, name, value):
        return queryset.filter(stock_qty__gt=0) if value else queryset

class CategoryViewSet(viewsets.ModelViewSet):
    queryset = Category.objects.all()
    serializer_class = CategorySerializer
    permission_classes = [IsAdminOrReadOnly]
    filter_backends = [SearchFilter, OrderingFilter, filters.DjangoFilterBackend]
    search_fields = ["name", "description"]
    ordering_fields = ["name"]
    ordering = ["name"]

    def perform_create(self, serializer):
        obj = serializer.save()
        log.info("Category created id=%s name=%s", obj.id, obj.name)

    def perform_update(self, serializer):
        obj = serializer.save()
        log.info("Category updated id=%s name=%s", obj.id, obj.name)

    def perform_destroy(self, instance):
        log.warning("Category deleted id=%s name=%s", instance.id, instance.name)
        return super().perform_destroy(instance)

class ProductViewSet(viewsets.ModelViewSet):
    queryset = Product.objects.select_related("category").all()
    serializer_class = ProductSerializer
    permission_classes = [IsAdminOrReadOnly]
    filter_backends = [SearchFilter, OrderingFilter, filters.DjangoFilterBackend]
    search_fields = ["title", "description", "sku"]
    ordering_fields = ["price", "created_at", "title"]
    ordering = ["-created_at"]
    filterset_class = ProductFilter

    def list(self, request, *args, **kwargs):
        q = request.query_params.get("search") or request.query_params.get("q")
        if q:
            log.debug("List products q='%s'", q)
        return super().list(request, *args, **kwargs)

    def perform_create(self, serializer):
        obj = serializer.save()
        log.info(
            "Product created id=%s sku=%s title=%s price=%s stock=%s",
            obj.id, obj.sku, obj.title, obj.price, obj.stock_qty
        )

    def perform_update(self, serializer):
        obj = serializer.save()
        log.info(
            "Product updated id=%s sku=%s title=%s price=%s stock=%s",
            obj.id, obj.sku, obj.title, obj.price, obj.stock_qty
        )

    def perform_destroy(self, instance):
        log.warning("Product deleted id=%s sku=%s title=%s", instance.id, instance.sku, instance.title)
        return super().perform_destroy(instance)
