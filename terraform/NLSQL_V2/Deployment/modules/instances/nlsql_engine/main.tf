provider "oci" {
  region = var.region
}

resource "oci_core_instance" "nlsql_engine_instance" {
    display_name = var.display_name
    compartment_id      = var.compartment_id
    availability_domain = var.availability_domain
    shape               = var.instance_shape
    freeform_tags = var.user_tags
    create_vnic_details {
      subnet_id        = var.subnet_id
      assign_public_ip = false
    }
    source_details {
      boot_volume_size_in_gbs = var.boot_volume_size_in_gbs
      source_type = "image"
      source_id   = var.image_ocid
    }
    metadata = {
      #ssh_authorized_keys = file(each.value.ssh_public_key)
      ssh_authorized_keys = var.ssh_public_key
    }
    shape_config {
      memory_in_gbs = var.memory_gbs
      ocpus = var.ocpu_count
    }
      agent_config {
    are_all_plugins_disabled = false
    is_management_disabled   = false
    is_monitoring_disabled   = false
    plugins_config {
      desired_state = lookup(var.cloud_agent_plugins,"autonomous_linux","DISABLED")
      name          = "Oracle Autonomous Linux"
    }
    plugins_config {
      desired_state = lookup(var.cloud_agent_plugins,"bastion","DISABLED")
      name          = "Bastion"
    }
    plugins_config {
      desired_state = lookup(var.cloud_agent_plugins,"block_volume_mgmt","DISABLED")
      name          = "Block Volume Management"
    }
    plugins_config {
      desired_state = lookup(var.cloud_agent_plugins,"custom_logs","DISABLED")
      name          = "Custom Logs Monitoring"
    }
    plugins_config {
      desired_state = lookup(var.cloud_agent_plugins,"management","DISABLED")
      name          = "Management Agent"
    }
    plugins_config {
      desired_state = lookup(var.cloud_agent_plugins,"monitoring","DISABLED")
      name          = "Compute Instance Monitoring"
    }
    plugins_config {
      desired_state = lookup(var.cloud_agent_plugins,"osms","DISABLED")
      name          = "OS Management Service Agent"
    }
    plugins_config {
      desired_state = lookup(var.cloud_agent_plugins,"run_command","DISABLED")
      name          = "Compute Instance Run Command"
    }
    plugins_config {
      desired_state = lookup(var.cloud_agent_plugins,"vulnerability_scanning","DISABLED")
      name          = "Vulnerability Scanning"
    }
    plugins_config {
      desired_state = lookup(var.cloud_agent_plugins,"java_management_service","DISABLED")
      name = "Oracle Java Management Service"
    }
  }
}