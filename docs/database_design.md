# Database Design v1 --- E-commerce Text-to-SQL System

## Purpose

This document defines the database architecture for the Text-to-SQL
project.

The goal is not only to store business data, but to create a realistic
environment where an AI system can reason about:

-   database structure
-   relationships
-   business concepts
-   analytical questions

The schema represents a realistic e-commerce company.

------------------------------------------------------------------------

# Design Principles

## 1. Clear Semantics

Tables and columns should communicate their meaning.

Preferred:

-   payment_status
-   total_amount
-   created_at
-   delivered_at

Avoid ambiguous names:

-   status
-   amount
-   date

unless the context is obvious.

------------------------------------------------------------------------

## 2. Separation of Business Concepts

Different concepts should have separate entities.

Examples:

-   User != Customer
-   Product != Inventory
-   Order != Payment
-   Payment != Refund

Each entity should represent one clear business concept.

------------------------------------------------------------------------

## 3. Preserve Historical Information

Current values are not always enough.

Examples:

-   Product price can change.
-   Product cost can change.
-   Inventory changes over time.

Transactional tables should store values at the time of the event.

Example:

products.base_price

is different from:

order_items.unit_price

------------------------------------------------------------------------

# Architecture Overview

The database contains:

## OLTP Layer

Supports business operations:

-   customers
-   products
-   orders
-   payments
-   shipping
-   inventory

## OLAP Layer

Supports analytics:

-   fact tables
-   dimensions
-   reporting queries

------------------------------------------------------------------------

# OLTP Schema

# Security Domain

## users

Purpose:

Stores authentication identities.

Important attributes:

-   user_id
-   email
-   password_hash
-   account_status
-   created_at
-   last_login_at

Relationships:

-   A user may have zero or one customer profile.
-   A user may have multiple roles.

------------------------------------------------------------------------

## roles

Purpose:

Stores system roles.

Examples:

-   customer
-   admin
-   warehouse_manager
-   finance_manager

Important attributes:

-   role_id
-   role_name

------------------------------------------------------------------------

## user_roles

Purpose:

Maps users to roles.

Important attributes:

-   user_id
-   role_id

------------------------------------------------------------------------

## permissions

Purpose:

Stores available system permissions.

Important attributes:

-   permission_id
-   permission_name

------------------------------------------------------------------------

## audit_logs

Purpose:

Tracks sensitive system changes.

Important attributes:

-   audit_id
-   user_id
-   action
-   table_name
-   record_id
-   timestamp

------------------------------------------------------------------------

# Customer Domain

## customers

Purpose:

Represents buyers using the e-commerce platform.

Important attributes:

-   customer_id
-   user_id
-   first_name
-   last_name
-   phone
-   customer_status
-   registered_at
-   last_order_date

Note:

last_order_date is a derived/cache field. Orders remain the source of
truth.

Relationships:

-   One customer has many orders.
-   One customer has many addresses.
-   One customer has many events.

------------------------------------------------------------------------

## customer_addresses

Purpose:

Stores customer addresses.

Important attributes:

-   address_id
-   customer_id
-   address_type
-   city
-   country
-   postal_code

Relationship:

One customer can have many addresses.

------------------------------------------------------------------------

## customer_events

Purpose:

Stores customer behavior events.

Examples:

-   product_view
-   search
-   add_to_cart
-   purchase

Important attributes:

-   event_id
-   customer_id
-   event_type
-   timestamp

------------------------------------------------------------------------

# Product Domain

## products

Purpose:

Stores product identity information.

Important attributes:

-   product_id
-   name
-   brand_id
-   description

Relationships:

-   One brand has many products.
-   One product has many variants.

------------------------------------------------------------------------

## product_variants

Purpose:

Represents sellable product versions.

Examples:

-   Small Black Shirt
-   Large White Shirt

Important attributes:

-   variant_id
-   product_id
-   SKU
-   size
-   color
-   price

Reason:

Inventory and sales usually belong to a specific variant, not only the
general product.

------------------------------------------------------------------------

## brands

Purpose:

Stores brand information.

Important attributes:

-   brand_id
-   brand_name

Relationship:

One brand has many products.

------------------------------------------------------------------------

## categories

Purpose:

Stores category hierarchy.

Important attributes:

-   category_id
-   category_name
-   parent_category_id

------------------------------------------------------------------------

## product_categories

Purpose:

Maps products to categories.

