import requests

TOKEN = "7536020028:AAGCmOyTd6zyusyUxsH98nuoLeKAdCATo2o"
url = f"https://api.telegram.org/bot{TOKEN}/getMe"

response = requests.get(url).json()
print(response)
