from rest_framework.routers import DefaultRouter
from django.urls import path, include
from .views import *
from .models import *

router = DefaultRouter()
router.register("products", ProductViewSet, basename=Product)
router.register("customers", CustomerViewSet, basename=Customer)

urlpatterns = [
    path("", include(router.urls)),
    path("auth-login/", CustomerLoginView.as_view()),
    path("get-customer-data/", GetCustomerDetails.as_view()),
    path("update-customer-data/", UpdateCustomer.as_view())

    #path("get-data/", GetMemberData.as_view()),
]