Reason:

A product can belong to multiple categories.

------------------------------------------------------------------------

# Inventory Domain

## warehouses

Purpose:

Stores warehouse locations.

Important attributes:

-   warehouse_id
-   warehouse_name
-   location

------------------------------------------------------------------------

## inventory

Purpose:

Stores current stock levels.

Important attributes:

-   inventory_id
-   warehouse_id
-   variant_id
-   quantity_on_hand
-   quantity_reserved

Relationship:

A product variant can exist in multiple warehouses.

------------------------------------------------------------------------

## inventory_transactions

Purpose:

Stores inventory changes over time.

Examples:

-   purchase +100
-   sale -5
-   return +1
-   damage -2

Important attributes:

-   transaction_id
-   warehouse_id
-   variant_id
-   transaction_type
-   quantity_change
-   created_at

------------------------------------------------------------------------

# Order Domain

## orders

Purpose:

Represents customer transactions.

Important attributes:

-   order_id
-   customer_id
-   order_status
-   subtotal_amount
-   discount_amount
-   shipping_amount
-   tax_amount
-   total_amount
-   created_at

Relationships:

-   One customer has many orders.
-   One order has many order items.
-   One order has many payment attempts.
-   One order can have many shipments.

------------------------------------------------------------------------

## order_items

Purpose:

Stores products purchased inside an order.

Important attributes:

-   order_item_id
-   order_id
-   variant_id
-   quantity
-   unit_price
-   unit_cost
-   discount_amount
-   tax_amount
-   line_total

------------------------------------------------------------------------

## order_status_history

Purpose:

Stores the lifecycle of an order.

Examples:

-   Created
-   Paid
-   Packed
-   Shipped
-   Delivered
-   Cancelled

Important attributes:

-   history_id
-   order_id
-   status
-   changed_at

------------------------------------------------------------------------

# Payment Domain

## payment_methods

Purpose:

Stores available payment methods.

Examples:

-   Visa
-   Mastercard
-   Apple Pay

Important attributes:

-   payment_method_id
-   method_name
-   provider_name
-   method_type

------------------------------------------------------------------------

## payments

Purpose:

Stores payment attempts.

Important attributes:

-   payment_id
-   order_id
-   payment_method_id
-   amount
-   payment_status
-   attempted_at
-   completed_at
-   transaction_reference

Relationship:

One order can have multiple payment attempts.

------------------------------------------------------------------------

## refunds

Purpose:

Stores refund events.

Important attributes:

-   refund_id
-   payment_id
-   refund_amount
-   refund_status
-   reason
-   created_at

Relationship:

One payment can have multiple refunds.

------------------------------------------------------------------------

# Shipping Domain

## shipping_carriers

Purpose:

Stores shipping companies.

Examples:

-   DHL
-   FedEx
-   Aramex

Important attributes:

-   carrier_id
-   carrier_name

------------------------------------------------------------------------

## shipping_methods

Purpose:

Stores available delivery services.

Examples:

-   Express
-   Standard

Important attributes:

-   shipping_method_id
-   carrier_id
-   method_name

------------------------------------------------------------------------

## shipments

Purpose:

Stores fulfillment shipments.

Important attributes:

-   shipment_id
-   order_id
-   warehouse_id
-   shipping_method_id
-   tracking_number
-   shipment_status
-   shipped_at
-   delivered_at

------------------------------------------------------------------------

## shipment_items

Purpose:

Maps order items to shipments.

Important attributes:

-   shipment_id
-   order_item_id
-   quantity

------------------------------------------------------------------------

# Marketing Domain

Marketing campaigns represent business initiatives used to attract customers, promote products, and measure conversion.

A campaign is not directly stored on orders or products because:

- One campaign can target many products.
- One product can participate in many campaigns over time.
- One customer can interact with multiple campaigns.
- A purchase may be influenced by a campaign but cannot always be inferred from dates alone.

---

## campaigns

Purpose:

Stores marketing campaign information.

Important attributes:

- campaign_id
- campaign_name
- campaign_type
- budget
- start_date
- end_date
- created_at

Relationships:

- One campaign can target many products.
- One campaign can interact with many customers.
- One campaign can generate many attributed conversions.

---

## customer_campaigns

Purpose:

Stores customer interactions with campaigns.

Examples:

- viewed campaign
- clicked advertisement
- opened email
- received promotion

Important attributes:

