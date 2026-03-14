import requests

API_KEY = "YOUR_NOVA_API_KEY"

url = "https://api.amazon.com/nova/v1/generate"

# Writing samples used to teach TwinAI the style
writing_samples = """
Hi Sarah,

I'll send the file later today once I finish the last section.

Thanks!

---

Hi John,

I'm working on the final edits and will share the document this afternoon.

Thanks!
"""

# Message to respond to
message = "Can you send the final report today?"

# Prompt for Nova model
prompt = f"""
You are TwinAI, an AI digital twin.

Analyze the user's writing samples and generate a reply in the same tone and style.

Writing samples:
{writing_samples}

Message:
{message}

Generate a natural response in the user's style.
"""

headers = {
    "Authorization": f"Bearer {API_KEY}",
    "Content-Type": "application/json"
}

data = {
    "model": "nova-2-lite-v1",
    "prompt": prompt,
    "max_tokens": 200
}

response = requests.post(url, headers=headers, json=data)

print(response.text)
