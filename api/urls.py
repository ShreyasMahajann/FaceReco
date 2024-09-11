# api/urls.py

from django.urls import path
from .views import VerificationView,index,create_new_encoding

urlpatterns = [
    path('verify/', VerificationView.as_view(), name='verify'),
    path('',index,name='index'),
    path('new1038aphxnn/',create_new_encoding,name='create_new_encoding'),
]
