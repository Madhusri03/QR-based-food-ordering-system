from django.shortcuts import render, redirect, get_object_or_404
from django.http import JsonResponse
from django.contrib import messages
from django.utils import timezone
from menu.models import Category, Food
from customer.models import Table
from orders.models import Order, OrderItem
from django.db.models import Q

def table_scan_view(request, table_number):
    """Entry point when customer scans QR code. Automatically detects table number."""
    table = get_object_or_404(Table, table_number=table_number)
    
    # Check if table is occupied by someone else
    if table.is_occupied and request.session.get('table_id') != table.id:
        messages.error(request, f"Table {table_number} is currently occupied.")
        return redirect('customer:menu')
        
    # Reserve the table
    if not table.is_occupied:
        table.is_occupied = True
        table.occupied_at = timezone.now()
        table.save()
        
    request.session['table_id'] = table.id
    request.session['table_number'] = table.table_number
    request.session.modified = True
    messages.success(request, f"Welcome! Table {table_number} detected successfully. You can now place orders.")
    return redirect('customer:menu')

def menu_view(request):
    """View digital menu, category filters, and search items."""
    from django.core.cache import cache
    
    categories = cache.get('menu_categories')
    if categories is None:
        categories = list(Category.objects.all())
        cache.set('menu_categories', categories, 300) # 5 mins cache
        
    query = request.GET.get('q')
    category_id = request.GET.get('category')
    
    # Cache foods only when there is no query and no category filter
    if not query and not category_id:
        foods = cache.get('menu_foods')
        if foods is None:
            foods = list(Food.objects.all().select_related('category'))
            cache.set('menu_foods', foods, 300)
    else:
        foods = Food.objects.all().select_related('category')
        if query:
            foods = foods.filter(Q(name__icontains=query) | Q(description__icontains=query))
        if category_id:
            foods = foods.filter(category_id=category_id)
            
    table_number = request.session.get('table_number')
    table_id = request.session.get('table_id')
    
    # Check if table is actually occupied in the database
    if table_id:
        try:
            table_obj = Table.objects.get(id=table_id)
            if not table_obj.is_occupied:
                request.session['order_placed'] = False
                request.session.pop('table_id', None)
                request.session.pop('table_number', None)
                request.session.modified = True
                table_number = None
        except Table.DoesNotExist:
            request.session['order_placed'] = False
            request.session.pop('table_id', None)
            request.session.pop('table_number', None)
            request.session.modified = True
            table_number = None

    cart = request.session.get('cart', {})
    cart_count = sum(item['quantity'] for item in cart.values())
    
    # Check if the customer has already placed an order (table is locked)
    has_ordered = request.session.get('order_placed', False)
    
    context = {
        'categories': categories,
        'foods': foods,
        'table_number': table_number,
        'cart_count': cart_count,
        'selected_category': int(category_id) if category_id else None,
        'query': query,
        'has_ordered': has_ordered,
    }
    return render(request, 'customer/menu.html', context)

def cart_view(request):
    """View items currently in the cart and total cost."""
    table_id = request.session.get('table_id')
    table_number = request.session.get('table_number')
    
    # Check if table is actually occupied in the database
    if table_id:
        try:
            table_obj = Table.objects.get(id=table_id)
            if not table_obj.is_occupied:
                request.session['order_placed'] = False
                request.session.pop('table_id', None)
                request.session.pop('table_number', None)
                request.session.modified = True
                table_number = None
        except Table.DoesNotExist:
            request.session['order_placed'] = False
            request.session.pop('table_id', None)
            request.session.pop('table_number', None)
            request.session.modified = True
            table_number = None

    cart = request.session.get('cart', {})
    
    total = 0.00
    cart_items = []
    
    for food_id, item in cart.items():
        subtotal = float(item['price']) * int(item['quantity'])
        total += subtotal
        cart_items.append({
            'food_id': food_id,
            'name': item['name'],
            'price': item['price'],
            'quantity': item['quantity'],
            'image_url': item['image_url'],
            'subtotal': round(subtotal, 2)
        })
        
    # If table is not set in session, retrieve all tables for fallback manual selection
    all_tables = None
    if not table_number:
        all_tables = Table.objects.all()
        
    context = {
        'cart_items': cart_items,
        'total': round(total, 2),
        'table_number': table_number,
        'all_tables': all_tables,
    }
    return render(request, 'customer/cart.html', context)

def cart_add_view(request, food_id):
    """Add a dish to the session cart."""
    food = get_object_or_404(Food, id=food_id)
    cart = request.session.get('cart', {})
    
    str_food_id = str(food_id)
    if str_food_id in cart:
        cart[str_food_id]['quantity'] += 1
    else:
        cart[str_food_id] = {
            'name': food.name,
            'price': str(food.price),
            'quantity': 1,
            'image_url': food.image.url if food.image else '/static/images/default_food.png'
        }
        
    request.session['cart'] = cart
    request.session.modified = True
    messages.success(request, f"Added {food.name} to cart.")
    return redirect('customer:menu')

