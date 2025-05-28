from mcp.server.fastmcp import FastMCP
import httpx
import asyncio
import logging
import ssl
import socket
from datetime import datetime
import whois
from dotenv import load_dotenv
import os

# Config
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)
load_dotenv()

ZABBIX_API_URL = os.getenv("ZABBIX_API_URL")
ZABBIX_USER = os.getenv("ZABBIX_USER")
ZABBIX_TOKEN = os.getenv("ZABBIX_TOKEN")

HEADERS = {
    "Content-Type": "application/json-rpc",
    "Authorization": f"Bearer {ZABBIX_TOKEN}"
}

TEMPLATES_TO_MATCH = ["Domain Expiry", "Website certificate by Zabbix agent 2"]

mcp = FastMCP()

# ------------- Tool Definitions -------------

@mcp.tool()
async def get_domain_status() -> list[dict]:
    """Get domain SSL and WHOIS expiry data from Zabbix-monitored hosts"""
    return await fetch_domain_info()

@mcp.tool()
async def get_host_list() -> list[str]:
    hosts = await zabbix_api_request({
        "jsonrpc": "2.0",
        "method": "host.get",
        "params": {
            "output": ["hostid", "host", "name", "status"]
        },
        "auth": ZABBIX_TOKEN,
        "id": 1
    })
    return [f"- {h['name']} (ID: {h['hostid']}, Status: {'Enabled' if h['status']=='0' else 'Disabled'})" for h in hosts['result']]

@mcp.tool()
async def get_esxi_host_list() -> list[str]:
    hosts = await zabbix_api_request({
        "jsonrpc": "2.0",
        "method": "host.get",
        "params": {
            "output": ["hostid", "host", "name", "status"]
        },
        "auth": ZABBIX_TOKEN,
        "id": 2
    })
    return [f"- {h['name']} (ID: {h['hostid']}, Status: {'Enabled' if h['status']=='0' else 'Disabled'})" for h in hosts['result'] if 'esxi' in h['name'].lower()]

@mcp.tool()
async def get_total_hosts() -> list[str]:
    hosts = await zabbix_api_request({
        "jsonrpc": "2.0",
        "method": "host.get",
        "params": {"output": ["hostid"]},
        "auth": ZABBIX_TOKEN,
        "id": 3
    })
    return [f"Total hosts: {len(hosts['result'])}"]

@mcp.tool()
async def get_host_memory_disk(host_name: str) -> list[str]:
    result = await zabbix_api_request({
        "jsonrpc": "2.0",
        "method": "host.get",
        "params": {
            "output": ["hostid", "name"],
            "search": {"name": host_name},
            "selectItems": ["itemid", "name", "key_", "lastvalue"]
        },
        "auth": ZABBIX_TOKEN,
        "id": 4
    })
    if not result['result']:
        return [f"Host '{host_name}' not found"]
    host = result['result'][0]
    items = host.get("items", [])
    memory = [f"- {i['name']}: {i['lastvalue']}" for i in items if "memory" in i['name'].lower()]
    disk = [f"- {i['name']}: {i['lastvalue']}" for i in items if "disk" in i['name'].lower()]
    return ["Memory:"] + memory + ["Disk:"] + disk if memory or disk else ["No memory/disk data found"]

@mcp.tool()
async def get_host_disk_space(host_name: str) -> list[str]:
    result = await zabbix_api_request({
        "jsonrpc": "2.0",
        "method": "host.get",
        "params": {
            "output": ["hostid", "name"],
            "search": {"name": host_name},
            "selectItems": ["itemid", "name", "key_", "lastvalue"]
        },
        "auth": ZABBIX_TOKEN,
        "id": 5
    })
    if not result['result']:
        return [f"Host '{host_name}' not found"]
    items = result['result'][0].get("items", [])
    total = [f"Total: {i['lastvalue']}" for i in items if 'total' in i['name'].lower() or 'size' in i['name'].lower()]
    free = [f"Available: {i['lastvalue']}" for i in items if 'free' in i['name'].lower() or 'available' in i['name'].lower()]
    return total + free if total or free else ["Disk data not found"]

