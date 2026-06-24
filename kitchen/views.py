from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied
from orders.models import Order
from django.contrib import messages

def kitchen_role_required(view_func):
    """Decorator to ensure only kitchen staff or admin can access kitchen views."""
    def _wrapped_view_func(request, *args, **kwargs):
        if not request.user.is_authenticated:
            return redirect('accounts:login')
        if not hasattr(request.user, 'profile') or request.user.profile.role not in ['KITCHEN', 'ADMIN']:
            from django.contrib import messages as msg
            msg.error(request, "You must be logged in as Kitchen staff to access this page.")
            return redirect('accounts:login')
        return view_func(request, *args, **kwargs)
    return _wrapped_view_func

@kitchen_role_required
def kitchen_dashboard(request):
    """Kitchen Panel: view incoming active orders and completed orders."""
    from django.core.cache import cache
    
    # Cache active orders to handle polling requests efficiently
    active_orders = cache.get('kitchen_active_orders')
    if active_orders is None:
        active_orders = list(Order.objects.filter(status__in=['Pending', 'Preparing', 'Ready']) \
                                          .select_related('table') \
                                          .prefetch_related('items__food') \
                                          .order_by('created_at'))
        cache.set('kitchen_active_orders', active_orders, 3) # 3 seconds cache
        
    # Cache recently completed orders (limit 15)
    completed_orders = cache.get('kitchen_completed_orders')
    if completed_orders is None:
        completed_orders = list(Order.objects.filter(status='Served') \
                                             .select_related('table') \
                                             .prefetch_related('items__food') \
                                             .order_by('-created_at')[:15])
        cache.set('kitchen_completed_orders', completed_orders, 3) # 3 seconds cache
    
    context = {
        'active_orders': active_orders,
        'completed_orders': completed_orders,
    }
    return render(request, 'kitchen/dashboard.html', context)



@kitchen_role_required
def update_order_status(request, order_id):
    """Change the status of an order (Pending -> Preparing -> Ready -> Served)."""
    order = get_object_or_404(Order, id=order_id)
    
    if request.method == 'POST':
        new_status = request.POST.get('status')
        if new_status in dict(Order.STATUS_CHOICES):
            old_status = order.status
            order.status = new_status
            order.save()
            messages.success(request, f"Order #{order.id} status updated from {old_status} to {new_status}.")
            
            # Release table if status updated to Served and no active orders remain
            if new_status == 'Served':
                table = order.table
                active_orders = Order.objects.filter(
                    table=table,
                    status__in=['Pending', 'Preparing', 'Ready']
                ).exclude(id=order.id).exists()
                
                if not active_orders:
                    table.is_occupied = False
                    table.occupied_at = None
                    table.save()
        else:
            messages.error(request, "Invalid status transition.")
            
    return redirect('kitchen:dashboard')
