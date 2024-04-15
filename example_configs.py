"""
Example configs.py file with all configurations enabled and filled in with dummy values.
"""

# Telegram collection configs
PHONE_NUMBER: str = "+12223334444"
API_HASH: str = "e73b1b3f59542462493182f96ee4bb1c"  # Randomly generated MD5 hash for this example
API_ID: int = 12345678

# Proxy configs (3 proxies configured)
PROXIES: list[dict] = [
    {
        "proxy_type": "socks5",
        "addr": "123.123.123.123",
        "port": 1080,
        "username": "user",
        "password": "whatintheworld",
        "rdns": True,
    },
    {
        "proxy_type": "socks5",
        "addr": "123.123.123.124",
        "port": 1080,
        "username": "user",
        "password": "whatintheworld",
        "rdns": True,
    },
    {
        "proxy_type": "socks5",
        "addr": "123.123.123.125",
        "port": 1080,
        "username": "user",
        "password": "whatintheworld",
        "rdns": True,
    },
]

# Elastic configs (local Elasticsearch Windows installation)
es_username: str = "elastic"
es_password: str = "XDcF4HwKsD"
es_ca_cert_path: str = "C:\Elasticsearch\elasticsearch-8.12.2\config\certs\http_ca.crt"
