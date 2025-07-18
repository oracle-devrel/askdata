# Configure the Oracle Cloud Infrastructure Provider
terraform {
  required_providers {
    oci = {
      source  = "oracle/oci"
      version = "~> 5.0"
    }
  }
}

provider "oci" {
  # Authentication will be picked up from:
  # - OCI CLI config file (~/.oci/config)
  # - Environment variables
  # - Instance principal (if running on OCI)
}

# Get availability domain
data "oci_identity_availability_domains" "ads" {
  compartment_id = var.compartment_id
}

# Get the latest Oracle Linux 9 image
data "oci_core_images" "oracle_linux_9" {
  compartment_id   = var.compartment_id
  operating_system = "Oracle Linux"
  filter {
    name   = "display_name"
    values = ["Oracle-Linux-9.*"]
    regex  = true
  }
  sort_by    = "TIMECREATED"
  sort_order = "DESC"
}

# No local variables needed - moved to variables.tf

# Create the compute instance
resource "oci_core_instance" "vm" {
  availability_domain = data.oci_identity_availability_domains.ads.availability_domains[0].name
  compartment_id      = var.compartment_id
  display_name        = "ol9-test-vm"
  shape               = "VM.Standard.E4.Flex"

  shape_config {
    ocpus         = 2         # Customize as needed
    memory_in_gbs = 16        # Customize as needed
  }
   create_vnic_details {
    subnet_id        = var.subnet_id
    display_name     = "primary-vnic"
    assign_public_ip = true
    hostname_label   = "ol9testvm"
  }

  source_details {
    source_type = "image"
    source_id   = data.oci_core_images.oracle_linux_9.images[0].id
  }

  metadata = {
    ssh_authorized_keys = var.ssh_public_key
    user_data = base64encode(templatefile("${path.module}/trust-cloud-init.yaml.tpl", {
      service_name = var.service_name
      namespace = var.namespace
      nl2sql_bucket = var.nl2sql_bucket
      nl2sql_env  = var.nl2sql_env
      nl2sql_port = var.nl2sql_port
      deployment_bucket = var.deployment_bucket
      zipfile = var.zipfile
      app_version  = var.app_version
    }))
  }
}

# to see the resulting file
# clear; sudo cat /var/lib/cloud/instances/*/user-data.txt

# Output the public IP
output "public_ip" {
  value = oci_core_instance.vm.public_ip
}

output "ssh_command" {
  value = "ssh opc@${oci_core_instance.vm.public_ip}"
}

output "service_url" {
  value = "http://${oci_core_instance.vm.public_ip}:${var.nl2sql_port}"
}