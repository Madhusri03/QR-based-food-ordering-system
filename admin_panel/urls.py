from django.urls import path
from . import views

app_name = 'admin_panel'

urlpatterns = [
    # Dashboard / Analytics
    path('', views.admin_dashboard, name='dashboard'),
    
    # Category Management
    path('categories/', views.category_list, name='category_list'),
    path('categories/add/', views.category_add, name='category_add'),
    path('categories/edit/<int:category_id>/', views.category_edit, name='category_edit'),
    path('categories/delete/<int:category_id>/', views.category_delete, name='category_delete'),
    
    # Menu Management
    path('menu/', views.menu_list, name='menu_list'),
    path('menu/add/', views.menu_add, name='menu_add'),
    path('menu/edit/<int:food_id>/', views.menu_edit, name='menu_edit'),
    path('menu/delete/<int:food_id>/', views.menu_delete, name='menu_delete'),
    
    # Table Management
    path('tables/', views.table_list, name='table_list'),
    path('tables/add/', views.table_add, name='table_add'),
    path('tables/edit/<int:table_id>/', views.table_edit, name='table_edit'),
    path('tables/delete/<int:table_id>/', views.table_delete, name='table_delete'),
    path('tables/free/<int:table_id>/', views.table_free, name='table_free'),
    
    # Order Management
    path('orders/', views.order_list, name='order_list'),
    path('orders/<int:order_id>/', views.order_detail, name='order_detail'),
    path('orders/<int:order_id>/complete/', views.order_complete, name='order_complete'),
]
