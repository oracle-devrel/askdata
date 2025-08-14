# Introduction

## Summary

This document provides instructions for setting up resources for the
Oracle AskData application. It does not cover details related to the
Administration UI developed with APEX, including the Trusted component.

### Overview

The following activities are covered as part of this document,

- IDCS Application setup
- API Gateway setup
- ODA Setup
- VBCS Setup
- VM1- Engine
- Misc.

| Component | Details |
|----|----|
| IDCS Application | This component enables the generation and use of OAuth-based authentication across multiple layers, including the UI (VBCS), Conversation UI (ODA), and the API Gateway. |
| API Gateway | The API Gateway service allows us to publish APIs with private endpoints accessible within our network, while also exposing them via public IP addresses for internet access. It supports enabling SSL over HTTP and secures the endpoints with an authentication layer. |
| Oracle Digital Assistant | The solution utilizes ODA to provide chat-based interactions between business end users and the bot. User-entered prompts are routed to the backend LLM component, and the responses are displayed within the chat widget. |
| VBCS | VBCS (Visual Builder Cloud Service) provides an enhanced user experience through interactive elements such as dynamic tables and rich graphical visualizations, enabling users to engage with data more effectively. The VBCS pages are secured with built-in authentication and role-based access control, ensuring that only authorized users can access or interact with the application. |
| VM1 | The Compute VM hosts the core backend logic developed in Python, which supports key functionalities such as Natural Language to SQL (NL2SQL) processing, enrichment of backend data, and querying or persisting data within backend tables. |
