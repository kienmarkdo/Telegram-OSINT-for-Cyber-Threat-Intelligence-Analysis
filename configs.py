"""
Replace the value None with your info. If it is a string, place the string in double-quotes ""

Note that all values below are constants and cannot be modified.
Any attempt to modify them will cause a runtime error.
"""
# Telegram collection configs (required)
PHONE_NUMBER: str = "+12263327244"  # "+12345554444"
API_HASH: str = "b7cfc54b1590ea5938b68c121e8be97a"
API_ID: int = 26550010

# Proxy configs (optional)
# PROXIES: list[dict] = None            # (optional) default None
PROXIES: list[dict] = [
    {
        'proxy_type': 'socks5',         # (mandatory) protocol to use (see above)
        'addr': '104.236.195.225',      # (mandatory) proxy IP address
        'port': 1080,                   # (mandatory) proxy port number
        'username': 'user',             # (optional) username if the proxy requires auth
        'password': 'whatintheworld',   # (optional) password if the proxy requires auth
        'rdns': True                    # (optional) whether to use remote or local resolve, default remote
    },
    {
        'proxy_type': 'socks5',         # (mandatory) protocol to use (see above)
        'addr': '167.71.189.116',       # (mandatory) proxy IP address
        'port': 1080,                   # (mandatory) proxy port number
        'username': 'user',             # (optional) username if the proxy requires auth
        'password': 'whatintheworld',   # (optional) password if the proxy requires auth
        'rdns': True                    # (optional) whether to use remote or local resolve, default remote
    },
    {
        'proxy_type': 'socks5',         # (mandatory) protocol to use (see above)
        'addr': '104.236.195.226',      # (mandatory) proxy IP address
        'port': 1080,                   # (mandatory) proxy port number
        'username': 'user',             # (optional) username if the proxy requires auth
        'password': 'whatintheworld',   # (optional) password if the proxy requires auth
        'rdns': True                    # (optional) whether to use remote or local resolve, default remote
    },
]

# Elasticsearch configs (optional)
es_username: str = "elastic"  # (required) default None
es_password: str = "Cy2=xVma=m8yI7s9LYSH"  # (required) default None
es_ca_cert_path: str = "C:\Elasticsearch\elasticsearch-8.12.2\config\certs\http_ca.crt"  # (required) path to 'http_ca.crt' file stored in elasticsearch-<VERSION>/config/certs/http_ca.crt