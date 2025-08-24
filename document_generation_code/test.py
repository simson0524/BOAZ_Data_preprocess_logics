from google import genai

client = genai.Client(api_key="AIzaSyD1mYaY5DesUV-g")
resp = client.models.generate_content(
    model="gemini-2.5-pro",
    contents="테스트"
)
print(resp.text)
