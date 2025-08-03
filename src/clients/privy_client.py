from typing import Dict, Any, Optional
import logging
from privy import PrivyAPI
from privy_eth_account import PrivyHTTPClient, create_eth_account
from ..core.config import Config

logger = logging.getLogger(__name__)

class PrivyWalletManager:
    """Manages Privy server-side wallets for users"""
    
    def __init__(self):
        """Initialize Privy client"""
        Config.validate()
        
        # Initialize Privy API client
        self.privy_api = PrivyAPI(
            app_id=Config.PRIVY_APP_ID,
            app_secret=Config.PRIVY_APP_SECRET
        )
        
        # Initialize HTTP client for eth-account integration
        self.http_client = PrivyHTTPClient(
            app_id=Config.PRIVY_APP_ID,
            app_secret=Config.PRIVY_APP_SECRET,
            authorization_key=Config.PRIVY_AUTHORIZATION_KEY
        )
        
        logger.info("Privy wallet manager initialized")
    
    def create_user_wallet(self, user_id: str) -> Dict[str, Any]:
        """Create a new Ethereum wallet for a user"""
        try:
            # Create wallet using Privy API
            wallet = self.privy_api.wallets.create(
                chain_type="ethereum"
            )
            
            logger.info(f"Created wallet {wallet.id} for user {user_id}")
            
            return {
                "wallet_id": wallet.id,
                "address": wallet.address,
                "chain_type": wallet.chain_type,
                "user_id": user_id
            }
            
        except Exception as e:
            logger.error(f"Failed to create wallet for user {user_id}: {str(e)}")
            raise
    
    def get_wallet_balance(self, wallet_id: str, wallet_address: str) -> Dict[str, Any]:
        """Get wallet balance (this would typically query the blockchain)"""
        try:
            # Create eth account for balance queries
            account = create_eth_account(
                self.http_client, 
                wallet_address, 
                wallet_id
            )
            
            # Note: In a real implementation, you'd query the blockchain for balance
            # For now, we'll return a placeholder
            return {
                "wallet_id": wallet_id,
                "address": wallet_address,
                "balance": "0.0",  # This should be fetched from blockchain
                "currency": "ETH"
            }
            
        except Exception as e:
            logger.error(f"Failed to get balance for wallet {wallet_id}: {str(e)}")
            raise
    
    def sign_message(self, wallet_id: str, message: str) -> Dict[str, Any]:
        """Sign a message with the specified wallet"""
        try:
            result = self.privy_api.wallets.rpc(
                wallet_id=wallet_id,
                method="personal_sign",
                caip2="eip155:1",
                params={
                    "message": message,
                    "encoding": "utf-8"
                }
            )
            
            logger.info(f"Message signed with wallet {wallet_id}")
            return result
            
        except Exception as e:
            logger.error(f"Failed to sign message with wallet {wallet_id}: {str(e)}")
            raise
    
    def send_transaction(self, wallet_id: str, to_address: str, value: int, chain_id: str = "eip155:1") -> Dict[str, Any]:
        """Send a transaction from the specified wallet"""
        try:
            result = self.privy_api.wallets.rpc(
                wallet_id=wallet_id,
                method="eth_sendTransaction",
                caip2=chain_id,
                params={
                    "transaction": {
                        "to": to_address,
                        "value": value,
                    }
                }
            )
            
            logger.info(f"Transaction sent from wallet {wallet_id} to {to_address}")
            return result
            
        except Exception as e:
            logger.error(f"Failed to send transaction from wallet {wallet_id}: {str(e)}")
            raise
    
    def create_eth_account(self, wallet_address: str, wallet_id: str):
        """Create an eth-account instance for Hyperliquid integration"""
        try:
            account = create_eth_account(
                self.http_client,
                wallet_address,
                wallet_id
            )
            
            logger.info(f"Created eth-account for wallet {wallet_id}")
            return account
            
        except Exception as e:
            logger.error(f"Failed to create eth-account for wallet {wallet_id}: {str(e)}")
            raise
