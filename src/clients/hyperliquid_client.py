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
        
        # Initialize info client for market data
        self.info = Info(base_url=self.base_url, skip_ws=True)
        
        logger.info(f"Hyperliquid trader initialized (testnet: {use_testnet})")
    
    def create_exchange_client(self, wallet_address: str, wallet_id: str) -> Exchange:
        """Create an exchange client for a specific wallet"""
        try:
            # Create eth-account using Privy
            account = self.privy_manager.create_eth_account(wallet_address, wallet_id)
            
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
            # Get all available symbols from meta
            meta = self.info.meta()
            available_symbols = [item["name"] for item in meta.get("universe", [])]
            logger.info(f"Available symbols: {available_symbols}")
            # Check if symbol is available
            if symbol not in available_symbols:
                logger.error(f"Symbol {symbol} not found in available symbols.")
                raise ValueError(f"Symbol {symbol} not found. Available symbols: {available_symbols}")

            # Create exchange client for this wallet
            exchange = self.create_exchange_client(wallet_address, wallet_id)
            # ... (actual order placement logic follows here)
            # This part should be restored to its original implementation.
        except Exception as e:
            logger.error(f"Failed to place order: {e}")
            raise
            # Debug: print the symbol requested
            logger.info(f"Requested to place order for symbol: {symbol}")
            # Get all available symbols from meta
            meta = self.info.meta()
            available_symbols = [item["name"] for item in meta.get("universe", [])]
            logger.info(f"Available symbols: {available_symbols}")
            # Check if symbol is available
            if symbol not in available_symbols:
                logger.error(f"Symbol {symbol} not found in available symbols.")
                raise ValueError(f"Symbol {symbol} not found. Available symbols: {available_symbols}")

            # Create exchange client for this wallet
            exchange = self.create_exchange_client(wallet_address, wallet_id)
            
            # Prepare order parameters
            if market_type == "spot":
                # For spot, use the spot-specific order method if available, or pass a spot flag/parameter
                # Here, we assume exchange.order() supports spot via an extra param (API may differ)
                if order_type == "limit":
                    order_params = {"limit": {"tif": "Gtc"}, "marketType": "spot"}
                else:
                    order_params = {"market": {}, "marketType": "spot"}
            else:
                if order_type == "limit":
                    order_params = {"limit": {"tif": "Gtc"}}
                else:
                    order_params = {"market": {}}
            
            # Place the order
            result = exchange.order(symbol, is_buy, size, price, order_params)
            
            logger.info(f"Order placed for wallet {wallet_id}: {symbol} {'BUY' if is_buy else 'SELL'} {size} @ {price} (market_type={market_type})")
            return result
            
        except Exception as e:
            logger.error(f"Failed to place order for wallet {wallet_id}: {str(e)}")
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
