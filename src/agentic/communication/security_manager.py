"""
Security Manager for agentic AI system
Handles authentication, authorization, and encryption for agent communications
"""

import hashlib
import hmac
import json
import secrets
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
import jwt
import logging
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
import base64

from ..core.interfaces import ISecurityManager
from ..core.models import AgentConfiguration


class SecurityManager(ISecurityManager):
    """
    Security manager for agent authentication, authorization, and encryption
    """
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.logger = logging.getLogger(__name__)
        
        # Initialize encryption
        self.encryption_key = self._generate_or_load_encryption_key()
        self.cipher_suite = Fernet(self.encryption_key)
        
        # JWT settings
        self.jwt_secret = config.get("jwt_secret", secrets.token_urlsafe(32))
        self.jwt_algorithm = config.get("jwt_algorithm", "HS256")
        self.token_expiry_hours = config.get("token_expiry_hours", 24)
        
        # Agent permissions and policies
        self.agent_permissions: Dict[str, List[str]] = {}
        self.communication_policies: Dict[str, Dict[str, Any]] = {}
        self.active_tokens: Dict[str, Dict[str, Any]] = {}
        
        # Load default policies
        self._load_default_policies()
    
    def _generate_or_load_encryption_key(self) -> bytes:
        """Generate or load encryption key"""
        key_file = self.config.get("encryption_key_file", ".encryption_key")
        
        try:
            # Try to load existing key
            with open(key_file, "rb") as f:
                return f.read()
        except FileNotFoundError:
            # Generate new key
            key = Fernet.generate_key()
            
            # Save key securely (in production, use proper key management)
            with open(key_file, "wb") as f:
                f.write(key)
            
            self.logger.info("Generated new encryption key")
            return key
    
    def _load_default_policies(self) -> None:
        """Load default security policies"""
        # Default agent permissions
        self.agent_permissions.update({
            "orchestrator": ["*"],  # Full permissions
            "cost_management": ["cost_analysis", "budget_monitoring", "cost_optimization"],
            "resource_management": ["resource_monitoring", "resource_optimization"],
            "forecasting": ["cost_forecasting", "trend_analysis"],
            "alert_management": ["alert_generation", "notification_sending"],
            "user_interface": ["user_interaction", "response_formatting"],
            "approval": ["decision_management", "approval_processing"]
        })
        
        # Default communication policies
        self.communication_policies.update({
            "orchestrator": {
                "can_communicate_with": ["*"],
                "can_receive_from": ["*"],
                "encryption_required": False
            },
            "cost_management": {
                "can_communicate_with": ["orchestrator", "approval", "alert_management"],
                "can_receive_from": ["orchestrator", "user_interface"],
                "encryption_required": True
            },
            "resource_management": {
                "can_communicate_with": ["orchestrator", "approval", "alert_management"],
                "can_receive_from": ["orchestrator", "user_interface"],
                "encryption_required": True
            },
            "forecasting": {
                "can_communicate_with": ["orchestrator", "approval", "cost_management"],
                "can_receive_from": ["orchestrator", "user_interface"],
                "encryption_required": True
            },
            "alert_management": {
                "can_communicate_with": ["orchestrator", "approval", "user_interface"],
                "can_receive_from": ["*"],
                "encryption_required": False
            },
            "user_interface": {
                "can_communicate_with": ["orchestrator"],
                "can_receive_from": ["*"],
                "encryption_required": False
            },
            "approval": {
                "can_communicate_with": ["*"],
                "can_receive_from": ["*"],
                "encryption_required": True
            }
        })
    
    async def validate_sender(self, sender: str, recipient: str) -> bool:
        """Validate if sender is authorized to communicate with recipient"""
        try:
            # Get sender's communication policy
            sender_policy = self.communication_policies.get(sender, {})
            can_communicate_with = sender_policy.get("can_communicate_with", [])
            
            # Check if sender can communicate with recipient
            if "*" in can_communicate_with or recipient in can_communicate_with:
                # Check recipient's policy
                recipient_policy = self.communication_policies.get(recipient, {})
                can_receive_from = recipient_policy.get("can_receive_from", [])
                
                if "*" in can_receive_from or sender in can_receive_from:
                    return True
            
            self.logger.warning(f"Communication denied: {sender} -> {recipient}")
            return False
            
        except Exception as e:
            self.logger.error(f"Error validating sender: {e}")
            return False
    
    async def validate_action(self, agent_id: str, action: str, context: Dict[str, Any]) -> bool:
        """Validate if agent is authorized to perform specific action"""
        try:
            agent_permissions = self.agent_permissions.get(agent_id, [])
            
            # Check if agent has wildcard permission
            if "*" in agent_permissions:
                return True
            
            # Check if agent has specific permission
            if action in agent_permissions:
                return True
            
            # Check for pattern-based permissions
            for permission in agent_permissions:
                if permission.endswith("*") and action.startswith(permission[:-1]):
                    return True
            
            # Check context-based permissions
            if self._validate_context_permissions(agent_id, action, context):
                return True
            
            self.logger.warning(f"Action denied: {agent_id} -> {action}")
            return False
            
        except Exception as e:
            self.logger.error(f"Error validating action: {e}")
            return False
    
    def _validate_context_permissions(self, agent_id: str, action: str, context: Dict[str, Any]) -> bool:
        """Validate permissions based on context"""
        # Example: Cost management agent can only modify budgets below certain threshold
        if agent_id == "cost_management" and action == "modify_budget":
            budget_amount = context.get("budget_amount", 0)
            max_budget = self.config.get("max_budget_modification", 10000)
            return budget_amount <= max_budget
        
        # Example: Resource management agent can only terminate instances with specific tags
        if agent_id == "resource_management" and action == "terminate_instance":
            instance_tags = context.get("instance_tags", {})
            return instance_tags.get("Environment") in ["dev", "test"]
        
        return False
    
    async def encrypt_sensitive_data(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Encrypt sensitive data in agent communications"""
        try:
            # Identify sensitive fields
            sensitive_fields = self._identify_sensitive_fields(data)
            
            if not sensitive_fields:
                return data
            
            encrypted_data = data.copy()
            
            for field_path in sensitive_fields:
                # Get the value to encrypt
                value = self._get_nested_value(data, field_path)
                
                if value is not None:
                    # Encrypt the value
                    encrypted_value = self.cipher_suite.encrypt(
                        json.dumps(value).encode('utf-8')
                    )
                    
                    # Store encrypted value with metadata
                    encrypted_field = {
                        "encrypted": True,
                        "value": base64.b64encode(encrypted_value).decode('utf-8'),
                        "field_path": field_path
                    }
                    
                    # Replace original value
                    self._set_nested_value(encrypted_data, field_path, encrypted_field)
            
            return encrypted_data
            
        except Exception as e:
            self.logger.error(f"Error encrypting sensitive data: {e}")
            return data
    
    async def decrypt_sensitive_data(self, encrypted_data: Dict[str, Any]) -> Dict[str, Any]:
        """Decrypt sensitive data from agent communications"""
        try:
            decrypted_data = encrypted_data.copy()
            
            # Find encrypted fields
            encrypted_fields = self._find_encrypted_fields(encrypted_data)
            
            for field_path in encrypted_fields:
                encrypted_field = self._get_nested_value(encrypted_data, field_path)
                
                if isinstance(encrypted_field, dict) and encrypted_field.get("encrypted"):
                    try:
                        # Decrypt the value
                        encrypted_value = base64.b64decode(encrypted_field["value"])
                        decrypted_value = self.cipher_suite.decrypt(encrypted_value)
                        original_value = json.loads(decrypted_value.decode('utf-8'))
                        
                        # Replace encrypted field with original value
                        self._set_nested_value(decrypted_data, field_path, original_value)
                        
                    except Exception as e:
                        self.logger.error(f"Error decrypting field {field_path}: {e}")
            
            return decrypted_data
            
        except Exception as e:
            self.logger.error(f"Error decrypting sensitive data: {e}")
            return encrypted_data
    
    async def generate_auth_token(self, agent_id: str, permissions: List[str]) -> str:
        """Generate authentication token for agent"""
        try:
            payload = {
                "agent_id": agent_id,
                "permissions": permissions,
                "issued_at": datetime.utcnow().isoformat(),
                "expires_at": (datetime.utcnow() + timedelta(hours=self.token_expiry_hours)).isoformat(),
                "token_id": secrets.token_urlsafe(16)
            }
            
            token = jwt.encode(payload, self.jwt_secret, algorithm=self.jwt_algorithm)
            
            # Store active token
            self.active_tokens[payload["token_id"]] = {
                "agent_id": agent_id,
                "permissions": permissions,
                "expires_at": payload["expires_at"]
            }
            
            return token
            
        except Exception as e:
            self.logger.error(f"Error generating auth token: {e}")
            raise
    
    async def validate_auth_token(self, token: str) -> Dict[str, Any]:
        """Validate authentication token"""
        try:
            # Decode token
            payload = jwt.decode(token, self.jwt_secret, algorithms=[self.jwt_algorithm])
            
            # Check if token is still active
            token_id = payload.get("token_id")
            if token_id not in self.active_tokens:
                raise jwt.InvalidTokenError("Token not found in active tokens")
            
            # Check expiration
            expires_at = datetime.fromisoformat(payload["expires_at"])
            if datetime.utcnow() > expires_at:
                # Remove expired token
                self.active_tokens.pop(token_id, None)
                raise jwt.ExpiredSignatureError("Token has expired")
            
            return {
                "valid": True,
                "agent_id": payload["agent_id"],
                "permissions": payload["permissions"],
                "expires_at": payload["expires_at"]
            }
            
        except jwt.ExpiredSignatureError:
            return {"valid": False, "error": "Token expired"}
        except jwt.InvalidTokenError as e:
            return {"valid": False, "error": f"Invalid token: {e}"}
        except Exception as e:
            self.logger.error(f"Error validating auth token: {e}")
            return {"valid": False, "error": str(e)}
    
    async def get_agent_permissions(self, agent_id: str) -> List[str]:
        """Get permissions for specific agent"""
        return self.agent_permissions.get(agent_id, [])
    
    def revoke_token(self, token_id: str) -> bool:
        """Revoke authentication token"""
        try:
            if token_id in self.active_tokens:
                del self.active_tokens[token_id]
                return True
            return False
        except Exception as e:
            self.logger.error(f"Error revoking token: {e}")
            return False
    
    def update_agent_permissions(self, agent_id: str, permissions: List[str]) -> bool:
        """Update permissions for agent"""
        try:
            self.agent_permissions[agent_id] = permissions
            self.logger.info(f"Updated permissions for agent {agent_id}")
            return True
        except Exception as e:
            self.logger.error(f"Error updating agent permissions: {e}")
            return False
    
    def update_communication_policy(self, agent_id: str, policy: Dict[str, Any]) -> bool:
        """Update communication policy for agent"""
        try:
            self.communication_policies[agent_id] = policy
            self.logger.info(f"Updated communication policy for agent {agent_id}")
            return True
        except Exception as e:
            self.logger.error(f"Error updating communication policy: {e}")
            return False
    
    def _identify_sensitive_fields(self, data: Dict[str, Any]) -> List[str]:
        """Identify sensitive fields in data"""
        sensitive_keywords = [
            "password", "token", "key", "secret", "credential", "auth",
            "api_key", "access_key", "private_key", "certificate"
        ]
        
        sensitive_fields = []
        
        def check_dict(d, path=""):
            if isinstance(d, dict):
                for key, value in d.items():
                    current_path = f"{path}.{key}" if path else key
                    
                    # Check if key contains sensitive keywords
                    if any(keyword in key.lower() for keyword in sensitive_keywords):
                        sensitive_fields.append(current_path)
                    elif isinstance(value, (dict, list)):
                        check_dict(value, current_path)
            elif isinstance(d, list):
                for i, item in enumerate(d):
                    current_path = f"{path}[{i}]"
                    check_dict(item, current_path)
        
        check_dict(data)
        return sensitive_fields
    
    def _find_encrypted_fields(self, data: Dict[str, Any]) -> List[str]:
        """Find encrypted fields in data"""
        encrypted_fields = []
        
        def check_dict(d, path=""):
            if isinstance(d, dict):
                for key, value in d.items():
                    current_path = f"{path}.{key}" if path else key
                    
                    if isinstance(value, dict) and value.get("encrypted"):
                        encrypted_fields.append(current_path)
                    elif isinstance(value, (dict, list)):
                        check_dict(value, current_path)
            elif isinstance(d, list):
                for i, item in enumerate(d):
                    current_path = f"{path}[{i}]"
                    check_dict(item, current_path)
        
        check_dict(data)
        return encrypted_fields
    
    def _get_nested_value(self, data: Dict[str, Any], path: str) -> Any:
        """Get nested value from data using dot notation path"""
        keys = path.split('.')
        current = data
        
        for key in keys:
            if '[' in key and ']' in key:
                # Handle array indices
                key_name, index_part = key.split('[', 1)
                index = int(index_part.rstrip(']'))
                current = current[key_name][index]
            else:
                current = current[key]
        
        return current
    
    def _set_nested_value(self, data: Dict[str, Any], path: str, value: Any) -> None:
        """Set nested value in data using dot notation path"""
        keys = path.split('.')
        current = data
        
        for key in keys[:-1]:
            if '[' in key and ']' in key:
                # Handle array indices
                key_name, index_part = key.split('[', 1)
                index = int(index_part.rstrip(']'))
                current = current[key_name][index]
            else:
                current = current[key]
        
        final_key = keys[-1]
        if '[' in final_key and ']' in final_key:
            key_name, index_part = final_key.split('[', 1)
            index = int(index_part.rstrip(']'))
            current[key_name][index] = value
        else:
            current[final_key] = value
    
    def get_security_stats(self) -> Dict[str, Any]:
        """Get security statistics"""
        active_token_count = len(self.active_tokens)
        expired_tokens = 0
        
        # Count expired tokens
        current_time = datetime.utcnow()
        for token_data in self.active_tokens.values():
            expires_at = datetime.fromisoformat(token_data["expires_at"])
            if current_time > expires_at:
                expired_tokens += 1
        
        return {
            "active_tokens": active_token_count,
            "expired_tokens": expired_tokens,
            "registered_agents": len(self.agent_permissions),
            "communication_policies": len(self.communication_policies)
        }