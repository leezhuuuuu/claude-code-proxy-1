import httpx

headers = {
    "Authorization": "Bearer Qq818308046"
}

response = httpx.post(
    "http://localhost:8082/v1/messages",
    headers=headers,
    json={
        "model": "claude-3-5-sonnet-20241022",  # Maps to MIDDLE_MODEL
        "max_tokens": 100,
        "messages": [
            {"role": "user", "content": "Hello!"}
        ]
    },
    timeout=60.0,
)

print(response.status_code)
print(response.text)