def cart_update_view(request, food_id):
    """Increase or decrease quantity of a dish in the cart."""
    cart = request.session.get('cart', {})
    str_food_id = str(food_id)
    
    if str_food_id in cart:
        action = request.POST.get('action')
        if action == 'increase':
            cart[str_food_id]['quantity'] += 1
        elif action == 'decrease':
            cart[str_food_id]['quantity'] -= 1
            if cart[str_food_id]['quantity'] <= 0:
                del cart[str_food_id]
                
        request.session['cart'] = cart
        request.session.modified = True
        
    return redirect('customer:cart')

def cart_remove_view(request, food_id):
    """Remove a dish completely from the cart."""
    cart = request.session.get('cart', {})
    str_food_id = str(food_id)
    
    if str_food_id in cart:
        del cart[str_food_id]
        request.session['cart'] = cart
        request.session.modified = True
        messages.info(request, "Item removed from cart.")
        
    return redirect('customer:cart')

def place_order_view(request):
    """Place an order from cart and clear cart session."""
    cart = request.session.get('cart', {})
    if not cart:
        messages.error(request, "Your cart is empty.")
        return redirect('customer:menu')
        
    # Get table from session or fallback from POST form
    table_id = request.session.get('table_id')
    if not table_id:
        table_id = request.POST.get('table_id')
        if table_id:
            table = get_object_or_404(Table, id=table_id)
            request.session['table_id'] = table.id
            request.session['table_number'] = table.table_number
        else:
            messages.error(request, "Please scan a table QR code or select a table first.")
            return redirect('customer:cart')
            
    table = get_object_or_404(Table, id=request.session['table_id'])
    
    # Calculate total and verify food existence
    total = 0.00
    order_items_to_create = []
    
    for food_id, item in cart.items():
        food = get_object_or_404(Food, id=food_id)
        subtotal = float(food.price) * int(item['quantity'])
        total += subtotal
        order_items_to_create.append((food, item['quantity'], food.price))
        
    # Create the Order
    order = Order.objects.create(
        table=table,
        total_amount=total,
        status='Pending'
    )
    
    # Create OrderItems
    for food, qty, price in order_items_to_create:
        OrderItem.objects.create(
            order=order,
            food=food,
            quantity=qty,
            price=price
        )
    
    # Mark table as occupied
    table.is_occupied = True
    table.occupied_at = timezone.now()
    table.save()
    
    # Lock the table for this session (prevent table changes after first order)
    request.session['order_placed'] = True
        
    # Clear the cart session
    request.session['cart'] = {}
    request.session.modified = True
    
    messages.success(request, "Order placed successfully!")
    return redirect('customer:order_confirm', order_id=order.id)

def order_confirm_view(request, order_id):
    """View order confirmation after placing order."""
    order = get_object_or_404(Order, id=order_id)
    return render(request, 'customer/order_confirm.html', {'order': order})

def order_track_view(request, order_id):
    """Track current order status (Pending, Preparing, Ready, Served). Supports AJAX polling."""
    order = get_object_or_404(Order, id=order_id)
    
    # Support AJAX polling for live status tracking
    if request.headers.get('x-requested-with') == 'XMLHttpRequest':
        return JsonResponse({
            'status': order.status,
            'status_display': order.get_status_display()
        })
        
    return render(request, 'customer/order_track.html', {'order': order})

# ---- API Views for Dynamic Table Selection ----

def get_tables_api(request):
    """Return JSON list of all tables with their availability status."""
    tables = Table.objects.all().order_by('table_number')
    data = []
    for t in tables:
        data.append({
            'id': t.id,
            'table_number': t.table_number,
            'is_occupied': t.is_occupied,
        })
    return JsonResponse({'tables': data})

def select_table_view(request):
    """Handle table selection via POST. Sets the table in session."""
    if request.method == 'POST':
        if request.session.get('order_placed', False):
            return JsonResponse({'success': False, 'error': 'You have already placed an order. Table assignment is locked.'})
            
        table_id = request.POST.get('table_id')
        if table_id:
            table = get_object_or_404(Table, id=table_id)
            if table.is_occupied:
                return JsonResponse({'success': False, 'error': 'This table is currently occupied.'})
            
            # Release previously selected table if any (only if not yet ordered)
            prev_table_id = request.session.get('table_id')
            if prev_table_id and not request.session.get('order_placed', False):
                try:
                    prev_table = Table.objects.get(id=prev_table_id)
                    # Only release if no active orders exist for this table from other sessions
                    active_orders = Order.objects.filter(
                        table=prev_table, 
                        status__in=['Pending', 'Preparing', 'Ready']
                    ).exists()
                    if not active_orders:
                        prev_table.is_occupied = False
                        prev_table.occupied_at = None
                        prev_table.save()
                except Table.DoesNotExist:
                    pass
            
            # Reserve table immediately when customer selects it
            table.is_occupied = True
            table.occupied_at = timezone.now()
            table.save()
            
            request.session['table_id'] = table.id
            request.session['table_number'] = table.table_number
            request.session.modified = True
            
            return JsonResponse({'success': True, 'table_number': table.table_number})
    
    return JsonResponse({'success': False, 'error': 'Invalid request.'})
