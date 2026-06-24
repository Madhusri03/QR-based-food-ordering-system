from django.test import TestCase, Client
from django.urls import reverse
from customer.models import Table
from menu.models import Category, Food
from orders.models import Order, OrderItem
from django.core.files.uploadedfile import SimpleUploadedFile
import os
from decimal import Decimal

class TableModelTests(TestCase):
    def test_table_qr_code_auto_generation(self):
        """Test that a Table's QR code is automatically generated on save."""
        table = Table.objects.create(table_number="99")
        self.assertIsNotNone(table.qr_code)
        self.assertTrue(table.qr_code.name.endswith("table_99_qr.png"))
        
        # Verify the file is created in the media directory
        # (Clean up later)
        file_exists = os.path.exists(table.qr_code.path)
        self.assertTrue(file_exists)
        
        # Clean up files created during test
        if file_exists:
            os.remove(table.qr_code.path)

class CustomerFlowTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.table = Table.objects.create(table_number="5")
        self.category = Category.objects.create(name="Appetizers")
        
        # Create a dummy image for testing
        image_content = b'\x47\x49\x46\x38\x39\x61\x01\x00\x01\x00\x80\x00\x00\x00\x00\x00\xff\xff\xff\x21\xf9\x04\x01\x00\x00\x00\x00\x2c\x00\x00\x00\x00\x01\x00\x01\x00\x00\x02\x02\x44\x01\x00\x3b'
        uploaded_image = SimpleUploadedFile(
            name='test_food.gif',
            content=image_content,
            content_type='image/gif'
        )
        
        self.food = Food.objects.create(
            name="Spring Rolls",
            category=self.category,
            description="Crispy rolls with vegetables.",
            price=Decimal('4.99'),
            image=uploaded_image
        )

    def tearDown(self):
        # Clean up image files
        if self.food.image and os.path.exists(self.food.image.path):
            os.remove(self.food.image.path)
        if self.table.qr_code and os.path.exists(self.table.qr_code.path):
            os.remove(self.table.qr_code.path)

    def test_table_scan_view_sets_session(self):
        """Test scanning a table redirects and sets session variables."""
        response = self.client.get(reverse('customer:table_scan', args=[self.table.table_number]))
        self.assertRedirects(response, reverse('customer:menu'))
        
        session = self.client.session
        self.assertEqual(session.get('table_id'), self.table.id)
        self.assertEqual(session.get('table_number'), self.table.table_number)

    def test_cart_session_operations(self):
        """Test adding, modifying, and removing items in the session-based cart."""
        # 1. Add item
        response = self.client.get(reverse('customer:cart_add', args=[self.food.id]))
        self.assertRedirects(response, reverse('customer:menu'))
        
        session = self.client.session
        cart = session.get('cart')
        str_food_id = str(self.food.id)
        self.assertIn(str_food_id, cart)
        self.assertEqual(cart[str_food_id]['quantity'], 1)
        
        # 2. Update quantity (increase)
        response = self.client.post(reverse('customer:cart_update', args=[self.food.id]), {'action': 'increase'})
        self.assertRedirects(response, reverse('customer:cart'))
        session = self.client.session
        self.assertEqual(session.get('cart')[str_food_id]['quantity'], 2)
        
        # 3. Update quantity (decrease)
        response = self.client.post(reverse('customer:cart_update', args=[self.food.id]), {'action': 'decrease'})
        self.assertRedirects(response, reverse('customer:cart'))
        session = self.client.session
        self.assertEqual(session.get('cart')[str_food_id]['quantity'], 1)

        # 4. Remove item
        response = self.client.get(reverse('customer:cart_remove', args=[self.food.id]))
        self.assertRedirects(response, reverse('customer:cart'))
        session = self.client.session
        self.assertNotIn(str_food_id, session.get('cart'))

    def test_place_order(self):
        """Test placing an order creates database entries and clears cart."""
        # Setup cart in session
        session = self.client.session
        session['cart'] = {
            str(self.food.id): {
                'name': self.food.name,
                'price': str(self.food.price),
                'quantity': 2,
                'image_url': self.food.image.url
            }
        }
        session['table_id'] = self.table.id
        session['table_number'] = self.table.table_number
        session.save()
        
        # Place order
        response = self.client.post(reverse('customer:place_order'))
        
        # Order should be created in DB
        orders = Order.objects.all()
        self.assertEqual(orders.count(), 1)
        order = orders.first()
        self.assertEqual(order.table, self.table)
        self.assertEqual(order.total_amount, self.food.price * 2)
        self.assertEqual(order.status, 'Pending')
        
        # OrderItem should be created
        items = OrderItem.objects.filter(order=order)
        self.assertEqual(items.count(), 1)
        item = items.first()
        self.assertEqual(item.food, self.food)
        self.assertEqual(item.quantity, 2)
        self.assertEqual(item.price, self.food.price)
        
        # Cart session should be cleared
        session = self.client.session
        self.assertEqual(session.get('cart'), {})
                # Should redirect to order confirmation
        self.assertRedirects(response, reverse('customer:order_confirm', args=[order.id]))

    def test_table_occupancy_and_lock(self):
        """Test reserving table on selection, locking, and releasing order."""
        # 1. Select table via select-table API
        response = self.client.post(reverse('customer:select_table'), {'table_id': self.table.id})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), {'success': True, 'table_number': self.table.table_number})
        
        # Table should be reserved in DB
        self.table.refresh_from_db()
        self.assertTrue(self.table.is_occupied)
        self.assertIsNotNone(self.table.occupied_at)
        
        # 2. Place order should set order_placed to True
        session = self.client.session
        session['cart'] = {
            str(self.food.id): {
                'name': self.food.name,
                'price': str(self.food.price),
                'quantity': 1,
                'image_url': self.food.image.url
            }
        }
        session.save()
        
        response = self.client.post(reverse('customer:place_order'))
        session = self.client.session
        self.assertTrue(session.get('order_placed'))
        
        # 3. Trying to select a different table should be rejected because assignment is locked
        another_table = Table.objects.create(table_number="6")
        response = self.client.post(reverse('customer:select_table'), {'table_id': another_table.id})
        self.assertEqual(response.json()['success'], False)
        self.assertIn('locked', response.json()['error'])
        
        # Cleanup table 6 QR code
        if another_table.qr_code and os.path.exists(another_table.qr_code.path):
            os.remove(another_table.qr_code.path)
