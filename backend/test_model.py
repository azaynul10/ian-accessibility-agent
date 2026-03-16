import os, asyncio
from dotenv import load_dotenv
load_dotenv()
from google import genai
from google.genai import types

async def test_live():
    api_key = os.environ.get('GEMINI_API_KEY')
    print('Testing with API KEY:', api_key[:10] + '...')
    client = genai.Client(api_key=api_key)
    models_to_test = ['gemini-2.0-flash-exp', 'gemini-2.5-flash', 'gemini-2.5-flash-native-audio-preview-12-2025']
    for m in models_to_test:
        try:
            print(f'Testing {m}...')
            async with client.aio.live.connect(model=m) as session:
                print(f'{m} SUCCESS')
        except Exception as e:
            print(f'{m} FAILED: {e}')

if __name__ == '__main__':
    asyncio.run(test_live())
