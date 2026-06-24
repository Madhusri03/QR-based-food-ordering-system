import os
import django

# Setup Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'restaurant_qr_ordering.settings')
django.setup()

from django.contrib.auth.models import User
from accounts.models import UserProfile
from customer.models import Table
from menu.models import Category, Food
from PIL import Image, ImageDraw

def create_users():
    print("Creating users...")
    # Admin / Manager
    admin_user, created = User.objects.get_or_create(username='admin')
    if created:
        admin_user.set_password('admin123')
        admin_user.is_superuser = True
        admin_user.is_staff = True
        admin_user.save()
        print("Superuser 'admin' with password 'admin123' created.")
    
    # Ensure profile role is ADMIN
    admin_profile = admin_user.profile
    admin_profile.role = 'ADMIN'
    admin_profile.save()

    # Kitchen Staff
    kitchen_user, created = User.objects.get_or_create(username='kitchen')
    if created:
        kitchen_user.set_password('kitchen123')
        kitchen_user.is_staff = True
        kitchen_user.save()
        print("Kitchen staff user 'kitchen' with password 'kitchen123' created.")
    
    # Ensure profile role is KITCHEN
    kitchen_profile = kitchen_user.profile
    kitchen_profile.role = 'KITCHEN'
    kitchen_profile.save()

def create_tables():
    print("Creating tables and generating QR codes...")
    for t_num in range(1, 21):
        table, created = Table.objects.get_or_create(table_number=str(t_num))
        if created:
            print(f"Table {t_num} created (QR generated automatically at {table.qr_code.name}).")
        else:
            # Re-save to regenerate QR codes if needed
            table.save()
            print(f"Table {t_num} updated.")

def create_dummy_image(name, color):
    """Create a dummy food image using Pillow and save it to media/foods/"""
    media_dir = os.path.join('media', 'foods')
    if not os.path.exists(media_dir):
        os.makedirs(media_dir)
        
    filepath = os.path.join(media_dir, f"{name}.png")
    if not os.path.exists(filepath):
        img = Image.new('RGB', (400, 300), color=color)
        draw = ImageDraw.Draw(img)
        # Draw some decorative text
        draw.text((20, 140), name.replace('_', ' ').title(), fill=(255, 255, 255))
        img.save(filepath)
        print(f"Dummy image created: {filepath}")
    return f"foods/{name}.png"

def create_menu():
    print("Creating menu categories and food dishes...")
    
    # Categories
    starters, _ = Category.objects.get_or_create(name="Starters")
    mains, _ = Category.objects.get_or_create(name="Main Course")
    desserts, _ = Category.objects.get_or_create(name="Desserts")
    beverages, _ = Category.objects.get_or_create(name="Beverages")
    
    # Food items with colors for their dummy images
    food_data = [
        # Starters
        {
            "category": starters,
            "name": "Garlic Bread",
            "desc": "Crispy toasted baguette with fresh garlic butter and herbs.",
            "price": 5.99,
            "img_name": "garlic_bread",
            "color": (210, 180, 140) # tan
        },
        {
            "category": starters,
            "name": "Bruschetta",
            "desc": "Grilled bread rubbed with garlic and topped with diced tomatoes, olive oil, and basil.",
            "price": 6.99,
            "img_name": "bruschetta",
            "color": (205, 92, 92) # indian red
        },
        {
            "category": starters,
            "name": "Chicken Wings",
            "desc": "Spicy buffalo wings served with blue cheese dip.",
            "price": 8.99,
            "img_name": "chicken_wings",
            "color": (165, 42, 42) # brown
        },
        
        # Mains
        {
            "category": mains,
            "name": "Margherita Pizza",
            "desc": "Classic pizza topped with fresh tomato sauce, mozzarella, and fresh basil leaves.",
            "price": 12.99,
            "img_name": "margherita_pizza",
            "color": (255, 99, 71) # tomato
        },
        {
            "category": mains,
            "name": "Grilled Salmon",
            "desc": "Atlantic salmon fillet served with garlic mashed potatoes and grilled asparagus.",
            "price": 18.99,
            "img_name": "grilled_salmon",
            "color": (250, 128, 114) # salmon
        },
        {
            "category": mains,
            "name": "Beef Burger",
            "desc": "Juicy beef patty with lettuce, tomato, cheese, and house sauce, served with fries.",
            "price": 11.99,
            "img_name": "beef_burger",
            "color": (139, 69, 19) # saddle brown
        },
        
        # Desserts
        {
            "category": desserts,
            "name": "Chocolate Lava Cake",
            "desc": "Rich chocolate cake with a warm liquid chocolate center, served with vanilla ice cream.",
            "price": 7.99,
            "img_name": "chocolate_lava_cake",
            "color": (47, 79, 79) # dark slate gray
        },
        {
            "category": desserts,
            "name": "New York Cheesecake",
            "desc": "Classic creamy baked cheesecake on a graham cracker crust with strawberry compote.",
            "price": 6.99,
            "img_name": "cheesecake",
            "color": (245, 222, 179) # wheat
        },
        
        # Beverages
        {
            "category": beverages,
            "name": "Iced Latte",
            "desc": "Chilled espresso with fresh cold milk and vanilla syrup.",
            "price": 4.50,
            "img_name": "iced_latte",
            "color": (188, 143, 143) # rosy brown
        },
        {
            "category": beverages,
            "name": "Mojito",
            "desc": "Refreshing blend of lime, fresh mint leaves, white sugar, and club soda.",
            "price": 5.50,
            "img_name": "mojito",
            "color": (46, 139, 87) # sea green
        }
    ]
    
    for food in food_data:
        img_path = create_dummy_image(food["img_name"], food["color"])
        dish, created = Food.objects.get_or_create(
            name=food["name"],
            defaults={
                "category": food["category"],
                "description": food["desc"],
                "price": food["price"],
                "image": img_path
            }
        )
        if created:
            print(f"Dish '{food['name']}' added to the menu.")
        else:
            print(f"Dish '{food['name']}' already exists.")

if __name__ == "__main__":
    create_users()
    create_tables()
    create_menu()
    print("Database population completed successfully!")
