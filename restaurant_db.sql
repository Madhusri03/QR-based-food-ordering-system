-- SQL script to create the database and set up sample data for the QR-Based Food Ordering System

-- 1. Create the Database
CREATE DATABASE IF NOT EXISTS restaurant_db CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
USE restaurant_db;

-- Note: In standard Django workflow, tables are created automatically using migrations:
--   python manage.py makemigrations
--   python manage.py migrate
--
-- Below is the SQL structure representing the schema created by Django ORM, 
-- followed by initial sample data insert statements.

-- 2. Structure of Table: customer_table
CREATE TABLE IF NOT EXISTS `customer_table` (
  `id` bigint(20) NOT NULL AUTO_INCREMENT,
  `table_number` varchar(50) NOT NULL,
  `qr_code` varchar(100) DEFAULT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `table_number` (`table_number`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- 3. Structure of Table: menu_category
CREATE TABLE IF NOT EXISTS `menu_category` (
  `id` bigint(20) NOT NULL AUTO_INCREMENT,
  `name` varchar(100) NOT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `name` (`name`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- 4. Structure of Table: menu_food
CREATE TABLE IF NOT EXISTS `menu_food` (
  `id` bigint(20) NOT NULL AUTO_INCREMENT,
  `category_id` bigint(20) NOT NULL,
  `name` varchar(150) NOT NULL,
  `description` longtext DEFAULT NULL,
  `image` varchar(100) NOT NULL,
  `price` decimal(8,2) NOT NULL,
  PRIMARY KEY (`id`),
  KEY `menu_food_category_id_fk` (`category_id`),
  CONSTRAINT `menu_food_category_id_fk` FOREIGN KEY (`category_id`) REFERENCES `menu_category` (`id`) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- 5. Structure of Table: orders_order
CREATE TABLE IF NOT EXISTS `orders_order` (
  `id` bigint(20) NOT NULL AUTO_INCREMENT,
  `table_id` bigint(20) NOT NULL,
  `total_amount` decimal(10,2) NOT NULL,
  `status` varchar(20) NOT NULL,
  `created_at` datetime(6) NOT NULL,
  PRIMARY KEY (`id`),
  KEY `orders_order_table_id_fk` (`table_id`),
  CONSTRAINT `orders_order_table_id_fk` FOREIGN KEY (`table_id`) REFERENCES `customer_table` (`id`) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- 6. Structure of Table: orders_orderitem
CREATE TABLE IF NOT EXISTS `orders_orderitem` (
  `id` bigint(20) NOT NULL AUTO_INCREMENT,
  `order_id` bigint(20) NOT NULL,
  `food_id` bigint(20) DEFAULT NULL,
  `quantity` int(10) unsigned NOT NULL,
  `price` decimal(8,2) NOT NULL,
  PRIMARY KEY (`id`),
  KEY `orders_orderitem_order_id_fk` (`order_id`),
  KEY `orders_orderitem_food_id_fk` (`food_id`),
  CONSTRAINT `orders_orderitem_food_id_fk` FOREIGN KEY (`food_id`) REFERENCES `menu_food` (`id`) ON DELETE SET NULL,
  CONSTRAINT `orders_orderitem_order_id_fk` FOREIGN KEY (`order_id`) REFERENCES `orders_order` (`id`) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- 7. Insert Sample Tables
INSERT INTO `customer_table` (`id`, `table_number`, `qr_code`) VALUES
(1, '1', 'qr_codes/table_1_qr.png'),
(2, '2', 'qr_codes/table_2_qr.png'),
(3, '3', 'qr_codes/table_3_qr.png'),
(4, '4', 'qr_codes/table_4_qr.png'),
(5, '5', 'qr_codes/table_5_qr.png')
ON DUPLICATE KEY UPDATE id=id;

-- 8. Insert Sample Categories
INSERT INTO `menu_category` (`id`, `name`) VALUES
(1, 'Starters'),
(2, 'Main Course'),
(3, 'Desserts'),
(4, 'Beverages')
ON DUPLICATE KEY UPDATE id=id;

-- 9. Insert Sample Food Items
INSERT INTO `menu_food` (`id`, `category_id`, `name`, `description`, `image`, `price`) VALUES
(1, 1, 'Garlic Bread', 'Crispy toasted baguette with fresh garlic butter and herbs.', 'foods/garlic_bread.jpg', 5.99),
(2, 1, 'Bruschetta', 'Grilled bread rubbed with garlic and topped with diced tomatoes, olive oil, and basil.', 'foods/bruschetta.jpg', 6.99),
(3, 1, 'Chicken Wings', 'Spicy buffalo wings served with blue cheese dip.', 'foods/chicken_wings.jpg', 8.99),
(4, 2, 'Margherita Pizza', 'Classic pizza topped with fresh tomato sauce, mozzarella, and fresh basil leaves.', 'foods/margherita_pizza.jpg', 12.99),
(5, 2, 'Grilled Salmon', 'Atlantic salmon fillet served with garlic mashed potatoes and grilled asparagus.', 'foods/grilled_salmon.jpg', 18.99),
(6, 2, 'Beef Burger', 'Juicy beef patty with lettuce, tomato, cheese, and house sauce, served with fries.', 'foods/beef_burger.jpg', 11.99),
(7, 3, 'Chocolate Lava Cake', 'Rich chocolate cake with a warm liquid chocolate center, served with vanilla ice cream.', 'foods/chocolate_lava_cake.jpg', 7.99),
(8, 3, 'New York Cheesecake', 'Classic creamy baked cheesecake on a graham cracker crust with strawberry compote.', 'foods/cheesecake.jpg', 6.99),
(9, 4, 'Iced Latte', 'Chilled espresso with fresh cold milk and vanilla syrup.', 'foods/iced_latte.jpg', 4.50),
(10, 4, 'Mojito', 'Refreshing blend of lime, fresh mint leaves, white sugar, and club soda.', 'foods/mojito.jpg', 5.50)
ON DUPLICATE KEY UPDATE id=id;
