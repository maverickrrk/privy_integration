import json
import os
from typing import Dict, Any, Optional, List
import logging

logger = logging.getLogger(__name__)

class SimpleDatabase:
    """Simple JSON-based database for storing user and wallet information"""
    
    def __init__(self, db_file: str = "database.json"):
        self.db_file = db_file
        self.data = self._load_data()
    
    def _load_data(self) -> Dict[str, Any]:
        """Load data from JSON file"""
        if os.path.exists(self.db_file):
            try:
                with open(self.db_file, 'r') as f:
                    return json.load(f)
            except Exception as e:
                logger.error(f"Failed to load database: {e}")
                return {"users": {}, "wallets": {}}
        else:
            return {"users": {}, "wallets": {}}
    
    def _save_data(self):
        """Save data to JSON file"""
        try:
            with open(self.db_file, 'w') as f:
                json.dump(self.data, f, indent=2)
        except Exception as e:
            logger.error(f"Failed to save database: {e}")
            raise
    
    def create_user(self, user_id: str, email: Optional[str] = None) -> Dict[str, Any]:
        """Create a new user"""
        if user_id in self.data["users"]:
            raise ValueError(f"User {user_id} already exists")
        
        user_data = {
            "user_id": user_id,
            "email": email,
            "wallets": [],
            "created_at": None  # You could add timestamp here
        }
        
        self.data["users"][user_id] = user_data
        self._save_data()
        
        logger.info(f"Created user {user_id}")
        return user_data
    
    def get_user(self, user_id: str) -> Optional[Dict[str, Any]]:
        """Get user by ID"""
        return self.data["users"].get(user_id)
    
    def add_wallet_to_user(self, user_id: str, wallet_data: Dict[str, Any]):
        """Add a wallet to a user"""
        if user_id not in self.data["users"]:
            raise ValueError(f"User {user_id} not found")
        
        wallet_id = wallet_data["wallet_id"]
        
        # Store wallet data
        self.data["wallets"][wallet_id] = wallet_data
        
        # Add wallet to user's wallet list
        if wallet_id not in self.data["users"][user_id]["wallets"]:
            self.data["users"][user_id]["wallets"].append(wallet_id)
        
        self._save_data()
        logger.info(f"Added wallet {wallet_id} to user {user_id}")
    
    def get_user_wallets(self, user_id: str) -> List[Dict[str, Any]]:
        """Get all wallets for a user"""
        user = self.get_user(user_id)
        if not user:
            return []
        
        wallets = []
        for wallet_id in user["wallets"]:
            wallet_data = self.data["wallets"].get(wallet_id)
            if wallet_data:
                wallets.append(wallet_data)
        
        return wallets
    
    def get_wallet(self, wallet_id: str) -> Optional[Dict[str, Any]]:
        """Get wallet by ID"""
        return self.data["wallets"].get(wallet_id)
    
    def get_wallet_by_address(self, address: str) -> Optional[Dict[str, Any]]:
        """Get wallet by address"""
        for wallet_data in self.data["wallets"].values():
            if wallet_data.get("address") == address:
                return wallet_data
        return None
    
    def list_all_users(self) -> List[Dict[str, Any]]:
        """List all users"""
        return list(self.data["users"].values())
    
    def list_all_wallets(self) -> List[Dict[str, Any]]:
        """List all wallets"""
        return list(self.data["wallets"].values())
    
    def delete_user(self, user_id: str) -> bool:
        """Delete a user and their wallets"""
        if user_id not in self.data["users"]:
            return False
        
        # Delete user's wallets
        user_wallets = self.data["users"][user_id]["wallets"]
        for wallet_id in user_wallets:
            if wallet_id in self.data["wallets"]:
                del self.data["wallets"][wallet_id]
        
        # Delete user
        del self.data["users"][user_id]
        self._save_data()
        
        logger.info(f"Deleted user {user_id} and their wallets")
        return True

# Global database instance
db = SimpleDatabase()