# Additional creation tool
@mcp.tool()
async def create_domain_host(domain: str, group_name: str, template_names: list[str]) -> list[str]:
    group_id = await get_group_id(group_name)
    template_ids = [{"templateid": await get_template_id(tpl)} for tpl in template_names]
    macros = [{"macro": "{$CERT.WEBSITE.HOSTNAME}", "value": domain}]

    payload = {
        "jsonrpc": "2.0",
        "method": "host.create",
        "params": {
            "host": domain,
            "interfaces": [{
                "type": 1,
                "main": 1,
                "useip": 1,
                "ip": "95.216.90.13",
                "dns": "",
                "port": "10052"
            }],
            "groups": [{"groupid": group_id}],
            "templates": template_ids,
            "macros": macros
        },
        "auth": ZABBIX_TOKEN,
        "id": 6
    }
    res = await zabbix_api_request(payload)
    return [f"✅ Host created: {res['result']['hostids'][0]} with macro {{$CERT.WEBSITE.HOSTNAME}} = {domain}"]

# ----------- Helper Functions -----------

async def zabbix_api_request(payload):
    async with httpx.AsyncClient() as client:
        response = await client.post(ZABBIX_API_URL, json=payload, headers=HEADERS)
        response.raise_for_status()
        return response.json()

async def get_group_id(group_name):
    payload = {
        "jsonrpc": "2.0",
        "method": "hostgroup.get",
        "params": {"filter": {"name": [group_name]}},
        "auth": ZABBIX_TOKEN,
        "id": 7
    }
    res = await zabbix_api_request(payload)
    groups = res.get("result", [])
    if not groups:
        raise Exception(f"Group '{group_name}' not found")
    return groups[0]["groupid"]

async def get_template_id(template_name):
    payload = {
        "jsonrpc": "2.0",
        "method": "template.get",
        "params": {"filter": {"host": [template_name]}},
        "auth": ZABBIX_TOKEN,
        "id": 8
    }
    res = await zabbix_api_request(payload)
    templates = res.get("result", [])
    if not templates:
        raise Exception(f"Template '{template_name}' not found")
    return templates[0]["templateid"]

def get_ssl_expiry(domain):
    try:
        ctx = ssl.create_default_context()
        with ctx.wrap_socket(socket.socket(), server_hostname=domain) as s:
            s.settimeout(5)
            s.connect((domain, 443))
            cert = s.getpeercert()
            expiry = datetime.strptime(cert['notAfter'], '%b %d %H:%M:%S %Y %Z')
            return expiry.strftime("%Y-%m-%d")
    except Exception as e:
        return f"SSL Error: {str(e)}"

def get_domain_expiry(domain):
    try:
        w = whois.whois(domain)
        expiry = w.expiration_date
        if isinstance(expiry, list):
            expiry = expiry[0]
        return expiry.strftime("%Y-%m-%d")
    except Exception as e:
        return f"WHOIS Error: {str(e)}"

async def fetch_domain_info():
    payload = {
        "jsonrpc": "2.0",
        "method": "host.get",
        "params": {
            "output": ["hostid", "host", "name", "status"],
            "selectParentTemplates": ["name"]
        },
        "auth": ZABBIX_TOKEN,
        "id": 9
    }
    response = await zabbix_api_request(payload)
    hosts = response.get("result", [])
    results = []
    for host in hosts:
        if not any(tpl['name'] in TEMPLATES_TO_MATCH for tpl in host.get("parentTemplates", [])):
            continue
        domain = host['host']
        results.append({
            "name": host['name'],
            "host": domain,
            "status": "Enabled" if host['status'] == "0" else "Disabled",
            "ssl_expiry": get_ssl_expiry(domain),
            "domain_expiry": get_domain_expiry(domain)
        })
    return results

if __name__ == "__main__":
    mcp.run(transport="sse")