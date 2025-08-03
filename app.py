#!/usr/bin/env python3
"""
Main entry point for Privy-Hyperliquid Trading Platform
"""

import sys
import os

# Add src to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from src.api.main import app

if __name__ == "__main__":
    import uvicorn
    from src.core.config import Config
    
    uvicorn.run(
        "app:app", 
        host=Config.API_HOST, 
        port=Config.API_PORT, 
        reload=Config.DEBUG
    )
