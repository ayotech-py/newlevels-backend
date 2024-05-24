from rest_framework.routers import DefaultRouter
from django.urls import path, include
from .views import *
from .models import *


router = DefaultRouter()
router.register("products", ProductViewSet, basename=Product)
router.register("customers", CustomerViewSet, basename=Customer)
router.register(r'chatrooms', ChatRoomViewSet, basename=ChatRoom)
router.register(r'messages', MessageViewSet, basename=Message)

urlpatterns = [
    path("", include(router.urls)),
    path("auth-login/", CustomerLoginView.as_view()),
    path("get-customer-data/", GetCustomerDetails.as_view()),
    path("update-customer-data/", UpdateCustomer.as_view()),
    path('send_message/', SendMessageView.as_view(), name='send_message'),
    path('password_reset/', PasswordResetRequestView.as_view(), name='password_reset_request'),
    path('password_reset_confirm/<uidb64>/<token>/', PasswordResetConfirmView.as_view(), name='password_reset_confirm'),
    path('approve/<uuid:unique_token>/', ApproveProduct.as_view(), name='approve_product'),
    path('feature/<uuid:unique_token>/', FeatureProduct.as_view(), name='feature_product'),

    #path("get-data/", GetMemberData.as_view()),
]
