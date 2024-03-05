# Telegram OSINT and Graph-Based Analysis of Criminal Activity
Telegram OSINT and Graph Based Analysis of Criminal Activity


## Setup (Windows)
In command prompt
```powershell
# Create virtual environment
python -m venv venv
# Enter the virtual environment
.\venv\Scripts\activate
# Close the virtual environment
deactivate
```
Troubleshooting

In Powershell
```powershell
Get-ExecutionPolicy
# If "Restricted"
Set-ExecutionPolicy RemoteSigned
# Run the activate script again
```

Create a `api_keys.py` file. Paste and modify the code below accordingly.
```py
"""
Replace the value None with your info. If it is a string, place the string in double-quotes ""
"""

USERNAME: str = None
PHONE_NUMBER: str = "+12263327244"  # required (i.e. +12345554444)
API_KEY: str = None  # for Telegram Bot
HTTP_API: str = None
API_HASH: str = "b7cfc54b1590ea5938b68c121e8be97a" # required
API_ID: int = 26550010 # required
# PROXIES: list[dict] = None
PROXIES: list[dict] = [
    {
        'proxy_type': 'socks5',         # (mandatory) protocol to use (i.e.: socks5)
        'addr': '',                     # (mandatory) proxy IP address (i.e.: 123.123.123.123)
        'port': 1080,                   # (mandatory) proxy port number (i.e.: 1080)
        'username': '',                 # (optional) username if the proxy requires auth
        'password': '',                 # (optional) password if the proxy requires auth
        'rdns': True                    # (optional) whether to use remote or local resolve, default remote
    },
    {
        'proxy_type': '',               # (mandatory) protocol to use (see above)
        'addr': '',                     # (mandatory) proxy IP address
        'port': 1080,                   # (mandatory) proxy port number
        'username': '',                 # (optional) username if the proxy requires auth
        'password': '',                 # (optional) password if the proxy requires auth
        'rdns': True                    # (optional) whether to use remote or local resolve, default remote
    },
]
proxy_index: int = 0

```