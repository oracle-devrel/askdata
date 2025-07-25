module "apigw_vault_secret"{
    source = "../modules/secrets/apigw_capp_vault_secret"
    region = var.region
    compartment_id = var.security-compartment-id
    vault_id = var.vault_id
    vault_kms_key = var.vault_kms_key
    apigw_capp_secret = module.idcs_confidential_app_apigw.apigw_idcs_capp.client_secret
    apigw_capp_vault_secret_name = "${var.object-prefix}-apigw-capp-secret"
}


module "database_vault_secret" {
    source = "../modules/secrets/db_secret"
    region = var.region
    compartment_id = var.security-compartment-id
    vault_id = var.vault_id
    vault_kms_key = var.vault_kms_key
    apex_db_secret_name = "${var.object-prefix}-apexdb-password"
    apex_db_password = var.adw_admin_password
}