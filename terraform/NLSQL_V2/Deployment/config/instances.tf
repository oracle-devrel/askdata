locals{ #TRUST APP DEPLOYPARAMETERS
    trustapp_memory_gbs = 32
    trustapp_ocpu = 2
    trustapp_boot_volume = 250
    trustapp_image_ocid = var.linux_image_ocid
    trustapp_shape = var.linux_image_shape
    trustapp_ssh_public_key = file("./files/ssh-keys/ssh-public.pub")
    trustapp_plugins = {
        autonomous_linux        = "DISABLED"
        bastion                 = "DISABLED"
        block_volume_mgmt       = "DISABLED"
        custom_logs             = "ENABLED"
        management              = "ENABLED"
        monitoring              = "ENABLED"
        osms                    = "DISABLED"
        run_command             = "ENABLED"
        vulnerability_scanning  = "DISABLED"
        java_management_service = "DISABLED"
    }
}

locals{ #NLSQL ENGINE APP DEPLOY PARAMETERS
    nlsql_engine_memory_gbs = 16
    nlsql_engine_ocpu = 2
    nlsql_engine_boot_volume = 300
    nlsql_engine_image_ocid = var.linux_image_ocid
    nlsql_engine_shape = var.linux_image_shape
    nlsql_engine_ssh_public_key = file("./files/ssh-keys/ssh-public.pub")
    nlsql_engine_plugins = {
        autonomous_linux        = "DISABLED"
        bastion                 = "DISABLED"
        block_volume_mgmt       = "DISABLED"
        custom_logs             = "ENABLED"
        management              = "ENABLED"
        monitoring              = "ENABLED"
        osms                    = "DISABLED"
        run_command             = "ENABLED"
        vulnerability_scanning  = "DISABLED"
        java_management_service = "DISABLED"
    }
}

module "trust_python_app" {
    source = "../modules/instances/trust_python_app"
    display_name = "${var.object-prefix}-trustapp"
    compartment_id = var.app-compartment-id
    region = var.region
    availability_domain = var.availability-domain
    subnet_id = var.private_subnet
    instance_shape = local.trustapp_shape
    image_ocid = local.trustapp_image_ocid
    ssh_public_key = local.trustapp_ssh_public_key
    memory_gbs = local.trustapp_memory_gbs
    ocpu_count = local.trustapp_ocpu
    boot_volume_size_in_gbs = local.trustapp_boot_volume
    cloud_agent_plugins = local.trustapp_plugins
    user_tags = var.resource_tags
}

module "nlsql_engine_app"{
    source = "../modules/instances/nlsql_engine"
    display_name = "${var.object-prefix}-nlsqlengine"
    compartment_id = var.app-compartment-id
    region = var.region
    availability_domain = var.availability-domain
    subnet_id = var.public_subnet
    instance_shape = local.nlsql_engine_shape
    image_ocid = local.nlsql_engine_image_ocid
    ssh_public_key = local.nlsql_engine_ssh_public_key
    memory_gbs = local.nlsql_engine_memory_gbs
    ocpu_count = local.nlsql_engine_ocpu
    boot_volume_size_in_gbs = local.nlsql_engine_boot_volume
    cloud_agent_plugins = local.nlsql_engine_plugins
    user_tags = var.resource_tags
}
