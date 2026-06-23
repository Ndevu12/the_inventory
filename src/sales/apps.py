from plugins.base import PluginConfig


class SalesConfig(PluginConfig):
    default = True
    name = "sales"
    plugin_name = "sales"
    plugin_version = "1.0.0"
    plugin_verbose_name = "Sales"
    plugin_description = "Customers, sales orders, and dispatches."
    plugin_requires = ["inventory"]
