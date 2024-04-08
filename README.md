# Welcome!
To view more information about the project, visit the [Wiki](https://github.com/kienmarkdo/Telegram-OSINT-for-Cyber-Threat-Intelligence-Analysis/wiki)!


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
- Download library dependencies
    - `pip install -r requirements.txt`
    - Optional: Download individual dependencies
        - `pip install telethon`
        - `pip install argostranslate`
        - `pip install lingua-language-detector`
        - `pip install requests`
        - `pip install elasticsearch`
        - `pip install ijson`

Create a `configs.py` file. Paste and modify the code below accordingly.
```py
"""
Replace mandatory None values with your info. Ensure correct data types, as specified.
For optional values, replace them with your info as needed. Otherwise, keep values as None.

Configurations:
- Basic configurations           (REQUIRED)
- Collection configurations      (OPTIONAL)
- Elasticsearch configurations   (OPTIONAL)
"""
########################
# Basic configurations #
########################
PHONE_NUMBER: str = None               # (mandatory) (i.e. +12223334444)
API_HASH: str = None                   # (mandatory)
API_ID: int = None                     # (mandatory)

#############################
# Collection configurations #
#############################

# Proxy configuration
PROXIES: list[dict] = None             # (mandatory) default None for no proxy
# Add a each proxy object to the list. Below is an example template for two proxies.
# PROXIES: list[dict] = [
#     {
#         'proxy_type': 'socks5',        # (mandatory) protocol to use (i.e.: socks5)
#         'addr': '',                    # (mandatory) proxy IP address (i.e.: 123.123.123.123)
#         'port': 1080,                  # (mandatory) proxy port number (i.e.: 1080)
#         'username': '',                # (optional) username if the proxy requires auth
#         'password': '',                # (optional) password if the proxy requires auth
#         'rdns': True                   # (optional) whether to use remote or local resolve, default remote
#     },
#     {
#         'proxy_type': '',              # (mandatory) protocol to use (see above)
#         'addr': '',                    # (mandatory) proxy IP address
#         'port': 1080,                  # (mandatory) proxy port number
#         'username': '',                # (optional) username if the proxy requires auth
#         'password': '',                # (optional) password if the proxy requires auth
#         'rdns': True                   # (optional) whether to use remote or local resolve, default remote
#     },
# ]  # uncomment to add proxies

################################
# Elasticsearch configurations #
################################
es_username: str = None                # (required) default None
es_password: str = None                # (required) default None
es_ca_cert_path: str = None            # (required) path to 'http_ca.crt' file stored in elasticsearch-<VERSION>/config/certs/http_ca.crt
```
