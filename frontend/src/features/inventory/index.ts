export { ProductListPage } from "./pages/product-list-page"
export { ProductCreatePage } from "./pages/product-create-page"
export { ProductEditPage } from "./pages/product-edit-page"
export { ProductDetailPage } from "./pages/product-detail-page"

export { CategoryListPage } from "./pages/category-list-page"
export { StockRecordsPage } from "./pages/stock-records-page"
export { LotListPage } from "./pages/lot-list-page"

export type {
  Product,
  Category,
  StockRecord,
  StockMovement,
  StockLot,
} from "./types/inventory.types"

export { LocationListPage } from "./pages/location-list-page"
export { LocationDetailPage } from "./pages/location-detail-page"
export { LocationTree } from "./components/locations/location-tree"
export type { LocationTreeHandle } from "./components/locations/location-tree"
export { LocationFormDialog } from "./components/locations/location-form-dialog"
export { CapacityBar } from "./components/locations/capacity-bar"
export {
  useLocations,
  useLocation,
  useLocationsByIds,
  useLocationStockPage,
  useCreateLocation,
  useUpdateLocation,
  useDeleteLocation,
} from "./hooks/use-locations"
export type {
  StockLocation,
  StockLocationFormData,
  StockRecordAtLocation,
} from "./types/location.types"
export type { Warehouse, WarehouseFormData } from "./types/warehouse.types"
export { warehousesApi } from "./api/warehouses-api"
export { useWarehousesForSelect } from "./hooks/use-warehouses"

export { MovementListPage } from "./pages/movement-list-page"
export { MovementDetailPage } from "./pages/movement-detail-page"
export { MovementCreatePage } from "./pages/movement-create-page"
export { MovementTable } from "./components/movements/movement-table"
export { MovementForm } from "./components/movements/movement-form"
export { getMovementColumns } from "./components/movement-columns"
export { useMovements, useMovement, useCreateMovement } from "./hooks/use-movements"
export { useMovementFormStore } from "./stores/movement-form-store"
export {
  createMovementFormSchema,
  MOVEMENT_TYPE_VALUES,
  ALLOCATION_STRATEGY_VALUES,
} from "./helpers/movement-schemas"
export type {
  StockMovementCreatePayload,
  MovementType,
  MovementListParams,
} from "./api/movements-api"
