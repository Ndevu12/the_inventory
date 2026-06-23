from plugins.base import PluginConfig


class InventoryConfig(PluginConfig):
    # Required so Django picks this class over the imported PluginConfig base
    # when auto-detecting the app's config (see docs/plugins.md).
    default = True
    name = "inventory"
    plugin_name = "inventory"
    plugin_version = "1.0.0"
    plugin_verbose_name = "Inventory"
    plugin_description = "Core inventory domain: products, stock, warehouses, lots."
