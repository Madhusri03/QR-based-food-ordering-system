from django.urls import path
from . import views

app_name = 'kitchen'

urlpatterns = [
    path('', views.kitchen_dashboard, name='dashboard'),
    path('order/<int:order_id>/update-status/', views.update_order_status, name='update_status'),
]
