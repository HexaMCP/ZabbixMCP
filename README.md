# 🔧 ZabbixMCP – Custom MCP Client & Server for Zabbix + Domain Monitoring

This project implements a **custom MCP (Model Context Protocol)** client and server to manage Zabbix-monitored hosts and monitor domain status (SSL + WHOIS expiry). It uses [FastMCP](https://github.com/ContextualAI/fastmcp) and connects with your Zabbix API to automate:

- ✅ Domain-based host creation  
- 🔐 SSL & WHOIS checks  
- 🖥️ Host listing  
- 📊 Resource monitoring (memory/disk)

---

## 📁 Project Structure

```
ZabbixMCP/
  ├── mcp_client.py # MCP Client - interacts with the MCP server and Zabbix tools
  ├── mcp_server/ # MCP Server setup and FastAPI/Tool handler files
  └── README.md # You're reading it!
  └── .env # For your Zabbix server login credentials

```

---

## 📦 Requirements

### Python Dependencies

Install via:

```bash
pip install -r requirements.txt
```

**`requirements.txt`**

```
mcp
httpx
python-dotenv
python-whois
```

### System Requirements

- Python 3.9+
- Active **Zabbix server** with API access
- Internet connectivity (for WHOIS & SSL)
- `.env` file configured with Zabbix credentials

---

## 🔐 Environment Setup

Create a `.env` file at the project root with:

```
ZABBIX_API_URL=https://your-zabbix-server/api_jsonrpc.php
ZABBIX_USER=your_zabbix_username
ZABBIX_TOKEN=your_zabbix_api_token
```

> ⚠️ The API token must have permission to query and create hosts.

---

## 🚀 Running the MCP Server

Launch your MCP server:

```bash
python mcp_server/custom_mcp_server.py
```

This starts the SSE-powered MCP server at:

```
http://localhost:8000/sse
```

---

## 💻 Using the MCP Client

You can:

- Create Zabbix hosts from domains
- Fetch SSL and WHOIS expiry data
- List all Zabbix/ESXi hosts
- Show memory/disk data for a host

### Basic Usage

```bash
python mcp_client.py
```

### With Host Info (Memory/Disk)

```bash
py custom_mcp_client.py --host your-server-name --memory-disk-only
```

### Create Host & Log Output

```bash
py custom_mcp_client.py --domain virtunest.com --add-only --log output.txt
```

---

## 🧠 MCP Tools Available

| Tool Name                | Description                                                   |
|--------------------------|---------------------------------------------------------------|
| `create_domain_host`     | Create a Zabbix host using a domain name and templates        |
| `get_domain_status`      | Check SSL & WHOIS expiry for Zabbix-monitored domains         |
| `get_host_list`          | List all Zabbix hosts                                         |
| `get_esxi_host_list`     | List ESXi-specific hosts                                      |
| `get_total_hosts`        | Show total number of hosts in Zabbix                         |
| `get_host_memory_disk`   | Display memory and disk usage for a specific host             |
| `get_host_disk_space`    | Show total and available disk space for a specific host       |

---

## ⚙️ Zabbix Prerequisites

Ensure the following exist in your Zabbix setup:

- ✅ **Host Group**: `Domains`  
- ✅ **Templates**:
  - `Domain Expiry`
  - `Website certificate by Zabbix agent 2`

> If missing, the `create_domain_host` tool will fail.

---

## 📝 Sample Output

```text
🆕 Host Creation Result for example.com:
✅ Host created: 12345 with macro {$CERT.WEBSITE.HOSTNAME} = example.com

🔐 Domain Status Report:
- example.com
  SSL Expiry: 2025-10-01
  Domain Expiry: 2026-02-15

🖥️ Zabbix Host List:
- example.com (ID: 12345, Status: Enabled)

🧠💾 Memory/Disk Info for esxi-node-01:
Memory:
- Free memory: 4294967296
Disk:
- Disk space on /: 21474836480

💾 Disk Size/Available Space for esxi-node-01:
Total: 21474836480
Available: 10737418240
```

---

## 🛠️ Troubleshooting

- ❌ **SSL Error**: Ensure port 443 is open and the domain has a valid certificate.
- ❌ **WHOIS Error**: Some registrars hide expiry data. Try another domain.
- ❌ **Template/Group Not Found**: Verify required templates and group exist in Zabbix.

---

---

## 📜 License

This project is licensed under the [MIT License](LICENSE) — © 2025 [blaze.ws](https://blaze.ws) **BLAZE WEB SERVICES PRIVATE LIMITED**

---

---

📞 Support

For any issues or assistance with the integration, please contact [blaze.ws](https://blaze.ws) for support.

You can reach out to us for troubleshooting, feature requests, or any general inquiries related to this MCP integration.

---
