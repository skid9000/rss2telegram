# RSS2Telegram

A self-hosted telegram python3 bot that dumps posts from RSS feeds to a telegram chat. This script was created because all the third party services were unreliable.

This project is based/forked from [BoKKeR](https://github.com/BoKKeR) work at https://github.com/BoKKeR/RSS-to-Telegram-Bot

### Installation.

You need Python3 (and pip) and SQLite3 support.

If you are using Debian for exemple :

```bash
apt install python3 python3-pip sqlite3 libsqlite3-0
```

When you have a working python environement all you have to do is :

```bash
mkdir -p /opt ; cd /opt
git clone https://github.com/skid9000/rss2telegram.git
cd rss2telegram
pip3 install -r requirements.txt
```

Then copy config.py.sample to config.py and edit properties.

```bash
cp config.py.sample config.py
$EDITOR config.py
```

After that, you can run :

```bash
python3 rss2telegram.py
```

If you want to make a systemd unit :

```bash
echo '[Unit]
Description=RSS2Telegram Bot
After=network.target

[Service]
Type=simple
ExecStart=/usr/bin/python3 rss2telegram.py
WorkingDirectory=/opt/rss2telegram
Restart=always

[Install]
WantedBy=multi-user.target' > /etc/systemd/system/rss2telegram.service
systemctl enable rss2telegram ; systemctl start rss2telegram
```