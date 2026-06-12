# Asterisk Smarthome – Installation Guide

This guide describes the setup of the Asterisk-based smarthome PBX server (Ubuntu Server on Proxmox), including system preparation, Asterisk installation, Piper TTS, and the Python smarthome services (calendar, news, weather, STT/TTS).

## 1. System Preparation

```bash
sudo apt install net-tools -y

# Enable and start SSH
sudo systemctl enable ssh
sudo systemctl start ssh

# Check network configuration
ifconfig

# Update system and install base packages
sudo apt update && sudo apt upgrade -y && sudo apt autoremove -y && sudo apt clean -y
sudo apt install qemu-guest-agent systemd-zram-generator -y
```

### Configure ZRAM

Why ZRAM config? Because you can configure the LXC container or Proxmox VM with only 512 MB RAM.

```bash
sudo nano /etc/systemd/zram-generator.conf
```

Example configuration:

```ini
[zram0]
zram-size = ram / 2
compression-algorithm = zstd
```

### Enable QEMU Guest Agent and reboot

```bash
sudo systemctl enable --now qemu-guest-agent
sudo reboot
```

After reboot, verify swap/zram is active:

```bash
swapon --show
```

## 2. Install Asterisk and Dependencies

```bash
sudo apt install -y asterisk
sudo apt install -y asterisk asterisk-config \
    python3 python3-pip ffmpeg wget curl espeak
```

## 3. Create Smarthome Directory

```bash
sudo mkdir -p /opt/smarthome
sudo chown -R $USER:$USER /opt/smarthome
cd /opt/smarthome
```

## 4. Install Piper TTS (German Voice)

```bash
cd /opt/smarthome
wget https://github.com/rhasspy/piper/releases/latest/download/piper_linux_x86_64.tar.gz
tar -xzf piper_linux_x86_64.tar.gz

# Download German voice model (Thorsten, medium quality)
wget https://huggingface.co/rhasspy/piper-voices/resolve/main/de/de_DE/thorsten/medium/de_DE-thorsten-medium.onnx
wget https://huggingface.co/rhasspy/piper-voices/resolve/main/de/de_DE/thorsten/medium/de_DE-thorsten-medium.onnx.json

rm -f piper_linux_x86_64.tar.gz
```

## 5. Configure Asterisk

### Backup and edit PJSIP configuration

```bash
sudo mv /etc/asterisk/pjsip.conf /etc/asterisk/pjsip.conf.bak
sudo nano /etc/asterisk/pjsip.conf
```

Then add following:

```bash
[transport-udp]
type=transport
protocol=udp
bind=0.0.0.0

[remote]
type=endpoint
context=smarthome
disallow=all
allow=ulaw
allow=alaw
allow=g722
allow=opus
auth=remote
aors=remote
media_encryption=sdes
media_encryption_optimistic=yes
rtp_symmetric=yes
rewrite_contact=yes

[remote] # As example Linphone
type=auth
auth_type=userpass
username=remote
password=remptepassword

[remote]
type=aor
max_contacts=1
remove_existing=yes

#[room1]
#type=endpoint
#context=smarthome
#disallow=all
#allow=ulaw
#allow=alaw
#allow=g722
#allow=opus
#auth=conference
#aors=conference
#media_encryption=sdes
#media_encryption_optimistic=yes
#rtp_symmetric=yes
#rewrite_contact=yes

#[room1]
#type=auth
#auth_type=userpass
#username=room1
#password=password

#[room1]
#type=aor
#max_contacts=1
#remove_existing=yes
```

### Backup and edit dialplan (extensions.conf)

```bash
sudo mv /etc/asterisk/extensions.conf /etc/asterisk/extensions.conf.bak
sudo nano /etc/asterisk/extensions.conf
```

Then add following:

