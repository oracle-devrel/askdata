provider "oci" {
  region = var.region
}
resource "oci_vault_secret" "apexdb_vault_secret" {
    #Required
    compartment_id = var.compartment_id
    key_id = var.vault_kms_key
    secret_name = var.apex_db_secret_name
    vault_id = var.vault_id

    #Optional
    description = "Database Password Secret"
    secret_content {
        #Required
        content_type = "BASE64"
        #Optional
        content = base64encode(var.apex_db_password)
    }
}