- customer_id
- campaign_id
- interaction_type
- created_at

Relationships:

- A customer can interact with many campaigns.
- A campaign can have many customer interactions.

Reason:

Customer interaction is different from purchase conversion.

A customer seeing a campaign does not necessarily mean the campaign caused a purchase.

---

## campaign_products

Purpose:

Maps campaigns to the products they target.

Important attributes:

- campaign_id
- product_id
- discount_percentage
- created_at

Relationships:

- One campaign can include many products.
- One product can participate in many campaigns.

Example:

Summer Sale Campaign:

- iPhone
- Laptop
- Headphones

---

## campaign_conversions

Purpose:

Stores explicit marketing attribution between campaigns and orders.

Important attributes:

- conversion_id
- campaign_id
- customer_id
- order_id
- attribution_type
- created_at

Relationships:

- A campaign can generate many conversions.
- A customer can have many campaign conversions.
- A conversion is linked to an order.

Reason:

Purchase attribution cannot always be determined from timestamps.

Example:

A customer may see a campaign in January but purchase in March.

The database should explicitly store when a purchase is considered influenced by a campaign.



------------------------------------------------------------------------

# Engagement Domain

## reviews

Purpose:

Stores customer reviews.

Important attributes:

-   review_id
-   customer_id
-   product_id
-   order_item_id
-   rating
-   comment
-   created_at

------------------------------------------------------------------------

# OLAP Data Warehouse Design

The analytical layer supports business intelligence.

------------------------------------------------------------------------

# Fact Tables

## fact_sales

Stores measurable sales events.

Measures:

-   quantity_sold
-   sales_amount
-   discount_amount
-   tax_amount
-   cost_amount
-   profit_amount
-   refund_amount

------------------------------------------------------------------------

## fact_customer_activity

Stores customer behavior analytics.

------------------------------------------------------------------------

## fact_inventory_snapshot

Stores inventory state over time.

------------------------------------------------------------------------

# Dimension Tables

## dim_customer

Customer analytical information.

## dim_product

Product analytical information.

## dim_category

Category hierarchy.

## dim_campaign

Marketing information.

## dim_date

Time attributes:

-   day
-   month
-   quarter
-   year

------------------------------------------------------------------------

# Security Considerations

The database should implement:

-   password hashing, never plain passwords
-   role-based access control
-   least privilege database users
-   foreign keys and constraints
-   audit logging for sensitive operations

------------------------------------------------------------------------

# Final Design Decisions

## Separate Users and Customers

Reason:

Authentication and business customer information are different concepts.

Impact:

Improved security and maintainability.

------------------------------------------------------------------------

## Separate Product and Inventory

Reason:

Stock depends on warehouse location.

Impact:

Supports multi-warehouse operations.

------------------------------------------------------------------------

## Add Product Variants

Reason:

Inventory and sales occur at the variant level.

Impact:

Supports realistic e-commerce products.

------------------------------------------------------------------------

## Separate Payments and Orders

Reason:

Payments have their own lifecycle including retries and failures.

Impact:

Supports realistic financial workflows.

------------------------------------------------------------------------

## Add Inventory Transactions

Reason:

Current inventory does not explain historical changes.

Impact:

Supports stock analysis.

------------------------------------------------------------------------

## Add Order Status History

Reason:

Orders have lifecycle events.

Impact:

Supports delivery and operational analytics.

------------------------------------------------------------------------

## Add OLAP Layer

Reason:

Analytical workloads differ from transactional workloads.

Impact:

Provides realistic Text-to-SQL evaluation scenarios.

---

## Separate Campaign Interaction From Campaign Conversion

Decision:

Do not store campaign_id directly inside orders or products.

Reason:

Campaign influence is a many-to-many relationship.

- Products can belong to many campaigns.
- Customers can interact with many campaigns.
- Orders may be influenced by campaigns but this cannot always be inferred.

Impact:

The schema supports realistic marketing attribution and Text-to-SQL questions.

---

## Add Campaign Product Mapping

Decision:

Create a campaign_products table.

Reason:

Campaigns can target specific products and products can participate in multiple campaigns over time.

Impact:

Supports questions about product promotions and campaign performance.

---

## Add Campaign Conversion Tracking

Decision:

Create campaign_conversions.

Reason:

Marketing attribution is a separate business concept from customer interaction.

Impact:

Allows analysis of which campaigns generated actual purchases and revenue.
