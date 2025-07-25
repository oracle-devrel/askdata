variable "region" {
    type = string
    description = "Region where the components will be deployed."
}
variable "tenancy_ocid" {
  type = string
  description = "OCID for the OCI tenancy"
}
variable "idcs_endpoint" {
    type = string
    description = "IDCS Endpoint URL, DO NOT INCLUDE THE PORT NUMBER."
}
variable "object-prefix" {
    type = string
    description = "Prefix to attach to every resource deployed with the TF Code."
}
variable "storage-namespace"{
    type = string
    description = "Object Storage Namespace."
}
variable "private_subnet" {
    type = string
    description = "OCID for the private subnet deployed by the landing zone stack."
}
variable "public_subnet" {
    type = string
    description = "OCID for the public subnet deployed by the landing zone stack."
}
variable "database_subnet" {
    type = string
    description = "OCID for the database subnet deployed by the landing zone stack."
}
variable "availability-domain" {
  description = "AD Key in multi AD regions, example: GqIF:US-CHICAGO-1-AD-1"
  type = string
}
variable "app-compartment-id" {
    type = string
    description = "Application compartment OCID deployed by the LZ Stack."
}
variable "network-compartment-id" {
    type = string
    description = "Network compartment OCID deployed by the LZ Stack."
}
variable "database-compartment-id" {
    type = string
    description = "Database compartment OCID deployed by the LZ Stack."
}
variable "security-compartment-id" {
    type = string
    description = "Security compartment OCID deployed by the LZ Stack."
}

variable "linux_image_ocid" {
  type = string
  description = "OCID for image to deploy EngineApp and TrustApp VMs."
}
variable "linux_image_shape" {
  type = string
  description = "Instance shape for EngineApp and TrustApp VMs."
}

variable "resource_tags" {
    type = map(string)
    description = "Freeform tags for the resources."
    default = {
        nl2sql_env="PoC"
    }
}
variable "adw_admin_password" {
  description = "Password for autonomous databases"
  type = string
}
variable "adw_wallet_password" {
  description = "Password for autonomous databases wallet."
  type = string
}
variable "adw_db_version" {
  description = "ADW version to deploy. Defaults to 23ai."
  type = string
  default = "23ai"
}
variable "lb_cert_id"{
  description = "OCID for the LB Certificate uploaded in Certificate Manager"
  type = string
}
variable "lb_hostname" {
  description = "Hostname for the Load Balancer Public Endpoint."
  type = string
}
variable "vault_id" {
  description = "OCID for the vault deployed by the LZ or and existing vault for the secrets."
  type = string
}
variable "vault_kms_key" {
  description = "KMS Key OCID for the secrets."
  type = string
}
variable "idcs_app_audience" {
  type = string
  description = "Audience URN for the IDCS APP. Example: urn:nl2sql:business"
}
variable "apex_app_redirect_uri" {
  type = string
  description = "APEX App redirect URL. Deploy with default, change after the APEX Application has been setup and apply terraform again."
  default = "<your-adb>/ords/apex_authentication.callback"
}
variable "apex_app_logout_uri" {
  type = string
  description = "APEX App logout URL. Deploy with default, change after the APEX Application has been setup and apply terraform again."
  default = "<your-adb>/ords/f?p=your_apex_number_here"
}