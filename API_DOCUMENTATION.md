# Artisa API Documentation (OpenAPI v1.0.0)

Welcome to the **Artisa API** documentation. All endpoints follow RESTful design principles and return standard JSON response envelopes.

---

## Response Envelopes

### Success Response (HTTP 200 / 201)
```json
{
  "success": true,
  "message": "عملیات با موفقیت انجام شد",
  "data": { ... }
}
```

### Error Response (HTTP 400 / 401 / 403 / 404 / 422 / 500)
```json
{
  "success": false,
  "message": "توضیحات خطا",
  "errors": [ "اطلاعات بیشتر" ]
}
```

---

## Authentication Endpoints

### 1. Register User
- **Method**: `POST`
- **URL**: `/api/v1/auth/register`
- **Request Body**:
```json
{
  "name": "علی رضایی",
  "email": "ali@example.com",
  "password": "password123",
  "phone": "09121234567"
}
```

### 2. Login User
- **Method**: `POST`
- **URL**: `/api/v1/auth/login`
- **Request Body**:
```json
{
  "email": "ali@example.com",
  "password": "password123"
}
```

### 3. Refresh Access Token
- **Method**: `POST`
- **URL**: `/api/v1/auth/refresh`

### 4. Logout User
- **Method**: `POST`
- **URL**: `/api/v1/auth/logout`

---

## User Profile Endpoints

### 1. Get Profile
- **Method**: `GET`
- **URL**: `/api/v1/users/me`
- **Header**: `Authorization: Bearer <access_token>`

### 2. Update Profile
- **Method**: `PUT`
- **URL**: `/api/v1/users/profile`
- **Request Body**:
```json
{
  "name": "علی رضایی جدید",
  "phone": "09129999999"
}
```

### 3. Change Password
- **Method**: `PUT`
- **URL**: `/api/v1/users/password`
- **Request Body**:
```json
{
  "currentPassword": "password123",
  "newPassword": "newpassword123"
}
```

---

## Products Endpoints

### 1. List Products
- **Method**: `GET`
- **URL**: `/api/v1/products`
- **Query Parameters**:
  - `search`: General search string
  - `category`: Category name (e.g. `تابلو نقاشی`, `هنر دیواری`, `مجسمه و دکوری`, `قاب و فریم`, `هنر مدرن`)
  - `isSpecial`: `true` / `false` (Amazing offers)
  - `isBestSeller`: `true` / `false` (Best sellers)
  - `minPrice`: Minimum price filter
  - `maxPrice`: Maximum price filter
  - `sort_by`: `price` | `rating` | `created_at`
  - `sort_order`: `asc` | `desc`
  - `page`: Page number (default `1`)
  - `limit`: Items per page (default `20`)

### 2. Get Product Details
- **Method**: `GET`
- **URL**: `/api/v1/products/{id}`

### 3. Create Product (Admin)
- **Method**: `POST`
- **URL**: `/api/v1/products`

---

## Comments Endpoints

### 1. List Product Comments
- **Method**: `GET`
- **URL**: `/api/v1/products/{product_id}/comments`

### 2. Post Comment
- **Method**: `POST`
- **URL**: `/api/v1/products/{product_id}/comments`
- **Request Body**:
```json
{
  "text": "بسیار زیبا و عالی بود",
  "rating": 5
}
```

---

## Addresses Endpoints

### 1. List User Addresses
- **Method**: `GET`
- **URL**: `/api/v1/addresses`

### 2. Add Address
- **Method**: `POST`
- **URL**: `/api/v1/addresses`

### 3. Set Default Address
- **Method**: `PUT`
- **URL**: `/api/v1/addresses/{id}/default`

---

## Orders & Tracking Endpoints

### 1. Create Order (Checkout)
- **Method**: `POST`
- **URL**: `/api/v1/orders`
- **Request Body**:
```json
{
  "fullName": "علیرضا محمدی",
  "phone": "09121234567",
  "postalCode": "1234567890",
  "address": "تهران، خیابان ولیعصر...",
  "paymentMethod": "online",
  "items": [
    {
      "id": "p1",
      "name": "تابلو نقاشی «افق طلایی»",
      "price": 3200000,
      "quantity": 1,
      "image": "https://..."
    }
  ]
}
```

### 2. Track Order Timeline
- **Method**: `GET`
- **URL**: `/api/v1/orders/track/{order_id}`
- **Example Response**:
```json
{
  "success": true,
  "message": "وضعیت سفارش دریافت شد",
  "data": {
    "orderId": "ORD-10042",
    "status": "delivered",
    "steps": [
      { "title": "statusReceived", "desc": "سفارش در سیستم ثبت شده است", "completed": true },
      { "title": "statusProcessing", "desc": "در حال آماده‌سازی", "completed": true },
      { "title": "statusShipped", "desc": "تحویل به پست پیشتاز", "completed": true },
      { "title": "statusDelivered", "desc": "تحویل داده شده است", "completed": true }
    ]
  }
}
```

---

## Image Upload Endpoint

### Upload Image
- **Method**: `POST`
- **URL**: `/api/v1/upload`
- **Content-Type**: `multipart/form-data`
- **Form Field**: `file` (image file)