```bash
[smarthome]

; ─── Extension 100: STT Test — Record call as WAV ───
exten => 100,1,Answer()
 same => n,Wait(1)
 same => n,Playback(beep)
 same => n,Record(/var/spool/asterisk/recording-${UNIQUEID}.wav,5,30,k)
 same => n,Playback(vm-goodbye)
 same => n,Hangup()

; ─── Extension 200: TTS-Test — Reading Text ─────────────
exten => 200,1,Answer()
 same => n,Wait(1)
 same => n,AGI(/opt/smarthome/tts.py)
 same => n,Playback(/opt/smarthome/tts-output)
 same => n,Hangup()

; ─── Extension 300: STT + Whisper + TTS Response ──────────
;exten => 300,1,Answer()
; same => n,Wait(1)
; same => n,Playback(beep)
; same => n,Record(/var/spool/asterisk/stt-latest.wav,3,20,k)
; same => n,AGI(/opt/smarthome/stt.py)
; same => n,Playback(/opt/smarthome/stt-answer)
; same => n,Hangup()

exten => 300,1,Answer()
 same => n,Wait(1)
 same => n,Playback(beep)
 same => n,Record(/var/spool/asterisk/stt-latest.wav,3,20,k)
 same => n,AGI(/opt/smarthome/stt.py)
 same => n,Playback(/opt/smarthome/stt-answer)
 same => n,Hangup()

exten => 400,1,Answer()
 same => n,Wait(1)
 same => n,Playback(beep)
 same => n(recording),Record(/var/spool/asterisk/stt-latest.wav,5,300,k)
 same => n,AGI(/opt/smarthome/stt.py)
 same => n,Playback(/opt/smarthome/stt-answer)
 same => n,Goto(400,recording)

; ── Intercom: Different rooms ────────────
;exten => 501,1,Dial(PJSIP/room1,30)
; same => n,Hangup()
; ── Add different rooms here. You can copy-paste room1.

; ── Extension 601: Google Calendar ───────────────────────
exten => 601,1,Answer()
 same => n,Wait(1)
 same => n,AGI(/opt/smarthome/calendar.py)
 same => n,Playback(/opt/smarthome/calendar-output)
 same => n,Hangup()

; ── Extension 602: Weather ────────────────────────────────
exten => 602,1,Answer()
 same => n,Wait(1)
 same => n,AGI(/opt/smarthome/weather.py)
 same => n,Playback(/opt/smarthome/weather-output)
 same => n,Hangup()

; ── Extension 603: Tagesschau news feed ────────────────
exten => 603,1,Answer()
 same => n,Wait(1)
 same => n,AGI(/opt/smarthome/news.py)
 same => n,Playback(/opt/smarthome/news-output)
 same => n,Hangup()
```

### Enable and start Asterisk

```bash
sudo systemctl enable asterisk
sudo systemctl restart asterisk
```

### Verify PJSIP endpoints

```bash
sudo asterisk -r
```

Inside the Asterisk CLI:

```
asterisk*CLI> pjsip show endpoints
```

### Configure logging (optional)

```bash
sudo nano /etc/asterisk/logger.conf
```

Maybe you uncomment following lines:

```bash
messages.log => notice,warning,error
full => notice,warning,error,debug,verbose,dtmf
console => notice,warning,error
```

Inside the Asterisk CLI, reload the logger:

```
asterisk*CLI> logger reload
```

## 6. Clone Smarthome Scripts

Clone the smarthome scripts to the server:

```bash
cd /opt/smarthome
git clone https://github.com/Michdo93/asterisk-smarthome .
sudo chown -R asterisk:asterisk /opt/smarthome
```

## 7. Python Environment & Dependencies

It is recommended to install the Python dependencies system-widely because Asterisk has to run it with admin-rights.

```bash
sudo pip install openai-whisper --break-system-packages
sudo pip install requests --break-system-packages
sudo pip install feedparser --break-system-packages
sudo pip install google-auth-oauthlib google-auth-httplib2 google-api-python-client --break-system-packages
```

## 8. Credentials

