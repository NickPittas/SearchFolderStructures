# secure_storage.py
import os
import base64
import json
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC

class SecureStorage:
    """Simple secure storage for API keys using encryption"""
    
    def __init__(self, storage_file="secure_keys.dat"):
        self.storage_file = os.path.join(os.path.expanduser('~'), storage_file)
        self.master_key = None
        
    def _get_master_key(self, password):
        """Derive encryption key from password"""
        # Use a fixed salt for consistency (in production, use random salt per user)
        salt = b'ai_file_organizer_salt_2024'
        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=32,
            salt=salt,
            iterations=100000,
        )
        key = base64.urlsafe_b64encode(kdf.derive(password.encode()))
        return Fernet(key)
    
    def save_api_key(self, service_name, api_key, master_password):
        """Save API key encrypted with master password"""
        try:
            fernet = self._get_master_key(master_password)
            
            # Load existing keys if file exists
            data = {}
            if os.path.exists(self.storage_file):
                try:
                    with open(self.storage_file, 'rb') as f:
                        encrypted_data = f.read()
                        decrypted_data = fernet.decrypt(encrypted_data)
                        data = json.loads(decrypted_data.decode())
                except:
                    # If decryption fails, start fresh (wrong password or corrupted file)
                    data = {}
            
            # Add/update the API key
            data[service_name] = api_key
            
            # Encrypt and save
            json_data = json.dumps(data)
            encrypted_data = fernet.encrypt(json_data.encode())
            
            with open(self.storage_file, 'wb') as f:
                f.write(encrypted_data)
                
            return True
            
        except Exception as e:
            print(f"Error saving API key: {e}")
            return False
    
    def load_api_key(self, service_name, master_password):
        """Load API key decrypted with master password"""
        try:
            if not os.path.exists(self.storage_file):
                return None
                
            fernet = self._get_master_key(master_password)
            
            with open(self.storage_file, 'rb') as f:
                encrypted_data = f.read()
                
            decrypted_data = fernet.decrypt(encrypted_data)
            data = json.loads(decrypted_data.decode())
            
            return data.get(service_name)
            
        except Exception as e:
            print(f"Error loading API key: {e}")
            return None
    
    def delete_api_key(self, service_name, master_password):
        """Delete a specific API key"""
        try:
            if not os.path.exists(self.storage_file):
                return True
                
            fernet = self._get_master_key(master_password)
            
            with open(self.storage_file, 'rb') as f:
                encrypted_data = f.read()
                
            decrypted_data = fernet.decrypt(encrypted_data)
            data = json.loads(decrypted_data.decode())
            
            if service_name in data:
                del data[service_name]
                
                # Save updated data
                json_data = json.dumps(data)
                encrypted_data = fernet.encrypt(json_data.encode())
                
                with open(self.storage_file, 'wb') as f:
                    f.write(encrypted_data)
                    
            return True
            
        except Exception as e:
            print(f"Error deleting API key: {e}")
            return False
    
    def has_stored_key(self, service_name):
        """Check if a key exists (without requiring password)"""
        try:
            if not os.path.exists(self.storage_file):
                return False
            # We can't check specific keys without password, but we can check if file exists
            return os.path.getsize(self.storage_file) > 0
        except:
            return False
