provider "oci" {
  region = var.region
}
resource "oci_vault_secret" "apigw_capp_vault_secret" {
    #Required
    compartment_id = var.compartment_id
    key_id = var.vault_kms_key
    secret_name = var.apigw_capp_vault_secret_name
    vault_id = var.vault_id

    #Optional
    description = "APIGateway Confidential App Secret"
    secret_content {
        #Required
        content_type = "BASE64"
        #Optional
        content = base64encode(var.apigw_capp_secret)
    }
}