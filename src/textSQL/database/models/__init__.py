"""
Database ORM models.

Import all models here so SQLAlchemy metadata
contains the complete schema.
"""

## Security Domain
from .users import User
from .role import Role
from .permission import Permission
from .user_role import UserRole
from .role_permission import RolePermission
from .audit_log import AuditLog


## Customer Domain
from .customers import Customer
from .customer_address import CustomerAddress
from .customer_event import CustomerEvent


## Order Domain

from .brands import Brand
from .products import Product
from .product_variant import ProductVariant
from .category import Category
from .product_category import ProductCategory

## Inventory Domain

from .warehouse import Warehouse
from .inventory import Inventory
from .inventory_transactions import InventoryTransaction

## Order Domain
from .orders import Order
from .order_items import OrderItem
from .order_status_history import OrderStatusHistory

## Payment Domain

from .payment_method import PaymentMethod
from .payments import Payment
from .refund import Refund

## Shipping Domain

from .shipping_carrier import ShippingCarrier
from .shipping_method import ShippingMethod
from .shipment import Shipment
from .shipment_items import ShipmentItem

## Marketing Domain

from .campaign import Campaign
from .customer_campaign import CustomerCampaign
from .campaign_products import CampaignProduct
from .campaign_conversion import CampaignConversion


## Review
from .review import Review