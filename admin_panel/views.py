from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied
from django.db.models import Sum, Count
from django.contrib import messages
from menu.models import Category, Food
from customer.models import Table
from orders.models import Order, OrderItem

def admin_role_required(view_func):
    """Decorator to ensure only admin users can access admin panel views."""
    def _wrapped_view_func(request, *args, **kwargs):
        if not request.user.is_authenticated:
            return redirect('accounts:login')
        if not hasattr(request.user, 'profile') or request.user.profile.role != 'ADMIN':
            # Not an admin — redirect to login with a clear message instead of 403
            from django.contrib import messages as msg
            msg.error(request, "You must be logged in as an Admin to access this page.")
            return redirect('accounts:login')
        return view_func(request, *args, **kwargs)
    return _wrapped_view_func

# ----------------- Dashboard & Analytics -----------------

@admin_role_required
def admin_dashboard(request):
    """Admin Dashboard: displays key performance metrics and analytics."""
    from django.utils import timezone
    from django.core.cache import cache
    now = timezone.now()
    
    # 1. Best selling dishes - cache for 5 minutes (300 seconds)
    best_sellers = cache.get('admin_best_sellers')
    if best_sellers is None:
        best_sellers = list(OrderItem.objects.values('food__name', 'food__price', 'food__image') \
                                         .annotate(total_qty=Sum('quantity')) \
                                         .order_by('-total_qty')[:5])
        cache.set('admin_best_sellers', best_sellers, 300)
        
    # 2. General dashboard stats - cache for 3 seconds (reduces polling database load)
    cache_key = f"admin_stats_{now.strftime('%Y%m%d')}"
    stats = cache.get(cache_key)
    if stats is None:
        total_orders = Order.objects.count()
        orders_today = Order.objects.filter(created_at__date=now.date()).count()
        
        # Calculate total revenue
        total_revenue_aggr = Order.objects.filter(status='Served').aggregate(total=Sum('total_amount'))
        total_revenue = total_revenue_aggr['total'] or 0.00
        
        # Revenue today
        revenue_today_aggr = Order.objects.filter(created_at__date=now.date(), status='Served').aggregate(total=Sum('total_amount'))
        revenue_today = revenue_today_aggr['total'] or 0.00
        
        # Revenue this month
        revenue_month_aggr = Order.objects.filter(created_at__year=now.year, created_at__month=now.month, status='Served').aggregate(total=Sum('total_amount'))
        revenue_month = revenue_month_aggr['total'] or 0.00
        
        # Recent orders summary
        recent_orders = list(Order.objects.all().select_related('table').order_by('-created_at')[:5])
        
        # Summary of order counts by status
        status_summary = Order.objects.values('status').annotate(count=Count('id'))
        status_counts = {item['status']: item['count'] for item in status_summary}
        
        # Table occupancy stats
        total_tables = Table.objects.count()
        occupied_tables = Table.objects.filter(is_occupied=True).count()
        available_tables = Table.objects.filter(is_occupied=False).count()
        
        stats = {
            'total_orders': total_orders,
            'orders_today': orders_today,
            'total_revenue': round(total_revenue, 2),
            'revenue_today': round(revenue_today, 2),
            'revenue_month': round(revenue_month, 2),
            'recent_orders': recent_orders,
            'status_counts': status_counts,
            'total_tables': total_tables,
            'occupied_tables': occupied_tables,
            'available_tables': available_tables,
        }
        cache.set(cache_key, stats, 3) # Cache for 3 seconds
        
    context = {
        'total_orders': stats['total_orders'],
        'orders_today': stats['orders_today'],
        'total_revenue': stats['total_revenue'],
        'revenue_today': stats['revenue_today'],
        'revenue_month': stats['revenue_month'],
        'best_sellers': best_sellers,
        'recent_orders': stats['recent_orders'],
        'status_counts': stats['status_counts'],
        'total_tables': stats['total_tables'],
        'occupied_tables': stats['occupied_tables'],
        'available_tables': stats['available_tables'],
    }
    return render(request, 'admin_panel/dashboard.html', context)

