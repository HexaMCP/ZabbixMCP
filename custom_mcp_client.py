from mcp import ClientSession
from mcp.client.sse import sse_client
import asyncio
import argparse
import whois
import sys

async def run(domains, log_file=None, host_name=None):
    output = []

    async def log_print(message):
        print(message)
        if log_file:
            output.append(message)

    async with sse_client(url="http://localhost:8000/sse") as streams:
        async with ClientSession(*streams) as session:
            await session.initialize()

            # 🔧 Create new Zabbix hosts only if domains are provided
            if domains:
                group = "Domains"
                templates = [
                    "Website certificate by Zabbix agent 2",
                    "Domain Expiry"
                ]

                for domain in domains:
                    result = await session.call_tool("create_domain_host", {
                        "domain": domain.strip(),
                        "group_name": group,
                        "template_names": templates
                    })
                    await log_print(f"\n🆕 Host Creation Result for {domain.strip()}:")
                    for item in result.content:
                        await log_print(item.text)

            # 🔐 Domain + SSL expiry info
            result = await session.call_tool("get_domain_status")
            await log_print("\n🔐 Domain Status Report:")
            for domain in result.content:
                await log_print(domain.text)
            await log_print(f"🔢 Total domains: {len(result.content)}")

            # 🖥️ Host list
            result = await session.call_tool("get_host_list")
            await log_print("\n🖥️ Zabbix Host List:")
            for item in result.content:
                await log_print(item.text)

            # 🔍 ESXi Hosts
            result = await session.call_tool("get_esxi_host_list")
            await log_print("\n🖥️ ESXi Host List:")
            for item in result.content:
                await log_print(item.text)

            # 📊 Total host count
            result = await session.call_tool("get_total_hosts")
            await log_print("\n📊 Total Hosts:")
            for item in result.content:
                await log_print(item.text)

            # 🧠💾 Host Memory and Disk Info
            async def print_memory_and_disk_info(host_name):
                result = await session.call_tool("get_host_memory_disk", {"host_name": host_name})
                await log_print(f"\n🧠💾 Memory/Disk Info for {host_name}:")
                for item in result.content:
                    await log_print(item.text)

                result = await session.call_tool("get_host_disk_space", {"host_name": host_name})
                await log_print(f"\n💾 Disk Size/Available Space for {host_name}:")
                for item in result.content:
                    try:
                        if 'total' in item.text.lower() or 'available' in item.text.lower():
                            value_in_gb = float(item.text.split(':')[-1].strip()) / (1024 ** 3)
                            await log_print(f"{item.text.split(':')[0]}: {value_in_gb:.2f} GB")
                        else:
                            await log_print(item.text)
                    except ValueError:
                        await log_print(f"Error parsing value for {item.text}")

            # ✅ If a host is passed, print its memory/disk info
            if host_name:
                await print_memory_and_disk_info(host_name)

    if log_file:
        with open(log_file, "w", encoding="utf-8") as f:
            f.write("\n".join(output))

async def add_domains_only(domains):
    async with sse_client(url="http://localhost:8000/sse") as streams:
        async with ClientSession(*streams) as session:
            await session.initialize()
            if domains:
                group = "Domains"
                templates = [
                    "Website certificate by Zabbix agent 2",
                    "Domain Expiry"
                ]
                for domain in domains:
                    result = await session.call_tool("create_domain_host", {
                        "domain": domain.strip(),
                        "group_name": group,
                        "template_names": templates
                    })
                    print(f"\n🆕 Host Creation Result for {domain.strip()}:")
                    for item in result.content:
                        print(item.text)

async def memory_disk_only(host_name):
    async with sse_client(url="http://localhost:8000/sse") as streams:
        async with ClientSession(*streams) as session:
            await session.initialize()
            if host_name:
                result = await session.call_tool("get_host_memory_disk", {"host_name": host_name})
                print(f"\n🧠💾 Memory/Disk Info for {host_name}:")
                for item in result.content:
                    print(item.text)

                result = await session.call_tool("get_host_disk_space", {"host_name": host_name})
                print(f"\n💾 Disk Size/Available Space for {host_name}:")
                for item in result.content:
                    try:
                        if 'total' in item.text.lower() or 'available' in item.text.lower():
                            value_in_gb = float(item.text.split(':')[-1].strip()) / (1024 ** 3)
                            print(f"{item.text.split(':')[0]}: {value_in_gb:.2f} GB")
                        else:
                            print(item.text)
                    except ValueError:
                        print(f"Error parsing value for {item.text}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--domain", type=str, help="Comma-separated domain names (e.g., domain1.com,domain2.com)")
    parser.add_argument("--host", type=str, help="Host name to get memory/disk info")
    parser.add_argument("--log", type=str, help="Optional log file to save output")
    parser.add_argument("--add-only", action="store_true", help="Only add domains, do not run full report")
    parser.add_argument("--memory-disk-only", action="store_true", help="Only get memory/disk info for a host")
    args = parser.parse_args()

    domain_list = [d.strip() for d in args.domain.split(',')] if args.domain else []

    if args.add_only:
        asyncio.run(add_domains_only(domain_list))
    elif args.memory_disk_only:
        asyncio.run(memory_disk_only(args.host))
    else:
        asyncio.run(run(domain_list, log_file=args.log, host_name=args.host))