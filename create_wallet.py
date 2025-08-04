from src.clients.privy_client import PrivyWalletManager

if __name__ == "__main__":
    manager = PrivyWalletManager()
    wallet = manager.create_user_wallet("demo_user")
    print(wallet)
