from django.urls import include, path
from rest_framework.routers import DefaultRouter
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView
from .views import (
    CustomerViewSet,
    DeviceViewSet,
    InventoryViewSet,
    LicenseCheckView,
    OfflineTokenView,
    RepairViewSet,
    SaleViewSet,
)

router = DefaultRouter()
router.register('inventory', InventoryViewSet, basename='inventory')
router.register('customers', CustomerViewSet, basename='customer')
router.register('sales', SaleViewSet, basename='sale')
router.register('repairs', RepairViewSet, basename='repair')
router.register('devices', DeviceViewSet, basename='device')

urlpatterns = [
    path('', include(router.urls)),
    path('auth/login/', TokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('auth/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    path('license/check/', LicenseCheckView.as_view(), name='license_check'),
    path('license/offline-token/', OfflineTokenView.as_view(), name='offline_token'),
]

