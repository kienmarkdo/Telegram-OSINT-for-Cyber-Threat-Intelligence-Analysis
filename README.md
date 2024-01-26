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
USERNAME: str = None      # Optional
PHONE_NUMBER: str = None  # Optional: "+12345554444"
API_KEY: str = None       # Optional (for Telegram Bot)
HTTP_API: str = None      # Optional
API_HASH: str = None      # Required
API_ID: int = None        # Required
```