`calendar.py` is used to read appointments from your Google Calendar. To do this, you need OAuth 2.0 credentials from the [Google Cloud Console](https://console.cloud.google.com), saved as `credentials.json` in `/opt/smarthome`, and a one-time login to generate `token.json`.

### 8.1 Create a Google Cloud project

1. Open the [Google Cloud Console](https://console.cloud.google.com).
2. Click the project selector at the top and choose **New Project**.
3. Give it a name (e.g. `asterisk-smarthome`) and click **Create**.
4. Make sure the new project is selected in the project selector.

### 8.2 Enable the Google Calendar API

1. In the left sidebar, go to **APIs & Services → Library**.
2. Search for **Google Calendar API**.
3. Click on it, then click **Enable**.

### 8.3 Configure the OAuth consent screen

1. Go to **APIs & Services → OAuth consent screen**.
2. Choose **External** (unless you have a Google Workspace organization, then **Internal** is fine) and click **Create**.
3. Fill in the required fields (app name, your email as support contact and developer contact).
4. Under **Scopes**, add `.../auth/calendar.readonly` (or `.../auth/calendar` if write access is also needed).
5. Under **Test users**, add the Google account whose calendar you want to read.
6. Save and continue through the remaining steps.

> While the app is in "Testing" status, only the test users you added can log in. This is fine for a personal smarthome setup.

### 8.4 Create OAuth client credentials

1. Go to **APIs & Services → Credentials**.
2. Click **Create Credentials → OAuth client ID**.
3. Select **Desktop app** as the application type.
4. Give it a name (e.g. `smarthome-calendar`) and click **Create**.
5. A dialog shows your client ID and secret. Click **Download JSON**.

### 8.5 Place the credentials file on the server

Copy the downloaded JSON file to the smarthome directory and rename it to `credentials.json`:

```bash
scp client_secret_XXXXX.json <username>@<server-ip>:/tmp/credentials.json
ssh <username>@<server-ip>
sudo mv /tmp/credentials.json /opt/smarthome/credentials.json
sudo chown asterisk:asterisk /opt/smarthome/credentials.json
sudo chmod 600 /opt/smarthome/credentials.json
```

### 8.6 First login (generate token.json)

The first time `calendar.py` (or `calendar_auth.py`) runs, it must perform an interactive OAuth login to create `token.json`, which stores the access/refresh tokens for future use.

Since the Asterisk server typically has no browser, you can run the script on the Asterisk server and copy the URL on a machine **with a browser** (e.g. your laptop), it will create the resulting `token.json` on the server even if you use the Browser on another machine.


Run the authorization script:

```bash
cd /opt/smarthome
sudo -u asterisk python3 calendar_auth.py
```

This prints a URL (or opens it automatically in your browser). Open it, log in with the Google account added as a **test user** in step 8.3, and grant the requested calendar permission.

After granting access, the script writes a `token.json` file in the same folder.

### 8.7 Verify

Run `calendar.py` once manually as the `asterisk` user to confirm it can read calendar events without prompting for login again:

```bash
cd /opt/smarthome
sudo -u asterisk python3 calendar.py
```

If the token expires and Google requires re-consent, repeat steps 8.5–8.6 to refresh `token.json`.

> `credentials.json` and `token.json` contain sensitive secrets and are excluded via `.gitignore` (see section 11) — never commit them to the repository.

## 9. Resulting Directory Structure

```
/opt/smarthome
├── .git/
├── .gitignore
├── calendar.py
├── calendar_auth.py
├── credentials.json
├── de_DE-thorsten-medium.onnx
├── de_DE-thorsten-medium.onnx.json
├── news.py
├── piper/
├── stt.py
├── token.json
├── tts.py
└── weather.py
```

## 10. Customize the weather location

You can change the weather location by changing following lines in the `weather.py`. You have to run `sudo nano /opt/smarthome/weather.py`:

```
# ── Configuration weather location ──────────────────────────────────
LAT = 48.31
LON = 8.12
CITY = "Furtwangen im Schwarzwald"
```

You can get the longitude and latitude as example using Google maps.

## 11. Useful Verification Commands

```bash
# Check Asterisk service status
sudo systemctl status asterisk

# Check active swap/zram
swapon --show

# Check Git status
cd /opt/smarthome && git status
```
