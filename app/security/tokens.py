"""Token encryption and RSVP token generation."""
import base64
import hmac
import hashlib
import secrets
from datetime import datetime, timedelta
from typing import Optional
from cryptography.fernet import Fernet
import structlog

from app.core.config import settings

logger = structlog.get_logger(__name__)


class TokenEncryption:
    """Encrypt and decrypt OAuth tokens."""
    
    def __init__(self):
        self.key = self._get_encryption_key()
        self.cipher = Fernet(self.key)
    
    def _get_encryption_key(self) -> bytes:
        """Get encryption key from settings."""
        enc_key = settings.OAUTH_ENC_KEY
        
        if enc_key.startswith("base64:"):
            # Decode base64 key
            key_b64 = enc_key[7:]  # Remove "base64:" prefix
            return base64.b64decode(key_b64)
        else:
            # Assume it's already a Fernet key
            return enc_key.encode('utf-8')
    
    def encrypt_token(self, token: str) -> str:
        """Encrypt a token."""
        try:
            encrypted = self.cipher.encrypt(token.encode('utf-8'))
            return base64.b64encode(encrypted).decode('utf-8')
        except Exception as e:
            logger.error("Failed to encrypt token", error=str(e))
            raise
    
    def decrypt_token(self, encrypted_token: str) -> str:
        """Decrypt a token."""
        try:
            encrypted_bytes = base64.b64decode(encrypted_token.encode('utf-8'))
            decrypted = self.cipher.decrypt(encrypted_bytes)
            return decrypted.decode('utf-8')
        except Exception as e:
            logger.error("Failed to decrypt token", error=str(e))
            raise


class RSVPTokenManager:
    """Generate and validate RSVP tokens."""
    
    def __init__(self):
        self.secret_key = settings.SECRET_KEY.encode('utf-8')
        self.token_lifetime = timedelta(hours=24)  # Tokens expire after 24 hours
    
    def generate_token(
        self,
        user_id: str,
        event_id: str,
        notification_id: str
    ) -> str:
        """Generate a signed RSVP token.
        
        Args:
            user_id: User ID
            event_id: Event ID
            notification_id: Notification ID
            
        Returns:
            Signed token string
        """
        # Create token data
        token_data = {
            "user_id": user_id,
            "event_id": event_id,
            "notification_id": notification_id,
            "issued_at": datetime.utcnow().isoformat(),
            "nonce": secrets.token_hex(16)
        }
        
        # Serialize token data
        import json
        token_json = json.dumps(token_data, sort_keys=True)
        
        # Create signature
        signature = hmac.new(
            self.secret_key,
            token_json.encode('utf-8'),
            hashlib.sha256
        ).hexdigest()
        
        # Combine data and signature
        token_parts = [token_json, signature]
        token = base64.b64encode('|'.join(token_parts).encode('utf-8')).decode('utf-8')
        
        return token
    
    def validate_token(self, token: str) -> Optional[dict]:
        """Validate and parse an RSVP token.
        
        Args:
            token: Token string to validate
            
        Returns:
            Token data if valid, None if invalid
        """
        try:
            # Decode token
            decoded = base64.b64decode(token.encode('utf-8')).decode('utf-8')
            token_json, signature = decoded.split('|', 1)
            
            # Verify signature
            expected_signature = hmac.new(
                self.secret_key,
                token_json.encode('utf-8'),
                hashlib.sha256
            ).hexdigest()
            
            if not hmac.compare_digest(signature, expected_signature):
                logger.warning("Invalid RSVP token signature")
                return None
            
            # Parse token data
            import json
            token_data = json.loads(token_json)
            
            # Check expiration
            issued_at = datetime.fromisoformat(token_data['issued_at'])
            if datetime.utcnow() - issued_at > self.token_lifetime:
                logger.warning("RSVP token expired", issued_at=issued_at)
                return None
            
            return token_data
            
        except Exception as e:
            logger.error("Failed to validate RSVP token", error=str(e))
            return None
    
    def is_token_valid(self, token: str) -> bool:
        """Check if token is valid without parsing data."""
        return self.validate_token(token) is not None


# Global instances
token_encryption = TokenEncryption()
rsvp_token_manager = RSVPTokenManager()


# Convenience functions
def encrypt_token(token: str) -> str:
    """Encrypt a token."""
    return token_encryption.encrypt_token(token)


def decrypt_token(encrypted_token: str) -> str:
    """Decrypt a token."""
    return token_encryption.decrypt_token(encrypted_token)


def generate_rsvp_token(user_id: str, event_id: str, notification_id: str) -> str:
    """Generate an RSVP token."""
    return rsvp_token_manager.generate_token(user_id, event_id, notification_id)


def validate_rsvp_token(token: str) -> Optional[dict]:
    """Validate an RSVP token."""
    return rsvp_token_manager.validate_token(token)
