from eth_account.signers.local import LocalAccount, TransactionDictType
from eth_account.typed_transactions import TypedTransaction
from eth_account.messages import SignableMessage, _hash_eip191_message, encode_typed_data
from eth_account.datastructures import SignedMessage, SignedTransaction
from hexbytes import HexBytes
from eth_utils import keccak

from typing import Dict, Any, Optional
from .lib.http_client import PrivyHTTPClient

def convert_bytes_to_hex(obj):
    if isinstance(obj, bytes):
        return '0x' + obj.hex()
    elif isinstance(obj, dict):
        return {k: convert_bytes_to_hex(v) for k, v in obj.items()}
    elif isinstance(obj, list):
        return [convert_bytes_to_hex(element) for element in obj]
    return obj

class PrivyRemoteAccount(LocalAccount):
    """
    A wrapper around LocalAccount that uses a remote API for signing operations.
    """
    def __init__(
        self,
        address,
        api_client: PrivyHTTPClient,
        wallet_id,
    ):
        # Initialize without a private key
        self._address = address
        self.api_client = api_client
        self.wallet_id = wallet_id
    
    def sign_message(self, message: SignableMessage) -> SignedMessage:
        """
        Sign a message using the remote API.
        Returns a SignedMessage type from eth-account.
        """

        # TODO: consider adding raw hash signing as a fallback
        if message.version != HexBytes(b"E"):
            raise ValueError("Privy sign_message only support messages with version 0x45")

        # Get the message in the correct format
        message_bytes = message.body
        message_hex = HexBytes(message_bytes).hex()

        # Call the privy API for signing
        endpoint = f"https://auth.privy.io/api/v1/wallets/{self.wallet_id}/rpc"
        payload = {
            "method": "personal_sign",
            "params": {"message": message_hex, "encoding": "hex"}
        }
    
        response = self.api_client.post(endpoint, json=payload)
        if response.status_code != 200:
            raise ValueError(f"Failed to sign message: {response.text}")
    
        # Extract the signature from the response based on the structure
        result = response.json().get("data")
        signature = HexBytes(result.get("signature"))
        if not signature:
            raise ValueError("No signature found")

        # Extract r, s, v components
        r = int.from_bytes(signature[0:32])
        s = int.from_bytes(signature[32:64])
        v = signature[64]
    
        # Calculate the message hash
        message_hash = HexBytes(_hash_eip191_message(message))

        # Create a proper SignedMessage instance from eth-account
        return SignedMessage(
            signature=signature,
            message_hash=message_hash,
            r=r,
            s=s,
            v=v,
        )
    
    def sign_transaction(self, transaction_dict: TransactionDictType) -> SignedTransaction:
         # Call the privy API for signing
        endpoint = f"https://auth.privy.io/api/v1/wallets/{self.wallet_id}/rpc"
        payload = {
            "method": "eth_signTransaction",
            "params": {"transaction": transaction_dict}
        }

        response = self.api_client.post(endpoint, json=payload)
        if response.status_code != 200:
            raise ValueError(f"Failed to sign transaction: {response.text}")
    
        # Extract the signature from the response based on the structure
        result = response.json().get("data")
        raw_transaction = HexBytes(result['signed_transaction'])
        if not raw_transaction:
            raise ValueError("No signed_transaction found")

        # Calculate the message hash           
        hash = HexBytes(keccak(raw_transaction))

        # Extract the r, s, v components using the TypedTransaction helper
        [v, r, s] = TypedTransaction.from_bytes(raw_transaction).vrs()

        # Create a proper SignedTransaction instance from eth-account
        return SignedTransaction(
            hash=hash,
            raw_transaction=raw_transaction,
            v=v,
            r=r,
            s=s,
        )
    
    # Should we only support full_message since we expect primary_type?
    def sign_typed_data(self,full_message: Optional[Dict[str, Any]] = None) -> SignedMessage:
        """
        Sign EIP-712 typed data using the remote API.
        Returns a SignedMessage type from eth-account.

        Can be called with either:
        1. domain_data, message_types, message_data separately
        2. full_message containing the complete EIP-712 structure
        """

        # Calculate the message hash, we do this up here to avoid a deep copy of full_message
        message_hash = HexBytes(_hash_eip191_message(encode_typed_data(full_message=full_message)))

        if full_message is not None:
            typed_data = full_message
            # Ensure EIP712Domain is defined in types
            if "types" in typed_data and "EIP712Domain" not in typed_data["types"]:
                raise ValueError("EIP712Domain must be defined in typed_data.types")
        else:
            raise ValueError("Only full_message is supported")

        # We expect primary type in snake case
        if "primaryType" in typed_data:
           typed_data["primary_type"] = typed_data["primaryType"]
           del typed_data["primaryType"]

        # Apply the conversion to the message part
        typed_data = convert_bytes_to_hex(typed_data)

        # Call the privy API for signing typed data
        endpoint = f"https://auth.privy.io/api/v1/wallets/{self.wallet_id}/rpc"
        payload = {
            "method": "eth_signTypedData_v4",
            "params": {"typed_data": typed_data}
        }

        response = self.api_client.post(endpoint, json=payload)
        if response.status_code != 200:
            raise ValueError(f"Failed to sign typed data: {response.text}")

        # Extract the signature from the response
        result = response.json().get("data")
        signature = HexBytes(result.get("signature"))

        if not signature:
            raise ValueError("No signature found") 
        
        # Extract r, s, v components
        r = int.from_bytes(signature[0:32], 'big')
        s = int.from_bytes(signature[32:64], 'big')
        v = signature[64]

        # Create a proper SignedMessage instance from eth-account
        return SignedMessage(
            signature=signature,
            message_hash=message_hash,
            r=r,
            s=s,
            v=v,
        )
    
def create_eth_account(client: PrivyHTTPClient, wallet_address: str, wallet_id: str) -> PrivyRemoteAccount: 
    return PrivyRemoteAccount(
        address=wallet_address,
        api_client=client,
        wallet_id=wallet_id
    )