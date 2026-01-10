import google.generativeai as genai
import os
from dotenv import load_dotenv

load_dotenv()
api_key = os.getenv('GEMINI_API_KEY')

if not api_key:
    print("Error: API Key not found!")
    exit(1)

print(f"API Key found: {api_key[:5]}...")

genai.configure(api_key=api_key)

# 2. 모델 초기화 테스트
print("\n[Test] Initializing Model...")
try:
    model = genai.GenerativeModel('gemini-3-flash-preview')
    print("Model initialized successfully!")
except Exception as e:
    print(f"Model initialization failed: {e}")
    exit(1)

# 3. 생성 테스트
print("\n[Test] Generative Content...")
try:
    response = model.generate_content("Hello, can you hear me? Answer in 1 short sentence.")
    print(f"Response: {response.text}")
except Exception as e:
    print(f"Generation failed: {e}")
