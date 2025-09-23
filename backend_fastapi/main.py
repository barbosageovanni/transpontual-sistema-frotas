#!/usr/bin/env python3
"""
Entry point for Railway deployment
"""
import os
from app.main import app

# For Railway deployment - let uvicorn handle the port via CLI args
# Railway sets PORT env var and we use it in CMD
if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)