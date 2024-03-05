# Telegram OSINT and Graph-Based Analysis of Criminal Activity
Telegram OSINT and Graph Based Analysis of Criminal Activity


## Setup
<!-- In command prompt
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
``` -->
- Install git and Python *version 3.11 or lower*.
- Create virtual environment
    - `python -m venv venv`
- Activate venv
    - `source venv/Scripts/activate  # Windows git bash`
    - `source venv/bin/activate  # UNIX` 
- Deactivate venv
    - `deactivate`


Create a `credentials.py` file. Paste and modify the code below accordingly.
```py
"""
Replace the value None with your info. If it is a string, place the string in double-quotes ""
"""

USERNAME: str = None
PHONE_NUMBER: str = "+12263327244"     # (mandatory) (i.e. +12345554444)
API_KEY: str = None                    # (optional) for Telegram Bot
HTTP_API: str = None
API_HASH: str = "<replace>"            # (mandatory)
API_ID: int = <replace>                # (mandatory)

# Proxy configurations (optional)
PROXIES: list[dict] = None             # (optional) default None for no proxy
# Add a proxy object to the list for each new proxy. Example below is of two proxies
# PROXIES: list[dict] = [
#     {
#         'proxy_type': 'socks5',         # (mandatory) protocol to use (i.e.: socks5)
#         'addr': '',                     # (mandatory) proxy IP address (i.e.: 123.123.123.123)
#         'port': 1080,                   # (mandatory) proxy port number (i.e.: 1080)
#         'username': '',                 # (optional) username if the proxy requires auth
#         'password': '',                 # (optional) password if the proxy requires auth
#         'rdns': True                    # (optional) whether to use remote or local resolve, default remote
#     },
#     {
#         'proxy_type': '',               # (mandatory) protocol to use (see above)
#         'addr': '',                     # (mandatory) proxy IP address
#         'port': 1080,                   # (mandatory) proxy port number
#         'username': '',                 # (optional) username if the proxy requires auth
#         'password': '',                 # (optional) password if the proxy requires auth
#         'rdns': True                    # (optional) whether to use remote or local resolve, default remote
#     },
# ]

```