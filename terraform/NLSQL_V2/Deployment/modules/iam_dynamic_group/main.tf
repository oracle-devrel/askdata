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

resource "oci_identity_dynamic_group" "instance_principal_dynamic_group" {
    #Required
    provider = oci.home
    compartment_id = var.tenancy_ocid
    description = "Dynamic group for NL2SQL OCI Instances."
    matching_rule = var.instance_dynamic_group_rule
    name = var.dynamic_group_name

}

resource "oci_identity_dynamic_group" "business_api_gw_dynamic_group" {
    #Required
    provider = oci.home
    compartment_id = var.tenancy_ocid
    description = "Dynamic group for Business API GW."
    matching_rule = var.api_gw_dynamic_group_rule
    name = var.dynamic_group_name

}
