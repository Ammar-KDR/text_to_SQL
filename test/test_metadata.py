from textSQL.database.base import Base
from textSQL.database.warehouse.base import WarehouseBase

from textSQL.database import models
from textSQL.database.warehouse import models as warehouse_models


print("OLTP:")
print(Base.metadata.tables.keys())


print("\nOLAP:")
print(WarehouseBase.metadata.tables.keys())