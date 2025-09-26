# Troubleshooting Guide

## ODA Chat Widget Issues

### Chat Widget Loading Error

When experiencing issues with the ODA chat widget failing to load, check the following configurations:

**ODA Channel Configuration:**
- Ensure the ODA channel is set to 'Enabled' in the channel definition page
- Verify that ODA channel authentication is set to 'Disabled'

**VBCS Main Application Configuration:**
- Confirm that all IDCS details are correct, including:
  - IDCS URL
  - Client ID
  - Client Secret
- Check for any typos or extra white spaces in the configuration values

### Chat Widget Response Issues

When the ODA chat widget is not returning the expected responses, follow these troubleshooting steps:

**API Gateway Validation:**
- Verify that the APIGW endpoint is returning the expected data (refer to the 'Validation' section in the documentation)
- Test the direct backend URL to ensure it's returning the expected data, since APIGW routes traffic to the backend server

**API Gateway Configuration:**
- Confirm that IDCS details used for Authentication are correct:
  - IDCS URL
  - Client ID
  - Client Secret
- Verify there are no typos or white spaces in the configuration
- Check that route details are properly configured
- Ensure IDCS URLs are specific to your tenancy and not using generic sample URLs from documentation

**Backend Server Verification:**
- Confirm that backend services are running (refer to the VM section in the documentation)

## Data Visualization Issues

### Graph and Table Data Link Problems

When links to view graph and table data are not working properly:

**VBCS Application Configuration:**
- Verify that IDCS details used for Authentication are correct:
  - IDCS URL
  - Client ID
  - Client Secret
- Check for typos and extra white spaces in configuration values
- Confirm the application is referencing the correct APIGW endpoint
- Ensure backend services `/igraph/` and `/getdata/` are running properly

## Access Control Issues

### User Access Errors in VBCS Application

When users encounter access-related errors when opening VBCS applications:

**User Permission Verification:**
- Confirm that the user has been added to the appropriate IDCS group
- Refer to the "End-user access to VBCS application" section in the documentation for proper group assignment procedures

## [Return home](../../../README.md)