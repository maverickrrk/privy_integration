from fastapi import FastAPI, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
import logging
from typing import List, Optional
import uvicorn

from ..core.config import Config
from ..core.models import *
from ..clients.privy_client import PrivyWalletManager
from ..clients.hyperliquid_client import HyperliquidTrader
from ..core.database import db

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Initialize FastAPI app
app = FastAPI(
    title="Privy-Hyperliquid Trading Platform",
    description="Server-managed wallet trading platform using Privy and Hyperliquid",
    version="1.0.0"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Global instances
privy_manager = None
hyperliquid_trader = None

@app.on_event("startup")
async def startup_event():
    """Initialize services on startup"""
    global privy_manager, hyperliquid_trader
    
    try:
        # Validate configuration
        Config.validate()
        
        # Initialize services
        privy_manager = PrivyWalletManager()
        hyperliquid_trader = HyperliquidTrader(use_testnet=True)  # Use testnet by default
        
        logger.info("Application started successfully")
        
    except Exception as e:
        logger.error(f"Failed to start application: {e}")
        raise

def get_privy_manager() -> PrivyWalletManager:
    """Dependency to get Privy manager"""
    if privy_manager is None:
        raise HTTPException(status_code=500, detail="Privy manager not initialized")
    return privy_manager

def get_hyperliquid_trader() -> HyperliquidTrader:
    """Dependency to get Hyperliquid trader"""
    if hyperliquid_trader is None:
        raise HTTPException(status_code=500, detail="Hyperliquid trader not initialized")
    return hyperliquid_trader

# User Management Endpoints

@app.post("/users", response_model=ApiResponse)
async def create_user(user_data: UserCreate):
    """Create a new user"""
    try:
        # Check if user already exists
        existing_user = db.get_user(user_data.user_id)
        if existing_user:
            raise HTTPException(status_code=400, detail="User already exists")
        
        # Create user in database
        user = db.create_user(user_data.user_id, user_data.email)
        
        return ApiResponse(
            success=True,
            message="User created successfully",
            data=user
        )
        
    except Exception as e:
        logger.error(f"Failed to create user: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/users/{user_id}", response_model=ApiResponse)
async def get_user(user_id: str):
    """Get user information"""
    user = db.get_user(user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    return ApiResponse(
        success=True,
        message="User retrieved successfully",
        data=user
    )

@app.get("/users", response_model=ApiResponse)
async def list_users():
    """List all users"""
    users = db.list_all_users()
    return ApiResponse(
        success=True,
        message="Users retrieved successfully",
        data=users
    )

# Wallet Management Endpoints

@app.post("/users/{user_id}/wallets", response_model=ApiResponse)
async def create_wallet(
    user_id: str,
    privy_mgr: PrivyWalletManager = Depends(get_privy_manager)
):
    """Create a new wallet for a user"""
    try:
        # Check if user exists
        user = db.get_user(user_id)
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        
        # Create wallet using Privy
        wallet_data = privy_mgr.create_user_wallet(user_id)
        
        # Store wallet in database
        db.add_wallet_to_user(user_id, wallet_data)
        
        return ApiResponse(
            success=True,
            message="Wallet created successfully",
            data=wallet_data
        )
        
    except Exception as e:
        logger.error(f"Failed to create wallet: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/users/{user_id}/wallets", response_model=ApiResponse)
async def get_user_wallets(user_id: str):
    """Get all wallets for a user"""
    user = db.get_user(user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    wallets = db.get_user_wallets(user_id)
    
    return ApiResponse(
        success=True,
        message="Wallets retrieved successfully",
        data=wallets
    )

@app.get("/wallets/{wallet_id}/balance", response_model=ApiResponse)
async def get_wallet_balance(
    wallet_id: str,
    privy_mgr: PrivyWalletManager = Depends(get_privy_manager)
):
    """Get wallet balance (DEMO: always returns 1000.0 ETH)"""
    try:
        wallet = db.get_wallet(wallet_id)
        if not wallet:
            raise HTTPException(status_code=404, detail="Wallet not found")
        
        # DEMO OVERRIDE: Always return 1000.0 ETH
        balance = {
            "wallet_id": wallet_id,
            "address": wallet["address"],
            "balance": "1000.0",
            "currency": "ETH"
        }
        return ApiResponse(
            success=True,
            message="Balance retrieved successfully (DEMO OVERRIDE)",
            data=balance
        )
    except Exception as e:
        logger.error(f"Failed to get balance: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# Trading Endpoints

@app.get("/market/symbols", response_model=ApiResponse)
async def get_supported_symbols(trader: HyperliquidTrader = Depends(get_hyperliquid_trader)):
    """Get all supported trading symbols"""
    try:
        meta = trader.info.meta()
        symbols = [item["name"] for item in meta.get("universe", [])]
        return ApiResponse(success=True, message="Symbols retrieved successfully", data=symbols)
    except Exception as e:
        logger.error(f"Failed to get supported symbols: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/market/{symbol}", response_model=ApiResponse)
async def get_market_data(
    symbol: str,
    trader: HyperliquidTrader = Depends(get_hyperliquid_trader)
):
    """Get market data for a symbol"""
    try:
        market_data = trader.get_market_data(symbol)
        
        return ApiResponse(
            success=True,
            message="Market data retrieved successfully",
            data=market_data
        )
        
    except Exception as e:
        logger.error(f"Failed to get market data: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/wallets/{wallet_id}/orders", response_model=ApiResponse)
async def place_order(
    wallet_id: str,
    order: OrderRequest,
    trader: HyperliquidTrader = Depends(get_hyperliquid_trader),
    privy_mgr: PrivyWalletManager = Depends(get_privy_manager)
):
    """Place a trading order and send a real on-chain ETH transfer as proof"""
    try:
        wallet = db.get_wallet(wallet_id)
        if not wallet:
            raise HTTPException(status_code=404, detail="Wallet not found")
        
        # Convert order side to boolean
        is_buy = order.side == OrderSide.BUY
        
        # Use provided price or 0 for market orders
        price = order.price if order.order_type == OrderType.LIMIT else 0
        
        # Place the simulated order (off-chain logic)
        result = trader.place_order(
            wallet["address"],
            wallet_id,
            order.symbol,
            is_buy,
            order.size,
            price,
            order.order_type.value,
            order.market_type.value
        )

        # Send a real ETH transfer to self (on-chain proof)
        # Value: 0.001 ETH (in wei)
        eth_value_wei = int(0.001 * 1e18)
        tx_result = privy_mgr.send_transaction(
            wallet_id=wallet_id,
            to_address=wallet["address"],
            value=eth_value_wei,
            chain_id="eip155:84532"  # Base Sepolia testnet (adjust as needed)
        )
        tx_hash = tx_result.get("result", {}).get("hash") or tx_result.get("result")

        return ApiResponse(
            success=True,
            message="Order placed and on-chain ETH transfer sent.",
            data={
                "order_result": result,
                "onchain_tx_hash": tx_hash
            }
        )
        
    except Exception as e:
        logger.error(f"Failed to place order or send on-chain tx: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.delete("/wallets/{wallet_id}/orders", response_model=ApiResponse)
async def cancel_order(
    wallet_id: str,
    cancel_request: CancelOrderRequest,
    trader: HyperliquidTrader = Depends(get_hyperliquid_trader)
):
    """Cancel a specific order"""
    try:
        wallet = db.get_wallet(wallet_id)
        if not wallet:
            raise HTTPException(status_code=404, detail="Wallet not found")
        
        result = trader.cancel_order(
            wallet["address"],
            wallet_id,
            cancel_request.symbol,
            cancel_request.order_id
        )
        
        return ApiResponse(
            success=True,
            message="Order cancelled successfully",
            data=result
        )
        
    except Exception as e:
        logger.error(f"Failed to cancel order: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.delete("/wallets/{wallet_id}/orders/all", response_model=ApiResponse)
async def cancel_all_orders(
    wallet_id: str,
    symbol: Optional[str] = None,
    trader: HyperliquidTrader = Depends(get_hyperliquid_trader)
):
    """Cancel all orders for a wallet"""
    try:
        wallet = db.get_wallet(wallet_id)
        if not wallet:
            raise HTTPException(status_code=404, detail="Wallet not found")
        
        result = trader.cancel_all_orders(wallet["address"], wallet_id, symbol)
        
        return ApiResponse(
            success=True,
            message="All orders cancelled successfully",
            data=result
        )
        
    except Exception as e:
        logger.error(f"Failed to cancel all orders: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/wallets/{wallet_id}/orders", response_model=ApiResponse)
async def get_open_orders(
    wallet_id: str,
    trader: HyperliquidTrader = Depends(get_hyperliquid_trader)
):
    """Get open orders for a wallet"""
    try:
        wallet = db.get_wallet(wallet_id)
        if not wallet:
            raise HTTPException(status_code=404, detail="Wallet not found")
        
        orders = trader.get_open_orders(wallet["address"])
        
        return ApiResponse(
            success=True,
            message="Open orders retrieved successfully",
            data=orders
        )
        
    except Exception as e:
        logger.error(f"Failed to get open orders: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/wallets/{wallet_id}/positions", response_model=ApiResponse)
async def get_positions(
    wallet_id: str,
    trader: HyperliquidTrader = Depends(get_hyperliquid_trader)
):
    """Get positions for a wallet"""
    try:
        wallet = db.get_wallet(wallet_id)
        if not wallet:
            raise HTTPException(status_code=404, detail="Wallet not found")
        
        positions = trader.get_positions(wallet["address"])
        
        return ApiResponse(
            success=True,
            message="Positions retrieved successfully",
            data=positions
        )
        
    except Exception as e:
        logger.error(f"Failed to get positions: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/wallets/{wallet_id}/account", response_model=ApiResponse)
async def get_account_value(
    wallet_id: str,
    trader: HyperliquidTrader = Depends(get_hyperliquid_trader)
):
    """Get account value and margin info"""
    try:
        wallet = db.get_wallet(wallet_id)
        if not wallet:
            raise HTTPException(status_code=404, detail="Wallet not found")
        
        account_info = trader.get_account_value(wallet["address"])
        
        return ApiResponse(
            success=True,
            message="Account info retrieved successfully",
            data=account_info
        )
        
    except Exception as e:
        logger.error(f"Failed to get account info: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# Health check endpoint
@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy", "message": "Privy-Hyperliquid Trading Platform is running"}

if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host=Config.API_HOST,
        port=Config.API_PORT,
        reload=Config.DEBUG
    )
