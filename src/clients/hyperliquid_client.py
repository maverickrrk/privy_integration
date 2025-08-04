from typing import Dict, Any, Optional, List
import logging
from hyperliquid.exchange import Exchange
from hyperliquid.info import Info
from ..core.config import Config
from .privy_client import PrivyWalletManager

logger = logging.getLogger(__name__)

class HyperliquidTrader:
    """Handles trading operations on Hyperliquid using Privy-managed wallets"""
    
    def __init__(self, use_testnet: bool = True):
        """Initialize Hyperliquid trader"""
        self.privy_manager = PrivyWalletManager()
        self.use_testnet = use_testnet
        
        # Set base URL based on testnet flag
        self.base_url = Config.HYPERLIQUID_TESTNET_URL if use_testnet else Config.HYPERLIQUID_BASE_URL
        
        # Log the URL being used for debugging
        logger.info(f"Using Hyperliquid API URL: {self.base_url}")
        
        # Initialize info client for market data with error handling
        try:
            self.info = Info(base_url=self.base_url, skip_ws=True)
            logger.info(f"Hyperliquid info client initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize Hyperliquid info client: {str(e)}")
            raise
        
        logger.info(f"Hyperliquid trader initialized (testnet: {use_testnet})")
    
    def create_exchange_client(self, wallet_address: str, wallet_id: str) -> Exchange:
        """Create an exchange client for a specific wallet"""
        try:
            from ..core.database import db
            from eth_account import Account
            
            # Get wallet data from database
            wallet_data = db.get_wallet(wallet_id)
            
            if wallet_data and wallet_data.get('compatible_with') == 'hyperliquid' and 'private_key' in wallet_data:
                # For Hyperliquid-compatible wallets, use the stored private key directly
                private_key = wallet_data['private_key']
                account = Account.from_key(private_key)
                logger.info(f"Using Hyperliquid-compatible wallet with direct private key for {wallet_id}")
            else:
                # For regular Privy wallets, use the Privy eth-account method
                account = self.privy_manager.create_eth_account(wallet_address, wallet_id)
                logger.info(f"Using Privy eth-account for wallet {wallet_id}")
            
            # Create exchange client
            exchange = Exchange(
                account, 
                base_url=self.base_url,
                account_address=wallet_address
            )
            
            logger.info(f"Created exchange client for wallet {wallet_id}")
            return exchange
            
        except Exception as e:
            logger.error(f"Failed to create exchange client for wallet {wallet_id}: {str(e)}")
            raise
    
    def get_user_state(self, wallet_address: str) -> Dict[str, Any]:
        """Get user's trading state on Hyperliquid"""
        try:
            user_state = self.info.user_state(wallet_address)
            logger.info(f"Retrieved user state for {wallet_address}")
            return user_state
            
        except Exception as e:
            logger.error(f"Failed to get user state for {wallet_address}: {str(e)}")
            raise
    
    def get_market_data(self, symbol: str) -> Dict[str, Any]:
        """Get market data for a trading pair"""
        try:
            # Get all mids (current prices)
            all_mids = self.info.all_mids()
            
            # Get meta info for the symbol
            meta = self.info.meta()
            
            # Find the symbol in the universe
            symbol_info = None
            for universe_item in meta.get("universe", []):
                if universe_item.get("name") == symbol:
                    symbol_info = universe_item
                    break
            
            if not symbol_info:
                raise ValueError(f"Symbol {symbol} not found")
            
            # Get current price
            current_price = all_mids.get(symbol, "0")
            
            return {
                "symbol": symbol,
                "current_price": current_price,
                "symbol_info": symbol_info
            }
            
        except Exception as e:
            logger.error(f"Failed to get market data for {symbol}: {str(e)}")
            raise
    
    def place_order(self, wallet_address: str, wallet_id: str, symbol: str, 
                   is_buy: bool, size: float, price: float, 
                   order_type: str = "limit", market_type: str = "perp") -> Dict[str, Any]:
        """Place a trading order"""
        try:
            # Debug: print the symbol requested
            logger.info(f"Requested to place order for symbol: {symbol}")
            
            # Get asset ID based on market type (spot vs perp)
            if market_type == "spot":
                # For spot trading, get spotMeta and calculate asset ID as 10000 + spot_index
                logger.info(f"Fetching spot metadata from Hyperliquid API: {self.base_url}")
                try:
                    spot_meta = self.info.spot_meta()
                    logger.info(f"Successfully fetched spot metadata")
                    spot_tokens = spot_meta.get("tokens", [])
                    logger.info(f"Found {len(spot_tokens)} spot tokens")
                except Exception as e:
                    logger.error(f"Failed to fetch spot metadata from {self.base_url}: {str(e)}")
                    logger.error(f"Error type: {type(e).__name__}")
                    # Return a more descriptive error
                    return {
                        "success": False, 
                        "error": f"Failed to connect to Hyperliquid testnet API ({self.base_url}). Error: {str(e)}"
                    }
                
                # Find the spot index for the symbol
                spot_index = None
                for i, token in enumerate(spot_tokens):
                    if token.get("name") == symbol:
                        spot_index = i
                        break
                
                if spot_index is None:
                    logger.error(f"Spot symbol {symbol} not found in spot tokens.")
                    available_spot_symbols = [token.get("name") for token in spot_tokens]
                    raise ValueError(f"Spot symbol {symbol} not found. Available spot symbols: {available_spot_symbols}")
                
                # Calculate correct spot asset ID: 10000 + spot_index
                asset_id = 10000 + spot_index
                logger.info(f"Using spot asset ID {asset_id} for symbol {symbol} (spot_index={spot_index})")
                
            else:
                # For perpetual trading, use the standard meta universe index
                meta = self.info.meta()
                available_symbols = [item["name"] for item in meta.get("universe", [])]
                logger.info(f"Available perp symbols: {available_symbols}")
                
                # Check if symbol is available
                if symbol not in available_symbols:
                    logger.error(f"Perp symbol {symbol} not found in available symbols.")
                    raise ValueError(f"Perp symbol {symbol} not found. Available symbols: {available_symbols}")
                
                # Find the perpetual asset index
                asset_id = None
                for i, item in enumerate(meta.get("universe", [])):
                    if item["name"] == symbol:
                        asset_id = i
                        break
                
                logger.info(f"Using perp asset ID {asset_id} for symbol {symbol}")

            # Create exchange client for this wallet
            exchange = self.create_exchange_client(wallet_address, wallet_id)
            
            # Log the asset ID being used
            logger.info(f"Final asset ID for {symbol} ({market_type}): {asset_id}")
            
            # Prepare order parameters
            if market_type == "spot":
                # Spot trading only supports limit orders on Hyperliquid
                # Force limit order for spot trading regardless of requested order type
                order_params = {"limit": {"tif": "Gtc"}, "marketType": "spot"}
                if order_type == "market":
                    logger.info(f"Converting market order to limit order for spot trading")
                    # For market orders, we'll use current market price
                    # Get current market price for the symbol
                    try:
                        market_data = self.get_market_data(symbol)
                        current_price = float(market_data.get('current_price', price))
                        # Add small buffer for market-like execution
                        if is_buy:
                            price = current_price * 1.01  # Buy slightly above market
                        else:
                            price = current_price * 0.99  # Sell slightly below market
                        logger.info(f"Using adjusted price {price} for market-like execution")
                    except Exception as e:
                        logger.warning(f"Could not get market price, using provided price: {e}")
                else:
                    # For limit orders, use the exact price provided by user
                    logger.info(f"Using user-provided limit price: {price}")
                    # Don't modify the price for limit orders
            else:
                # For perp trading, both limit and market orders are supported
                if order_type == "limit":
                    order_params = {"limit": {"tif": "Gtc"}}
                else:
                    order_params = {"market": {}}
            
            # Place the order with correct asset ID
            try:
                # For spot trading, use direct API call to ensure correct asset ID
                if market_type == "spot":
                    logger.info(f"Placing spot order with calculated asset ID {asset_id} for symbol {symbol}")
                    
                    # Use direct API call with our calculated spot asset ID
                    # Based on official Hyperliquid API documentation
                    import time
                    from hyperliquid.utils.signing import sign_l1_action
                    
                    # Build order request with correct spot asset ID
                    order_request = {
                        "a": asset_id,  # Our calculated spot asset ID (10000 + spot_index)
                        "b": is_buy,
                        "p": str(price),
                        "s": str(size),
                        "r": False,  # reduceOnly
                        "t": order_params
                    }
                    
                    timestamp = int(time.time() * 1000)
                    action = {
                        "type": "order",
                        "orders": [order_request],
                        "grouping": "na"
                    }
                    
                    # Sign and send the order
                    signature = sign_l1_action(
                        exchange.wallet,
                        action,
                        None,  # vault_address
                        timestamp,
                        exchange.expires_after,
                        exchange.base_url == "https://api.hyperliquid.xyz"
                    )
                    
                    result = exchange._post_action(action, signature, timestamp)
                    logger.info(f"Spot order placed with asset ID {asset_id} for wallet {wallet_id}: {symbol} {'BUY' if is_buy else 'SELL'} {size} @ {price}")
                else:
                    # For perp trading, use the normal SDK method
                    result = exchange.order(symbol, is_buy, size, price, order_params)
                    logger.info(f"Perp order placed for wallet {wallet_id}: {symbol} {'BUY' if is_buy else 'SELL'} {size} @ {price}")
                
                logger.info(f"Full order response: {result}")
                return result
            except Exception as e:
                logger.error(f"Order placement failed for wallet {wallet_id}: {str(e)}")
                logger.info(f"Full error response: {e}")
                return {"success": False, "error": str(e)}
            
        except Exception as e:
            logger.error(f"Failed to place order: {e}")
            raise
    
    def cancel_order(self, wallet_address: str, wallet_id: str, symbol: str, oid: int) -> Dict[str, Any]:
        """Cancel a specific order"""
        try:
            exchange = self.create_exchange_client(wallet_address, wallet_id)
            
            result = exchange.cancel(symbol, oid)
            
            logger.info(f"Order {oid} cancelled for wallet {wallet_id}")
            return result
            
        except Exception as e:
            logger.error(f"Failed to cancel order {oid} for wallet {wallet_id}: {str(e)}")
            raise
    
    def cancel_all_orders(self, wallet_address: str, wallet_id: str, symbol: Optional[str] = None) -> Dict[str, Any]:
        """Cancel all orders for a symbol or all symbols"""
        try:
            exchange = self.create_exchange_client(wallet_address, wallet_id)
            
            result = exchange.cancel_all(symbol)
            
            logger.info(f"All orders cancelled for wallet {wallet_id} (symbol: {symbol or 'ALL'})")
            return result
            
        except Exception as e:
            logger.error(f"Failed to cancel all orders for wallet {wallet_id}: {str(e)}")
            raise
    
    def get_open_orders(self, wallet_address: str) -> List[Dict[str, Any]]:
        """Get all open orders for a wallet"""
        try:
            user_state = self.get_user_state(wallet_address)
            open_orders = user_state.get("assetPositions", [])
            
            # Filter for actual open orders
            orders = []
            for position in open_orders:
                position_orders = position.get("position", {}).get("openOrders", [])
                orders.extend(position_orders)
            
            logger.info(f"Retrieved {len(orders)} open orders for {wallet_address}")
            return orders
            
        except Exception as e:
            logger.error(f"Failed to get open orders for {wallet_address}: {str(e)}")
            raise
    
    def get_positions(self, wallet_address: str) -> List[Dict[str, Any]]:
        """Get all positions for a wallet"""
        try:
            user_state = self.get_user_state(wallet_address)
            positions = []
            
            for asset_position in user_state.get("assetPositions", []):
                position = asset_position.get("position")
                if position and float(position.get("szi", "0")) != 0:
                    positions.append({
                        "symbol": asset_position.get("coin"),
                        "size": position.get("szi"),
                        "entry_price": position.get("entryPx"),
                        "unrealized_pnl": position.get("unrealizedPnl"),
                        "margin_used": position.get("marginUsed")
                    })
            
            logger.info(f"Retrieved {len(positions)} positions for {wallet_address}")
            return positions
            
        except Exception as e:
            logger.error(f"Failed to get positions for {wallet_address}: {str(e)}")
            raise
    
    def get_account_value(self, wallet_address: str) -> Dict[str, Any]:
        """Get total account value and margin info"""
        try:
            user_state = self.get_user_state(wallet_address)
            margin_summary = user_state.get("marginSummary", {})
            
            return {
                "account_value": margin_summary.get("accountValue", "0"),
                "total_margin_used": margin_summary.get("totalMarginUsed", "0"),
                "total_ntl_pos": margin_summary.get("totalNtlPos", "0"),
                "total_raw_usd": margin_summary.get("totalRawUsd", "0")
            }
            
        except Exception as e:
            logger.error(f"Failed to get account value for {wallet_address}: {str(e)}")
            raise
