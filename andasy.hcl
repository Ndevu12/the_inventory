
# andasy.hcl app configuration file generated for theinventoryapp on Wednesday, 18-Mar-26 19:41:50 CAT
#
# See https://github.com/quarksgroup/andasy-cli for information about how to use this file.

app_name = "theinventoryapp"

app {

  env = {
  }

  port = 8000

  primary_region = "kgl"

  compute {
    cpu      = 1
    memory   = 1024
    cpu_kind = "shared"
  }

  process {
    name = "theinventoryapp"
  }

}
