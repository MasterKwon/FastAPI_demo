# Database Schema Documentation

## Overview
This document describes the database schema for the FastAPI demo application. The schema includes tables for users, items, item images, and item reviews.

## Tables

### Users Table
Stores user account information.

| Column | Type | Description |
|--------|------|-------------|
| id | SERIAL | Primary key, auto-incrementing |
| username | VARCHAR(50) | Unique username |
| email | VARCHAR(100) | Unique email address |
| hashed_password | VARCHAR(255) | Hashed password string |
| is_active | BOOLEAN | Account status (default: TRUE) |
| created_at | TIMESTAMPTZ | Account creation timestamp |

**Indexes:**
- Primary Key: `id`
- Unique: `username`, `email`
- Index: `email`, `username`, `created_at`

### Items Table
Stores product information.

| Column | Type | Description |
|--------|------|-------------|
| id | SERIAL | Primary key, auto-incrementing |
| name | VARCHAR(100) | Product name |
| description | TEXT | Product description |
| price | DECIMAL(10,2) | Product price |
| tax | DECIMAL(10,2) | Tax amount (default: 0) |
| created_at | TIMESTAMPTZ | Product creation timestamp |

**Indexes:**
- Primary Key: `id`
- Index: `name`, `description`, `created_at`

### Item Images Table
Stores product image information.

| Column | Type | Description |
|--------|------|-------------|
| id | SERIAL | Primary key, auto-incrementing |
| item_id | INTEGER | Foreign key to items.id |
| image_path | VARCHAR(255) | Image storage path |
| image_filename | VARCHAR(255) | Image filename |
| original_filename | VARCHAR(255) | Original filename |
| file_extension | VARCHAR(10) | File extension |
| file_size | INTEGER | File size in bytes |
| created_at | TIMESTAMPTZ | Image upload timestamp |

**Indexes:**
- Primary Key: `id`
- Foreign Key: `item_id` references `items(id)`
- Index: `item_id`

### Item Review Table
Stores product reviews with sentiment analysis.

| Column | Type | Description |
|--------|------|-------------|
| id | SERIAL | Primary key, auto-incrementing |
| item_id | INTEGER | Foreign key to items.id |
| usr_id | INTEGER | Foreign key to users.id |
| review_content | TEXT | Review text content |
| score | INTEGER | Rating score (1-5) |
| sentiment | VARCHAR(10) | AI-analyzed sentiment |
| confidence | INTEGER | AI confidence percentage |
| explanation | TEXT | AI analysis explanation |
| created_at | TIMESTAMPTZ | Review creation timestamp |

**Indexes:**
- Primary Key: `id`
- Foreign Key: `item_id` references `items(id)`
- Foreign Key: `usr_id` references `users(id)`
- Index: `item_id`, `usr_id`

## Relationships

1. **Items to Item Images**
   - One-to-Many relationship
   - An item can have multiple images
   - Each image belongs to one item

2. **Items to Reviews**
   - One-to-Many relationship
   - An item can have multiple reviews
   - Each review belongs to one item

3. **Users to Reviews**
   - One-to-Many relationship
   - A user can write multiple reviews
   - Each review is written by one user

## Notes

- All tables use `SERIAL` for auto-incrementing primary keys
- Timestamps are stored with timezone information (TIMESTAMPTZ)
- Foreign key constraints ensure referential integrity
- Indexes are created for frequently queried columns
- All tables include `created_at` for tracking record creation time 