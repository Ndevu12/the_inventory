from plugins.base import PluginConfig


class ProcurementConfig(PluginConfig):
    default = True
    name = "procurement"
    plugin_name = "procurement"
    plugin_version = "1.0.0"
    plugin_verbose_name = "Procurement"
    plugin_description = "Suppliers, purchase orders, and goods-received notes."
    plugin_requires = ["inventory"]
