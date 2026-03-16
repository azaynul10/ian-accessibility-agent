import sys
sys.stdout.reconfigure(line_buffering=True)
import asyncio, websockets, json, base64

async def run_test():
    uri = 'ws://127.0.0.1:8082/ag-ui'
    try:
        print('[CLIENT] Connecting to', uri)
        async with websockets.connect(uri) as ws:
            print('[CLIENT] Connected!')
            await ws.send(json.dumps({'type': 'StartSpeaking'}))
            print('[CLIENT] Sent StartSpeaking')
            
            # Send small buffer of mock static to prevent silent threshold drops
            b64_audio = base64.b64encode(b'\x01\x00' * 16000).decode('utf-8')
            for _ in range(3):
                await ws.send(json.dumps({'type': 'AudioChunk', 'data': {'base64Audio': b64_audio}}))
                await asyncio.sleep(0.5)
            print('[CLIENT] Sent AudioChunks')
            
            await ws.send(json.dumps({'type': 'EndOfAudio'}))
            print('[CLIENT] Sent EndOfAudio. Waiting for response...')
            
            for _ in range(5):
                resp = await asyncio.wait_for(ws.recv(), timeout=5.0)
                print('[CLIENT] Got:', resp)
                
    except Exception as e:
        print('[CLIENT] Error:', e)

asyncio.run(run_test())
