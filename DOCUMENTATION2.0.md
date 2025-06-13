# 🚀 Bot Command Reference

---

## 👤 User Commands

| Command | Usage | Description |
|---------|-------|-------------|
| **/start** | `/start` | Start the bot and show the main menu. |
| **/categories** | `/categories` | List all product categories. |
| **/search** | `/search <keyword>` | Search for products by name or description.<br>_Example:_ `/search Spliff` |
| **/profile** | `/profile` | Show your profile: join date, order count, and balance. |
| **/balance** | `/balance` | Show your current coin balance. |
| **/deposit_ltc** | `/deposit_ltc` | Get a Litecoin deposit address (demo/testing). |
| **/myorders** | `/myorders` | Show your order history. |

**Inline Buttons:**
- 🛒 **Order**: Start the order process for a product.
- ℹ️ **Details**: Show detailed info for a product.
- 🔙 **Back to Menu**: Return to the main menu.
- 🔙 **Back to Categories**: Return to category selection.
- 🔙 **Back to Filters**: Return to order filter selection.

---

## 🛠️ Admin Commands

| Command | Usage | Description |
|---------|-------|-------------|
| **/addproduct** | `/addproduct <name> <price> <stock> <category>` | Add a new product.<br>_Example:_ `/addproduct Spliff 25 50 Spliff` |
| **/removeproduct** | `/removeproduct <product_id>` | Remove a product by its ID. |
| **/editproduct** | `/editproduct <product_id> <field> <new_value>` | Edit a product field (`name`, `price`, `stock`, `description`, `category`, `image`).<br>_Example:_ `/editproduct <id> price 30` |
| **/productlist** | `/productlist` | List all products with their IDs, names, prices, stock, and categories. |
| **/addproductphoto** | `/addproductphoto <product_name>` | Set the main presentation photo for a product.<br>_Then send a photo._ |
| **/addproductphoto_bulk** | `/addproductphoto_bulk <product_name>` | Bulk upload presentation photos for a product.<br>_Send multiple photos, then `/done`._ |
| **/addlocationphoto** | `/addlocationphoto <product_name>` | Bulk upload location (delivery) photos for a product.<br>_Send multiple photos, then `/done`._ |
| **/done** | `/done` | Finish a bulk photo upload session. |
| **/showlocationphotos** | `/showlocationphotos <product_name>` | Show all available (not yet delivered) location photos for a product. |
| **/allorders** | `/allorders` | Show all orders for all users, grouped by status. |
| **/exportorders** | `/exportorders` | Export all orders as a CSV file. |
| **/setorderstatus** | `/setorderstatus <order_id> <status>` | Change the status of an order (`completed`, `cancelled`, etc.).<br>_Example:_ `/setorderstatus <id> completed` |
| **/deliveries** | `/deliveries` | Show completed deliveries. |
| **/exportdeliveries** | `/exportdeliveries` | Export all deliveries as a CSV file. |
| **/removedelivery** | `/removedelivery <stock_id>` | Remove a delivery log by Stock ID. |
| **/addcoins** | `/addcoins <user_id> <amount>` | Add coins to a user's balance.<br>_Example:_ `/addcoins 5501799605 100` |
| **/setcoins** | `/setcoins <user_id> <amount>` | Set a user's balance.<br>_Example:_ `/setcoins 5501799605 500` |
| **/topusers** | `/topusers` | Show the top users by coin balance. |
| **/dashboard** | `/dashboard` | Show sales stats, top products, and low-stock alerts. |
| **/profits** | `/profits` | Show recent profits. |
| **/exportprofits** | `/exportprofits` | Export profits as a CSV file. |

---

## 📦 Product Example: Spliff

- **Add Spliff product:**  
  ```/addproduct Spliff 25 50 Spliff```
- **Add a presentation photo:**  
  ```/addproductphoto Spliff``` _(then send a photo)_
- **Bulk add presentation photos:**  
  ```/addproductphoto_bulk Spliff``` _(send multiple photos, then `/done`)_
- **Bulk add location photos:**  
  ```/addlocationphoto Spliff``` _(send multiple photos, then `/done`)_
- **Show available location photos:**  
  ```/showlocationphotos Spliff```

---

## 🖼️ Photo & Delivery Management

- **Location Photos:**  
  Bulk upload with `/addlocationphoto <product_name>`. Each order receives a unique, unused location photo if available. Delivered photos are archived.

- **Presentation Photos:**  
  Bulk upload with `/addproductphoto_bulk <product_name>`. The last photo sent is used as the main image.

- **Delivered Photos Archive:**  
  Every delivered location photo is saved in the `delivered_photos` table and downloaded to the `delivered_photos` folder with the pattern:  
  ```
  <product_name>_<order_id>_<user_id>_<quantity>_<date-time>.png
  ```

- **Show Available Location Photos:**  
  `/showlocationphotos <product_name>` (admin only): Shows all available (not yet delivered) location photos for the product.

---

## 🗄️ Database Structure (Key Tables)

- **products:** `id`, `name`, `price`, `stock`, `description`, `category`, `image`
- **location_photos:** `id`, `product_id`, `file_id`, `caption`, `is_delivered`, `order_id`
- **delivered_photos:** `id`, `file_id`, `product_id`, `order_id`, `delivered_at`
- **orders:** `id`, `user_id`, `product_id`, `product_name`, `quantity`, `status`, `created_at`, `location_photo_id`
- **users:** `id`, `join_date`, `balance`

---

## 📝 Notes

- All commands are case-insensitive for product names.
- Only admins (IDs in `ADMIN_IDS`) can use admin commands.
- All data is persistent in SQLite.
- The bot uses async handlers and the latest python-telegram-bot API.
- Inline buttons are used for navigation and order flow.

---

> _For any questions or to add more features, contact your bot developer!_
