import sys
sys.stdout.reconfigure(line_buffering=True)
sys.stderr.reconfigure(line_buffering=True)
print('[BOOT] Unbuffered server starting...')

import uvicorn
from main import app

if __name__ == '__main__':
    uvicorn.run(app, host='127.0.0.1', port=8082)
