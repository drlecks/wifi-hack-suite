# Wi-Fi Matamoscas: Evil Twin & Rogue AP Detector

```
 _______  _______ _________ _______  _______  _______  _______  _______  _______  _______
(       )(  ___  )\__   __/(  ___  )(       )(  ___  )(  ____ \(  ____ \(  ___  )(  ____ \
| () () || (   ) |   ) (   | (   ) || () () || (   ) || (    \/| (    \/| (   ) || (    \/
| || || || (___) |   | |   | (___) || || || || |   | || (_____ | |      | (___) || (_____
| |(_)| ||  ___  |   | |   |  ___  || |(_)| || |   | |(_____  )| |      |  ___  |(_____  )
| |   | || (   ) |   | |   | (   ) || |   | || |   | |      ) || |      | (   ) |      ) |
| )   ( || )   ( |   | |   | )   ( || )   ( || (___) |/\____) || (____/\| )   ( |/\____) |
|/     \||/     \|   )_(   |/     \||/     \|(_______)\_______)(_______/|/     \|\_______)
```

> A terminal-based Python tool to scan Wi-Fi networks, detect rogue access points (including Evil Twins), and optionally launch countermeasures like deauthentication floods.

---

## ⚙️ Features

- Scan nearby Wi-Fi networks and display key info
- Detect SSIDs with suspicious names or duplicate BSSIDs
- Identify Evil Twin attacks using known SSID validation
- Launch MDK3-based attacks (auth DoS, deauth, etc.)
- Disconnect clients from a target AP (deauth flood)

---

## 🛠️ Requirements

- Linux OS (tested on Kali and Ubuntu)
- Python 3.x
- Superuser privileges (`sudo`)
- Wireless card capable of monitor mode
- Required binaries:
  - `airmon-ng`
  - `airodump-ng`
  - `mdk3`
  - `iw`
  - `iwgetid`

Install them on Debian-based systems with:

```bash
sudo apt update && sudo apt install -y aircrack-ng mdk3 iw
```

---

## 🚀 How to Use

```bash
sudo python3 matamoscas.py
```


## 🔍 Rogue Detection Logic

- Flags SSIDs containing suspicious words:  
  `free`, `gratis`, `openwifi`, `libre`, `guest`
- Detects multiple BSSIDs for same SSID (possible clones)
- Identifies Evil Twins by comparing current channel with rogue ones broadcasting the same SSID

---

## ⚠️ Legal Warning

**This tool is for educational and authorized security testing purposes only.**  
Do **not** use this tool on networks you don’t own or don’t have explicit permission to test.
Check local regulatios before use, radio-signal jamming may be banned on your Country/City.

---

## 📄 License

MIT License

