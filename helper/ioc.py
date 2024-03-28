"""
Used for all things related to the analysis and extraction of Indicators of Compromise (IOCs)
from scraped Telegram messages.
"""

import re
from enum import Enum


class IOC(Enum):
    """
    Supported Indicators of Compromise (IOCs) types.

    Each value is a tuple represented as ("IOC Name", "Regex pattern for IOC").

    Examples:
    ```
    IPV4 = ("IPv4", r"\b(?:\d{1,3}\.){3}\d{1,3}\b")
    print(IOC.IPV4.value[0])  # Output: IPv4
    print(IOC.IPV4.value[1])  # Output: \b(?:\d{1,3}\.){3}\d{1,3}\b

    text = "3ca25ae354e192b26879f651a51d92aa8a34d8d3ca25ae354e192b26879f651a"
    print(re.match(IOC.HASH_SHA256.value[1], text))  # Output: True
    ```
    """

    IPV4 = ("IPv4", r"(?:\d{1,3}\.){3}\d{1,3}")
    IPV6 = ("IPv6", r"(?:[0-9a-fA-F]{1,4}:){7}[0-9a-fA-F]{1,4}")
    URL = ("URL", r"https?://(?:[-\w.]|(?:%[\da-fA-F]{2}))+")
    DOMAIN = ( "Domain", r"\b(?:[a-zA-Z0-9](?:[a-zA-Z0-9-]{0,61}[a-zA-Z0-9])?\.)+[a-zA-Z]{2,}\b")
    HASH_SHA1 = ("SHA1", r"\b[0-9a-f]{40}\b")
    HASH_SHA256 = ("SHA256", r"\b[0-9a-f]{64}\b")
    HASH_MD5 = ("MD5", r"\b[0-9a-f]{32}\b")
    CVE = ("CVE", r"CVE-\d{4}-\d+\b", re.IGNORECASE)
    EMAIL = ("Email", r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b")
    CRYPTO_BITCOIN = ("Bitcoin", r"\b[13][a-km-zA-HJ-NP-Z1-9]{25,34}\b")
    CRYPTO_DOGECOIN = ("Dogecoin", r"\bD{1}[5-9A-HJ-NP-U]{1}[1-9A-HJ-NP-Za-km-z]{32}\b")
    CRYPTO_ETHEREUM = ("Ethereum", r"\b0x[a-fA-F0-9]{40}\b")
    CRYPTO_MONERO = ("Monero", r"\b[48][123456789ABCDEFGHJKLMNPQRSTUVWXYZabcdefghijkmnopqrstuvwxyz]{94}\b")


def find_iocs(text: str) -> list[tuple[str]]:
    """
    Finds IOC(s) within a given string of text.

    Takes a string as input and returns all IOCs that are found in the string
    as well as the exact substrings that match the IOCs' Regex patterns.

    Examples:
    ```
    Input: "Hey guys, I have an RDP session on IP 2.3.4.5. Anyone interested?"
    Output: [("IPv4", "2.3.4.5")]

    Input: "I want to attack 2.3.4.5 with CVE-2024-21410. Willing to pay."
    Output: [("IPv4", "2.3.4.5"), ("CVE", "CVE-2024-21410")]
    ```

    Args:
        text: the input string

    Returns:
        A list containing tuples of IOCs found in the original string.
    """
    ioc_list: list = []
    for ioc_type in IOC:
        matches = re.findall(
            ioc_type.value[1],
            text,
            flags=ioc_type.value[2] if len(ioc_type.value) > 2 else 0,
        )
        ioc_list.extend((ioc_type.value[0], match) for match in matches)
    return ioc_list


if __name__ == "__main__":
    # Print Regex pattern of IPv4
    print(IOC.IPV4.value[1])
    print("---------------------------------------------------------------------")

    # Verify that a given string is a valid SHA256 hash
    text = "3ca25ae354e192b26879f651a51d92aa8a34d8d3ca25ae354e192b26879f651a"
    if re.match(IOC.HASH_SHA256.value[1], text):
        print("Valid SHA256 hash")
    print("---------------------------------------------------------------------")

    # Find IOCs
    input1 = "Hey guys, I have an RDP session on IP 2.3.4.5. Anyone interested?"
    print(find_iocs(input1))
    print("---------------------------------------------------------------------")

    input2 = "I want to attack 2.3.4.5 withcvE-2024-21410. Willing to pay."
    print(find_iocs(input2))
    print("---------------------------------------------------------------------")

    input3 = "Hi everyone. How's a going?"
    print(find_iocs(input3))
    print("---------------------------------------------------------------------")

    input4 = (
        "Я обнаружил, что компания X не исправила CVE-2024-21410 на своих серверах."
    )
    print(find_iocs(input4))
    print("---------------------------------------------------------------------")

    input5 = (
        "I want to DDos uottawa.ca. Any tips? I also want to use "
        + "00236a2ae558018ed13b5222ef1bd987 "  # MD5
        + "10886660c5b2746ff48224646c5094ebcf88c889 "  # SHA1
        + "3ca25ae354e192b26879f651a51d92aa8a34d8d3ca25ae354e192b26879f651a "  # SHA256
        + "on https://www.realmadrid.com/en-US, http://www.example.co.uk and 3.4.5.6. "
        + "Yesterday, I talked about my day.And be honest, it was great. "
        + "My IPv6 is 2001:0db8:85a3:0000:0000:8a2e:0370:7334. "
        + "I like going to cbc.ca to watch the news."
    )
    print(find_iocs(input5))
    print("---------------------------------------------------------------------")

    input6 = "Proxy IP Proxy Port Last Check Proxy Speed Proxy Country Anonymity 118.99.81.204118.99.81.204 8080 34 sec Indonesia - Tangerang Transparent 2.184.31.2 8080 58 sec Iran Transparent 93.126.11.189 8080 1 min Iran - Esfahan Transparent 202.118.236.130 7777 1 min China - Harbin Transparent 62.201.207.9 8080 1 min Iraq Transparent 219.143.244.170 8899 1 min China - Beijing Transparent 66.63.235.97 8080 1 min United States - Somerville Transparent 27.191.194.106 8080 1 min China Transparent 200.195.141.178 8080 2 min Brazil Transparent 210.101.131.232 8080 2 min South Korea - Seoul Transparent 218.75.205.44 9999 2 min China - Changsha Transparent212.119.97.198 3128 2 min Russia - Moscow Transparent 10.48.0.200 Your public IP address is 46.130.14.41 - Learn more"
    print(find_iocs(input6))
    print("---------------------------------------------------------------------")

    input7 = "Pay me 0.1 bitcoin here 1A1zP1eP5QGefi2DMPTfTL5SLmv7DivfNa 1BvBMSEYstWetqTFn5Au4m4GFg7xJaNVN2 3FZbgi29cpjq2GjdwV8eyHuJJnkLtktZc5"  # bitcoin
    input7 += "\nOr dogecoin DLCDJhnh6aGotar6b182jpzbNEyXb3C361"  # dogecoin
    input7 += "\nOr ethereum 0x742d35Cc6634C0532925a3b844Bc454e4438f44e"  # ethereum
    input7 += "\nOr monero 888tNkZrPN6JsEgekjMnABU4TBzc2Dt29EPAvkRxbANsAnjyPbb3iQ1YBRk1UXcdRsiKc9dhwMVgN5S9cQUiyoogDavup3H 4AfUP827TeRZ1cck3tZThgZbRCEwBrpcJTkA1LCiyFVuMH4b5y59bKMZHGb9y58K3gSjWDCBsB4RkGsGDhsmMG5R2qmbLeW"  # monero
    print(find_iocs(input7))
