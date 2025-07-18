### Public Load Balancer

#### Create Load Balancer

Since private APIs are not accessible from the VBCS applications, and the private endpoint feature is not supported by the custom component of ODA, you may create a load balancer of type public and have the private APIs fronted by the LB.

[Creating a Load Balancer](https://docs.oracle.com/en-us/iaas/Content/Balance/Tasks/managingloadbalancer_topic-Creating_Load_Balancers.htm)

Update the Access Control List to include the output IP address of VBCS instance. In case of ODA, the outbound IP address is not available, therefore you need to include OCI’s OSN (or OCI all) IP addresses of that region.

[docs.oracle.com/en-us/iaas/tools/public_ip_ranges.json](https://docs.oracle.com/en-us/iaas/tools/public_ip_ranges.json)


![ ](./business_media/media/image108.png)


![ ](./business_media/media/image109.png)
