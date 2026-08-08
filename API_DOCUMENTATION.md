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

### 2. Verify Email (4-Digit OTP)
- **Method**: `POST`
- **URL**: `/api/v1/auth/verify-email`
- **Request Body**:
```json
{
  "email": "ali@example.com",
  "code": "4281"
}
```

### 3. Resend Verification Code (60s Rate Limit)
- **Method**: `POST`
- **URL**: `/api/v1/auth/resend-verification`
- **Request Body**:
```json
{
  "email": "ali@example.com"
}
```

### 4. Login User
- **Method**: `POST`
- **URL**: `/api/v1/auth/login`
- **Request Body**:
```json
{
  "email": "ali@example.com",
  "password": "password123"
}
```

### 5. Forgot Password Code Request
- **Method**: `POST`
- **URL**: `/api/v1/auth/forgot-password`
- **Request Body**:
```json
{
  "email": "ali@example.com"
}
```

### 6. Reset Password with Code
- **Method**: `POST`
- **URL**: `/api/v1/auth/reset-password`
- **Request Body**:
```json
{
  "email": "ali@example.com",
  "code": "4281",
  "new_password": "newpassword123"
}
```

### 7. Google OAuth Sign-In
- **Method**: `POST`
- **URL**: `/api/v1/auth/google`
- **Request Body**:
```json
{
  "credential": "<google_id_token>"
}
```

---

## Admin Endpoints (RBAC Enforced)

### 1. Dashboard Analytics & KPIs
- **Method**: `GET`
- **URL**: `/api/v1/admin/analytics/dashboard`

### 2. List Users (Paginated & Filtered)
- **Method**: `GET`
- **URL**: `/api/v1/admin/users?page=1&limit=10&search=ali&role=customer`

### 3. Update User Account Status
- **Method**: `PATCH`
- **URL**: `/api/v1/admin/users/{user_id}/status`
- **Request Body**: `{ "is_active": false }`

### 4. Update User Role (Super Admin Only)
- **Method**: `PATCH`
- **URL**: `/api/v1/admin/users/{user_id}/role`
- **Request Body**: `{ "role": "admin" }`

### 5. List Products (Admin Table)
- **Method**: `GET`
- **URL**: `/api/v1/admin/products?page=1&limit=10&status=published`

### 6. Create Product (Admin)
- **Method**: `POST`
- **URL**: `/api/v1/admin/products`

### 7. Update Product
- **Method**: `PUT`
- **URL**: `/api/v1/admin/products/{product_id}`

### 8. Archive Product (Soft Delete)
- **Method**: `DELETE`
- **URL**: `/api/v1/admin/products/{product_id}`

### 9. Delete Product (Permanent)
- **Method**: `DELETE`
- **URL**: `/api/v1/admin/products/{product_id}/permanent`

### 10. Duplicate Product
- **Method**: `POST`
- **URL**: `/api/v1/admin/products/{product_id}/duplicate`

### 10. List Orders (Admin)
- **Method**: `GET`
- **URL**: `/api/v1/admin/orders?page=1&limit=10`

### 11. Update Order Status
- **Method**: `PATCH`
- **URL**: `/api/v1/admin/orders/{order_id}/status`
- **Request Body**: `{ "status": "shipped", "paymentStatus": "paid" }`

### 12. Manage Admin Accounts (Super Admin Only)
- **Method**: `GET` / `POST` / `DELETE`
- **URL**: `/api/v1/admin/admins`

### 13. Audit Trail Logs (Super Admin Only)
- **Method**: `GET`
- **URL**: `/api/v1/admin/audit-logs?page=1&limit=20`