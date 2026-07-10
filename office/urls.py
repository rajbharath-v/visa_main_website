from django.urls import path
from . import views

urlpatterns = [
    path('voucher/<int:pk>/pdf/', views.voucher_pdf, name='office_voucher_pdf'),
]
