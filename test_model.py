import requests
import json

headers = {
    'authorization': 'Bearer <YOUR_SECRET_KEY_HERE>',
    'Content-Type': 'application/json',
}

json_data = json.loads('''{
  "model": "deepseek-ai/deepseek-v4.1-flash",
  "temperature": 0.7,
  "top_p": 0.9,
  "stream": true,
  "max_tokens": 4096,
  "messages": []
}''')

response = requests.post('https://api.thehive.ai/api/v3/chat/completions', headers=headers, json=json_data)
print(response.text)