# ----------------- Category Management -----------------

@admin_role_required
def category_list(request):
    """View list of all food categories and add new categories."""
    categories = Category.objects.all().annotate(food_count=Count('dishes'))
    return render(request, 'admin_panel/category_list.html', {'categories': categories})

@admin_role_required
def category_add(request):
    """Add a new food category."""
    if request.method == 'POST':
        name = request.POST.get('name')
        if name:
            if Category.objects.filter(name__iexact=name).exists():
                messages.error(request, f"Category '{name}' already exists.")
            else:
                Category.objects.create(name=name)
                messages.success(request, f"Category '{name}' created successfully.")
        else:
            messages.error(request, "Category name cannot be empty.")
    return redirect('admin_panel:category_list')

@admin_role_required
def category_edit(request, category_id):
    """Edit category name."""
    category = get_object_or_404(Category, id=category_id)
    if request.method == 'POST':
        name = request.POST.get('name')
        if name:
            if Category.objects.filter(name__iexact=name).exclude(id=category_id).exists():
                messages.error(request, f"Category '{name}' already exists.")
            else:
                category.name = name
                category.save()
                messages.success(request, f"Category updated to '{name}' successfully.")
                return redirect('admin_panel:category_list')
        else:
            messages.error(request, "Category name cannot be empty.")
            
    return render(request, 'admin_panel/category_edit.html', {'category': category})

@admin_role_required
def category_delete(request, category_id):
    """Delete food category."""
    category = get_object_or_404(Category, id=category_id)
    if request.method == 'POST':
        name = category.name
        category.delete()
        messages.warning(request, f"Category '{name}' has been deleted.")
    return redirect('admin_panel:category_list')

# ----------------- Menu Management -----------------

@admin_role_required
def menu_list(request):
    """View all food items/dishes in the menu."""
    foods = Food.objects.all().select_related('category')
    categories = Category.objects.all()
    return render(request, 'admin_panel/menu_list.html', {'foods': foods, 'categories': categories})

@admin_role_required
def menu_add(request):
    """Add a new food item with image upload."""
    if request.method == 'POST':
        name = request.POST.get('name')
        category_id = request.POST.get('category')
        description = request.POST.get('description')
        price = request.POST.get('price')
        image = request.FILES.get('image')
        
        if name and category_id and price and image:
            category = get_object_or_404(Category, id=category_id)
            Food.objects.create(
                name=name,
                category=category,
                description=description,
                price=price,
                image=image
            )
            messages.success(request, f"Dish '{name}' added to menu successfully.")
            return redirect('admin_panel:menu_list')
        else:
            messages.error(request, "Please fill in all required fields and upload an image.")
            
    categories = Category.objects.all()
    return render(request, 'admin_panel/menu_add.html', {'categories': categories})

@admin_role_required
def menu_edit(request, food_id):
    """Edit menu item details and optionally change image."""
    food = get_object_or_404(Food, id=food_id)
    if request.method == 'POST':
        name = request.POST.get('name')
        category_id = request.POST.get('category')
        description = request.POST.get('description')
        price = request.POST.get('price')
        image = request.FILES.get('image')
        
        if name and category_id and price:
            category = get_object_or_404(Category, id=category_id)
            food.name = name
            food.category = category
            food.description = description
            food.price = price
            if image:
                food.image = image
            food.save()
            messages.success(request, f"Dish '{name}' updated successfully.")
            return redirect('admin_panel:menu_list')
        else:
            messages.error(request, "Please fill in all required fields.")
            
    categories = Category.objects.all()
    return render(request, 'admin_panel/menu_edit.html', {'food': food, 'categories': categories})

@admin_role_required
def menu_delete(request, food_id):
    """Delete menu item."""
    food = get_object_or_404(Food, id=food_id)
    if request.method == 'POST':
        name = food.name
        food.delete()
        messages.warning(request, f"Dish '{name}' deleted from menu.")
    return redirect('admin_panel:menu_list')

# ----------------- Table Management -----------------

