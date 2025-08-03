import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

class Config:
    # Privy Configuration
    PRIVY_APP_ID = os.getenv("PRIVY_APP_ID")
    PRIVY_APP_SECRET = os.getenv("PRIVY_APP_SECRET")
    PRIVY_AUTHORIZATION_KEY = os.getenv("PRIVY_AUTHORIZATION_KEY")
    
    # Hyperliquid Configuration
    HYPERLIQUID_BASE_URL = os.getenv("HYPERLIQUID_BASE_URL", "https://api.hyperliquid.xyz")
    HYPERLIQUID_TESTNET_URL = os.getenv("HYPERLIQUID_TESTNET_URL", "https://api.hyperliquid-testnet.xyz")
    
    # Application Configuration
    API_HOST = os.getenv("API_HOST", "0.0.0.0")
    API_PORT = int(os.getenv("API_PORT", 8000))
    DEBUG = os.getenv("DEBUG", "True").lower() == "true"
    
    @classmethod
    def validate(cls):
        """Validate that all required configuration is present"""
        required_fields = [
            "PRIVY_APP_ID",
            "PRIVY_APP_SECRET", 
            "PRIVY_AUTHORIZATION_KEY"
        ]
        
        missing_fields = []
        for field in required_fields:
            if not getattr(cls, field):
                missing_fields.append(field)
        
        if missing_fields:
            raise ValueError(f"Missing required configuration: {', '.join(missing_fields)}")
        
        return True
