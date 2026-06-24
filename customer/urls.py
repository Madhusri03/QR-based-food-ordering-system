from django.urls import path
from . import views

app_name = 'customer'

urlpatterns = [
    path('table/<str:table_number>/', views.table_scan_view, name='table_scan'),
    path('', views.menu_view, name='menu'),
    path('cart/', views.cart_view, name='cart'),
    path('cart/add/<int:food_id>/', views.cart_add_view, name='cart_add'),
    path('cart/update/<int:food_id>/', views.cart_update_view, name='cart_update'),
    path('cart/remove/<int:food_id>/', views.cart_remove_view, name='cart_remove'),
    path('order/place/', views.place_order_view, name='place_order'),
    path('order/confirm/<int:order_id>/', views.order_confirm_view, name='order_confirm'),
    path('order/track/<int:order_id>/', views.order_track_view, name='order_track'),
    # API endpoints for dynamic table selection
    path('api/tables/', views.get_tables_api, name='api_tables'),
    path('api/select-table/', views.select_table_view, name='select_table'),
]
