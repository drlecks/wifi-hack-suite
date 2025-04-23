# Rogue AP Lab

**Rogue AP Lab** is a Python-based tool that creates a fully functional rogue Wi-Fi Access Point with a captive portal, allowing for ethical phishing or testing purposes in security research and penetration testing labs.

> ⚠️ **Disclaimer:** This tool is intended for educational and authorized testing environments only. Unauthorized use against networks you do not own or have explicit permission to test is illegal.

---

## Features

- Interactive CLI interface for configuration
- Sets up a rogue Wi-Fi Access Point with a user-defined SSID
- Embeds a Python-based HTTP server (no need for PHP or external servers)
- Captive portal login page that captures submitted credentials
- Automatically redirects all HTTP requests to the fake login page
- Clean restoration of all system settings after termination

---

## Requirements

- WiFi interface with **Access Point** mode available
- Linux-based system
- Python 3
- `hostapd`, `dnsmasq`, `iptables`
- Root privileges
   
   ```bash
   sudo apt update && sudo apt install -y python3 hostapd dnsmasq iptables
   sudo apt install -y net-tools wireless-tools iw
   ```
---

## Setup & Usage

1. Clone the repository:
   ```bash
   git clone https://github.com/yourname/rogue-ap-lab
   cd rogue-ap-lab
   ```

2. Prepare your HTML content:
   - Create a folder with at least an `index.html` file.
   - The login form should POST to `/stealer` with `username` and `password` fields.

3. Run the rogue AP tool:
   ```bash
   sudo python3 rogue-ap.py
   ```

4. Follow the prompts:
   - Select the wireless interface to use (must support AP mode)
   - Enter the absolute path to your HTML root directory
   - Optionally, define a custom SSID (default: `Free Wifi`)

5. Once running:
   - Connect a device to the fake AP
   - Open a browser and navigate to any HTTP site to trigger redirection
   - Captured credentials are saved to `stolen_credentials.txt`

6. Terminate the AP:
   - Type `q` and press Enter, or use `Ctrl+C`

---

## File Structure

- `rogue-ap.py`: Main script that sets up the AP and web server
- `index.html`: The fake login page served by the captive portal
- `stolen_credentials.txt`: Output file where credentials are logged

---

## Example Login Form (HTML)
```html
<form method="POST" action="/stealer">
  <input type="text" name="username" placeholder="Username">
  <input type="password" name="password" placeholder="Password">
  <button type="submit">Login</button>
</form>
```

---

## Cleanup and Recovery

- Automatically:
  - Restores original IP settings
  - Restores iptables configuration
  - Deletes temporary configuration files
  - Restarts NetworkManager

---

## License

MIT License.  

---

## Author

Created by drlecks – Security Tools Enthusiast

