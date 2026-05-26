# Goliath - D2R Terror Zone & Diablo Clone Notifier

A Diablo 2 Resurrected desktop app that monitors Terror Zones and Diablo Clone progress, sending Discord notifications so you never miss a good farm session.

## Features

- Live Terror Zone tracking (current and next zone)
- Diablo Clone progress monitor (Ladder Softcore Europe)
- Discord webhook notifications
- Customisable watchlist of 35 zones
- Diablo-themed GUI dashboard
- System tray support
- Run on startup option
- Persistent settings

## Requirements

- Python 3.10+
- pip install requests pystray pillow

## Run

```
python goliath_gui.py
```

## Build exe

```
pyinstaller --onefile --windowed --icon=goliath.ico --name=Goliath goliath_gui.py
```

## Data Source

d2runewizard.com (public API)
