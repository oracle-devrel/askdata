provider "oci" {
  region = var.region
}

provider "oci" {
alias = "home"
region = data.oci_identity_regions.home-region.regions[0]["name"]
}

data "oci_identity_tenancy" "tenancy" {
  tenancy_id = var.tenancy_ocid
}

data "oci_identity_regions" "home-region" {
  filter {
    name   = "key"
    values = [data.oci_identity_tenancy.tenancy.home_region_key]
  }
}

resource "oci_identity_policy" "nl2sql-instance-principal-policy" {
  provider = oci.home
  name           = var.policy_name
  description    = "Policy to allow NL2SQL TrustApp and Engine VM Instance principal auth. The policy also allows the Business APIGW to read secrets in the vault."
  compartment_id = var.security_compartment
  statements = [
    "Allow dynamic-group id ${var.instance_principal_dg_id} to read vaults in compartment id '${var.security_compartment}'",
    "Allow dynamic-group id ${var.instance_principal_dg_id} to manage secret-family in compartment id '${var.security_compartment}'",
    "Allow dynamic-group id ${var.business_apigw_dg_id} to read vaults in compartment id '${var.security_compartment}'",
    "Allow dynamic-group id ${var.business_apigw_dg_id} to manage secret-family in compartment id '${var.security_compartment}'",
    "Allow dynamic-group id ${var.instance_principal_dg_id} to manage objects in compartment id '${var.appdev_compartment}'",
    "Allow dynamic-group id ${var.instance_principal_dg_id} to manage objects in compartment id '${var.database_compartment}'",
    "Allow dynamic-group id ${var.instance_principal_dg_id} to read buckets in compartment id '${var.appdev_compartment}'",
    "Allow dynamic-group id ${var.instance_principal_dg_id} to read certificates in compartment id '${var.security_compartment}'",
    "Allow dynamic-group id ${var.instance_principal_dg_id} to read tags in compartment id '${var.security_compartment}'",
    "Allow dynamic-group id ${var.instance_principal_dg_id} to read tags in compartment id '${var.appdev_compartment}'",
    "Allow dynamic-group id ${var.instance_principal_dg_id} to read tags in compartment id '${var.database_compartment}'",
  ]
}