@admin_role_required
def table_list(request):
    """View list of all tables and add new tables (triggers QR generation)."""
    tables = Table.objects.all().order_by('table_number')
    return render(request, 'admin_panel/table_list.html', {'tables': tables})

@admin_role_required
def table_add(request):
    """Add a new table."""
    if request.method == 'POST':
        table_number = request.POST.get('table_number')
        if table_number:
            if Table.objects.filter(table_number__iexact=table_number).exists():
                messages.error(request, f"Table '{table_number}' already exists.")
            else:
                Table.objects.create(table_number=table_number)
                messages.success(request, f"Table '{table_number}' added (QR generated).")
        else:
            messages.error(request, "Table number cannot be empty.")
    return redirect('admin_panel:table_list')

@admin_role_required
def table_edit(request, table_id):
    """Edit table details (triggers QR regeneration)."""
    table = get_object_or_404(Table, id=table_id)
    if request.method == 'POST':
        table_number = request.POST.get('table_number')
        if table_number:
            if Table.objects.filter(table_number__iexact=table_number).exclude(id=table_id).exists():
                messages.error(request, f"Table '{table_number}' already exists.")
            else:
                table.table_number = table_number
                table.save() # Triggers QR regeneration
                messages.success(request, f"Table updated to '{table_number}' (QR regenerated).")
                return redirect('admin_panel:table_list')
        else:
            messages.error(request, "Table number cannot be empty.")
            
    return render(request, 'admin_panel/table_edit.html', {'table': table})

@admin_role_required
def table_delete(request, table_id):
    """Delete a table."""
    table = get_object_or_404(Table, id=table_id)
    if request.method == 'POST':
        table_number = table.table_number
        table.delete()
        messages.warning(request, f"Table '{table_number}' deleted.")
    return redirect('admin_panel:table_list')

@admin_role_required
def table_free(request, table_id):
    """Manually free/release an occupied table."""
    table = get_object_or_404(Table, id=table_id)
    if request.method == 'POST':
        table.is_occupied = False
        table.occupied_at = None
        table.save()
        messages.success(request, f"Table '{table.table_number}' has been freed and is now available.")
    return redirect('admin_panel:table_list')

# ----------------- Order Management -----------------

@admin_role_required
def order_list(request):
    """View all orders, search by table number, and filter by status."""
    from django.core.paginator import Paginator
    
    orders = Order.objects.all().select_related('table')
    
    # Handle search by table number
    search_query = request.GET.get('q')
    if search_query:
        orders = orders.filter(table__table_number__icontains=search_query)
        
    # Handle filter by status
    status_filter = request.GET.get('status')
    if status_filter:
        orders = orders.filter(status=status_filter)
        
    # Paginate orders (15 per page)
    paginator = Paginator(orders, 15)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
        
    context = {
        'orders': page_obj,
        'search_query': search_query,
        'status_filter': status_filter,
        'status_choices': Order.STATUS_CHOICES,
    }
    return render(request, 'admin_panel/order_list.html', context)

@admin_role_required
def order_detail(request, order_id):
    """View detailed summary of an individual order."""
    order = get_object_or_404(Order.objects.select_related('table'), id=order_id)
    order_items = order.items.all().select_related('food')
    return render(request, 'admin_panel/order_detail.html', {'order': order, 'order_items': order_items})

@admin_role_required
def order_complete(request, order_id):
    """Complete/close an order and release the associated table."""
    order = get_object_or_404(Order, id=order_id)
    if request.method == 'POST':
        order.status = 'Served'
        order.save()
        
        # Release the table
        table = order.table
        # Only release if no other active orders exist for this table
        active_orders = Order.objects.filter(
            table=table,
            status__in=['Pending', 'Preparing', 'Ready']
        ).exclude(id=order.id).exists()
        
        if not active_orders:
            table.is_occupied = False
            table.occupied_at = None
            table.save()
            messages.success(request, f"Order #{order.id} completed. Table {table.table_number} is now available.")
        else:
            messages.success(request, f"Order #{order.id} completed. Table {table.table_number} still has other active orders.")
    
    return redirect('admin_panel:order_list')
