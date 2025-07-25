locals {
    adw_cpu_core_count = 2
    storage_tbs = 1
    admin_password = var.adw_admin_password
    wallet_password = var.adw_wallet_password
    database_version = var.adw_db_version
    #database_prefix = regex_replace(var.object-prefix, "[^a-zA-Z0-9]", "")
    database_prefix = regex("^[a-zA-Z0-9]+$",var.object-prefix)

}

module "apex_adw"{#ADW
    source = "../modules/adw/apex"
    region = var.region
    compartment_ocid = var.database-compartment-id
    admin_password = local.admin_password
    wallet_password = local.wallet_password
    cpu_core_count = local.adw_cpu_core_count
    data_storage_size_in_tbs = local.storage_tbs
    db_name = "${local.database_prefix}apexdb"
    display_name = "${local.database_prefix}apexadw"
    user_tags = var.resource_tags
    db_version = local.database_version
    subnet_id = var.private_subnet
}

module "business_adw"{ #ADW
    source = "../modules/adw/business"
    region = var.region
    compartment_ocid = var.database-compartment-id
    admin_password = local.admin_password
    wallet_password = local.wallet_password
    cpu_core_count = local.adw_cpu_core_count
    data_storage_size_in_tbs = local.storage_tbs
    db_name = "${local.database_prefix}businessdb"
    display_name = "${local.database_prefix}businessadw"
    user_tags = var.resource_tags
    db_version = local.database_version
}