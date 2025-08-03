from pydantic import BaseModel, Field
from typing import Optional, Dict, Any, List
from enum import Enum

class OrderType(str, Enum):
    LIMIT = "limit"
    MARKET = "market"

class OrderSide(str, Enum):
    BUY = "buy"
    SELL = "sell"

class UserCreate(BaseModel):
    user_id: str = Field(..., description="Unique user identifier")
    email: Optional[str] = Field(None, description="User email address")

class WalletResponse(BaseModel):
    wallet_id: str
    address: str
    chain_type: str
    user_id: str

class BalanceResponse(BaseModel):
    wallet_id: str
    address: str
    balance: str
    currency: str

class OrderRequest(BaseModel):
    symbol: str = Field(..., description="Trading symbol (e.g., 'ETH')")
    side: OrderSide = Field(..., description="Order side: buy or sell")
    size: float = Field(..., gt=0, description="Order size")
    price: Optional[float] = Field(None, gt=0, description="Order price (required for limit orders)")
    order_type: OrderType = Field(OrderType.LIMIT, description="Order type")

class OrderResponse(BaseModel):
    success: bool
    order_id: Optional[str] = None
    message: str
    details: Optional[Dict[str, Any]] = None

class CancelOrderRequest(BaseModel):
    symbol: str
    order_id: int

class MarketDataResponse(BaseModel):
    symbol: str
    current_price: str
    symbol_info: Dict[str, Any]

class PositionResponse(BaseModel):
    symbol: str
    size: str
    entry_price: Optional[str]
    unrealized_pnl: Optional[str]
    margin_used: Optional[str]

class AccountValueResponse(BaseModel):
    account_value: str
    total_margin_used: str
    total_ntl_pos: str
    total_raw_usd: str

class DepositRequest(BaseModel):
    amount: float = Field(..., gt=0, description="Amount to deposit")
    currency: str = Field(default="ETH", description="Currency to deposit")

class ApiResponse(BaseModel):
    success: bool
    message: str
    data: Optional[Any] = None
    error: Optional[str] = None
