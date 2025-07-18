output "gpu_private_ip_address" {
    value = oci_core_instance.GPU_instance.private_ip
}
output "gpu_vm_ocid"{
    value = oci_core_instance.GPU_instance.id
}