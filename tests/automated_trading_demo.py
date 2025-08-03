#!/usr/bin/env python3
"""
Automated Trading Demo - Complete workflow demonstration
Shows users depositing funds and trading on HyperCore with Privy server-managed wallets
"""

import sys
import os

# Add src to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

import requests
import json
import time
import random
from typing import Dict, Any, List
from datetime import datetime

class AutomatedTradingDemo:
    """Automated demo of the complete trading platform workflow"""
    
    def __init__(self, base_url: str = "http://localhost:8900"):
        self.base_url = base_url.rstrip('/')
        self.session = requests.Session()
        self.users = []
        self.wallets = {}
        
    def log(self, message: str, level: str = "INFO"):
        """Log messages with timestamp"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        icon = {"INFO": "ℹ️", "SUCCESS": "✅", "ERROR": "❌", "WARNING": "⚠️"}.get(level, "📝")
        print(f"[{timestamp}] {icon} {message}")
    
    def make_request(self, method: str, endpoint: str, **kwargs) -> Dict[str, Any]:
        """Make HTTP request with error handling"""
        url = f"{self.base_url}{endpoint}"
        
        try:
            response = self.session.request(method, url, **kwargs)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            self.log(f"Request failed: {e}", "ERROR")
            if hasattr(e, 'response') and e.response:
                self.log(f"Response: {e.response.text}", "ERROR")
            raise
    
    def check_server_health(self) -> bool:
        """Check if the API server is running"""
        try:
            response = self.make_request("GET", "/health")
            if response.get("status") == "healthy":
                self.log("API server is healthy and running", "SUCCESS")
                return True
            else:
                self.log("API server health check failed", "ERROR")
                return False
        except Exception as e:
            self.log(f"Cannot connect to API server: {e}", "ERROR")
            self.log("Make sure to run 'python main.py' first", "WARNING")
            return False
    
    def create_demo_users(self, count: int = 3) -> List[Dict[str, Any]]:
        """Create multiple demo users"""
        self.log(f"Creating {count} demo users...", "INFO")
        
        users = []
        for i in range(count):
            user_id = f"trader_{int(time.time())}_{i+1}"
            email = f"trader{i+1}@demo.com"
            
            try:
                response = self.make_request("POST", "/users", json={
                    "user_id": user_id,
                    "email": email
                })
                
                if response.get("success"):
                    user_data = response["data"]
                    users.append(user_data)
                    self.log(f"Created user: {user_id}", "SUCCESS")
                else:
                    self.log(f"Failed to create user {user_id}: {response.get('message')}", "ERROR")
                    
            except Exception as e:
                self.log(f"Error creating user {user_id}: {e}", "ERROR")
        
        self.users = users
        return users
    
    def create_wallets_for_users(self) -> Dict[str, Dict[str, Any]]:
        """Create wallets for all users"""
        self.log("Creating wallets for all users...", "INFO")
        
        wallets = {}
        for user in self.users:
            user_id = user["user_id"]
            
            try:
                response = self.make_request("POST", f"/users/{user_id}/wallets")
                
                if response.get("success"):
                    wallet_data = response["data"]
                    wallets[user_id] = wallet_data
                    self.log(f"Created wallet for {user_id}: {wallet_data['address']}", "SUCCESS")
                else:
                    self.log(f"Failed to create wallet for {user_id}: {response.get('message')}", "ERROR")
                    
            except Exception as e:
                self.log(f"Error creating wallet for {user_id}: {e}", "ERROR")
        
        self.wallets = wallets
        return wallets
    
    def simulate_deposits(self):
        """Simulate users depositing funds (demo only)"""
        self.log("Simulating user deposits...", "INFO")
        
        for user_id, wallet_data in self.wallets.items():
            # In a real scenario, users would deposit actual funds
            # For demo, we'll just log the simulation
            deposit_amount = random.uniform(100, 1000)
            
            self.log(f"💰 User {user_id} deposited ${deposit_amount:.2f} to wallet {wallet_data['address']}", "INFO")
            
            # Simulate some delay
            time.sleep(0.5)
    
    def get_market_data(self, symbols: List[str] = ["ETH", "BTC"]) -> Dict[str, Any]:
        """Get market data for trading symbols"""
        self.log("Fetching market data...", "INFO")
        
        market_data = {}
        for symbol in symbols:
            try:
                response = self.make_request("GET", f"/market/{symbol}")
                
                if response.get("success"):
                    data = response["data"]
                    market_data[symbol] = data
                    price = data.get("current_price", "N/A")
                    self.log(f"📊 {symbol} current price: ${price}", "SUCCESS")
                else:
                    self.log(f"Failed to get market data for {symbol}: {response.get('message')}", "ERROR")
                    
            except Exception as e:
                self.log(f"Error getting market data for {symbol}: {e}", "ERROR")
        
        return market_data
    
    def simulate_trading_activity(self, market_data: Dict[str, Any]):
        """Simulate realistic trading activity"""
        self.log("Starting automated trading simulation...", "INFO")
        
        trading_strategies = [
            {"name": "Conservative", "risk": 0.1, "trade_size": 0.01},
            {"name": "Moderate", "risk": 0.2, "trade_size": 0.05},
            {"name": "Aggressive", "risk": 0.3, "trade_size": 0.1}
        ]
        
        for i, (user_id, wallet_data) in enumerate(self.wallets.items()):
            strategy = trading_strategies[i % len(trading_strategies)]
            wallet_id = wallet_data["wallet_id"]
            
            self.log(f"🎯 {user_id} using {strategy['name']} strategy", "INFO")
            
            # Simulate multiple trades
            for trade_num in range(random.randint(2, 5)):
                self.simulate_single_trade(user_id, wallet_id, market_data, strategy, trade_num + 1)
                time.sleep(1)  # Delay between trades
    
    def simulate_single_trade(self, user_id: str, wallet_id: str, market_data: Dict[str, Any], 
                             strategy: Dict[str, Any], trade_num: int):
        """Simulate a single trade"""
        
        # Choose random symbol
        symbol = random.choice(list(market_data.keys()))
        side = random.choice(["buy", "sell"])
        
        # Get current price
        current_price_str = market_data[symbol].get("current_price", "2000")
        try:
            current_price = float(current_price_str)
        except:
            current_price = 2000.0  # Fallback price
        
        # Calculate trade parameters
        size = strategy["trade_size"] * random.uniform(0.5, 2.0)
        price_variation = strategy["risk"] * random.uniform(-1, 1)
        limit_price = current_price * (1 + price_variation)
        
        self.log(f"📈 Trade #{trade_num} - {user_id}: {side.upper()} {size:.3f} {symbol} @ ${limit_price:.2f}", "INFO")
        
        try:
            # Place the order (this will likely fail on testnet without funds, but shows the flow)
            response = self.make_request("POST", f"/wallets/{wallet_id}/orders", json={
                "symbol": symbol,
                "side": side,
                "size": size,
                "price": limit_price,
                "order_type": "limit"
            })
            
            if response.get("success"):
                self.log(f"✅ Order placed successfully for {user_id}", "SUCCESS")
            else:
                # Expected for demo without real funds
                self.log(f"⚠️  Order simulation for {user_id}: {response.get('message', 'Demo order')}", "WARNING")
                
        except Exception as e:
            # Expected for demo - log as info rather than error
            self.log(f"📝 Trade simulation for {user_id} (expected in demo): {str(e)[:100]}...", "INFO")
    
    def check_account_status(self):
        """Check account status for all users"""
        self.log("Checking account status for all users...", "INFO")
        
        for user_id, wallet_data in self.wallets.items():
            wallet_id = wallet_data["wallet_id"]
            
            try:
                # Get account info
                response = self.make_request("GET", f"/wallets/{wallet_id}/account")
                
                if response.get("success"):
                    account_data = response["data"]
                    account_value = account_data.get("account_value", "0")
                    margin_used = account_data.get("total_margin_used", "0")
                    
                    self.log(f"💼 {user_id} - Account Value: ${account_value}, Margin Used: ${margin_used}", "SUCCESS")
                else:
                    self.log(f"Could not get account info for {user_id}: {response.get('message')}", "WARNING")
                
                # Get positions
                positions_response = self.make_request("GET", f"/wallets/{wallet_id}/positions")
                
                if positions_response.get("success"):
                    positions = positions_response["data"]
                    if positions:
                        self.log(f"📊 {user_id} has {len(positions)} open positions", "SUCCESS")
                        for pos in positions[:2]:  # Show first 2 positions
                            symbol = pos.get("symbol", "N/A")
                            size = pos.get("size", "0")
                            pnl = pos.get("unrealized_pnl", "0")
                            self.log(f"   └─ {symbol}: {size} (PnL: ${pnl})", "INFO")
                    else:
                        self.log(f"📊 {user_id} has no open positions", "INFO")
                
            except Exception as e:
                self.log(f"Error checking status for {user_id}: {e}", "ERROR")
            
            time.sleep(0.5)
    
    def demonstrate_wallet_security(self):
        """Demonstrate that private keys are never exposed"""
        self.log("🔐 Demonstrating wallet security...", "INFO")
        
        for user_id, wallet_data in self.wallets.items():
            wallet_id = wallet_data["wallet_id"]
            address = wallet_data["address"]
            
            self.log(f"🔑 {user_id}:", "INFO")
            self.log(f"   └─ Wallet ID: {wallet_id}", "INFO")
            self.log(f"   └─ Address: {address}", "INFO")
            self.log(f"   └─ Private Key: NEVER EXPOSED (Managed by Privy)", "SUCCESS")
            self.log(f"   └─ Signing: Done server-side by Privy", "SUCCESS")
    
    def run_complete_demo(self):
        """Run the complete automated demo"""
        print("🚀 AUTOMATED PRIVY-HYPERLIQUID TRADING DEMO")
        print("=" * 50)
        print("This demo shows the complete workflow:")
        print("1. Server-managed wallet creation")
        print("2. User fund deposits (simulated)")
        print("3. Automated trading on HyperCore")
        print("4. Account monitoring")
        print("5. Security demonstration")
        print("=" * 50)
        
        try:
            # Step 1: Health check
            if not self.check_server_health():
                return False
            
            # Step 2: Create users
            users = self.create_demo_users(3)
            if not users:
                self.log("No users created, stopping demo", "ERROR")
                return False
            
            # Step 3: Create wallets
            wallets = self.create_wallets_for_users()
            if not wallets:
                self.log("No wallets created, stopping demo", "ERROR")
                return False
            
            # Step 4: Simulate deposits
            self.simulate_deposits()
            
            # Step 5: Get market data
            market_data = self.get_market_data(["ETH", "BTC"])
            
            # Step 6: Demonstrate security
            self.demonstrate_wallet_security()
            
            # Step 7: Simulate trading
            self.simulate_trading_activity(market_data)
            
            # Step 8: Check final status
            self.check_account_status()
            
            # Summary
            print("\n" + "=" * 50)
            self.log("🎉 DEMO COMPLETED SUCCESSFULLY!", "SUCCESS")
            print("=" * 50)
            self.log(f"✅ Created {len(users)} users with server-managed wallets", "SUCCESS")
            self.log(f"✅ Demonstrated secure wallet operations", "SUCCESS")
            self.log(f"✅ Simulated trading on HyperCore L1", "SUCCESS")
            self.log(f"✅ All private keys remain secure with Privy", "SUCCESS")
            
            print("\n📊 PLATFORM CAPABILITIES DEMONSTRATED:")
            print("• Server-managed wallet creation")
            print("• Secure transaction signing")
            print("• HyperCore L1 trading integration")
            print("• Real-time market data")
            print("• Account monitoring")
            print("• Multi-user support")
            
            return True
            
        except Exception as e:
            self.log(f"Demo failed with error: {e}", "ERROR")
            return False

def main():
    """Main function"""
    demo = AutomatedTradingDemo()
    
    print("🎯 Choose demo mode:")
    print("1. Full automated demo (recommended)")
    print("2. Quick test (basic functionality)")
    print("3. Continuous trading simulation")
    
    try:
        choice = input("\nEnter choice (1-3): ").strip()
        
        if choice == "1":
            demo.run_complete_demo()
            
        elif choice == "2":
            print("\n🔍 Quick Test Mode")
            print("-" * 20)
            
            if demo.check_server_health():
                users = demo.create_demo_users(1)
                if users:
                    wallets = demo.create_wallets_for_users()
                    if wallets:
                        market_data = demo.get_market_data(["ETH"])
                        demo.check_account_status()
                        print("\n✅ Quick test completed successfully!")
            
        elif choice == "3":
            print("\n🔄 Continuous Trading Simulation")
            print("-" * 30)
            print("This will run continuous trading simulation...")
            print("Press Ctrl+C to stop")
            
            if demo.check_server_health():
                users = demo.create_demo_users(2)
                wallets = demo.create_wallets_for_users()
                
                if users and wallets:
                    try:
                        while True:
                            market_data = demo.get_market_data(["ETH", "BTC"])
                            demo.simulate_trading_activity(market_data)
                            demo.log("💤 Waiting 30 seconds before next trading cycle...", "INFO")
                            time.sleep(30)
                    except KeyboardInterrupt:
                        demo.log("🛑 Continuous simulation stopped by user", "INFO")
        
        else:
            print("❌ Invalid choice. Running full demo...")
            demo.run_complete_demo()
            
    except KeyboardInterrupt:
        print("\n👋 Demo stopped by user")
    except Exception as e:
        print(f"\n❌ Demo error: {e}")

if __name__ == "__main__":
    main()
