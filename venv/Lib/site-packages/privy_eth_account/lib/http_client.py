import json
from typing import Optional, Any, Dict, cast
import httpx
from typing_extensions import override
from .authorization_signatures import get_authorization_signature
import base64

class PrivyHTTPClient(httpx.Client):
    """A custom HTTP client that adds authorization signatures to requests."""

    def __init__(
        self,
        *,
        app_id: str,
        app_secret: str,
        authorization_key: Optional[str] = None,
        **kwargs: Any,
    ) -> None:
        """Initialize the client.
        
        Args:
            app_id: The Privy app ID
            authorization_key: The authorization private key. If not provided, requests will not be signed.
            **kwargs: Additional arguments to pass to httpx.Client
        """
        super().__init__(**kwargs)
        self.app_id = app_id
        self.app_secret = app_secret
        self.authorization_key = None
        
        if authorization_key is not None:
            # Remove the 'wallet-auth:' prefix if present
            self.authorization_key = authorization_key.replace("wallet-auth:", "")

    def _prepare_request(self, request: httpx.Request) -> None:
        """Add authorization signature to the request if authorization_key is set.
        
        Args:
            request: The request to prepare
        """
        # Skip if no authorization key or not a POST request
        if self.authorization_key is None or request.method != "POST":
            return

        # Get the request body
        try:
            body_str = request.read().decode("utf-8")
            if body_str:
                body = json.loads(body_str)
            else:
                body = {}
        except Exception:
            body = {}

        # Generate the signature
        signature = get_authorization_signature(
            url=str(request.url),
            body=cast(Dict[str, Any], body),
            app_id=self.app_id,
            private_key=self.authorization_key,
        )

        # Add the signature to the request headers
        request.headers["privy-authorization-signature"] = signature

        # Create Basic auth token
        auth_string = f"{self.app_id}:{self.app_secret}"
        auth_bytes = auth_string.encode('ascii')
        base64_bytes = base64.b64encode(auth_bytes)
        base64_auth = base64_bytes.decode('ascii')

        request.headers["privy-app-id"] = self.app_id
        request.headers["Authorization"] = f"Basic {base64_auth}"

    @override
    def send(self, request: httpx.Request, **kwargs: Any) -> httpx.Response:
        """Send a request with authorization signature if authorization_key is set.
        
        Args:
            request: The request to send
            **kwargs: Additional arguments to pass to httpx.Client.send
            
        Returns:
            The response from the server
        """
        self._prepare_request(request)
        return super().send(request, **kwargs)