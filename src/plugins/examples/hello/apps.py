from plugins.base import PluginConfig


class HelloPluginConfig(PluginConfig):
    default = True
    name = "plugins.examples.hello"
    label = "hello_plugin"
    plugin_name = "hello"
    plugin_version = "1.0.0"
    plugin_verbose_name = "Hello (example)"
    plugin_description = "Reference plugin showing how to add an API endpoint."
    plugin_requires = ["inventory"]
