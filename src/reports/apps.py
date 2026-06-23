from plugins.base import PluginConfig


class ReportsConfig(PluginConfig):
    default = True
    name = "reports"
    plugin_name = "reports"
    plugin_version = "1.0.0"
    plugin_verbose_name = "Reports"
    plugin_description = "Inventory and order reporting endpoints."
    plugin_requires = ["inventory"]
