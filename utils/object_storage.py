"""
Object Storage Service for Replit
Handles file uploads and downloads using Google Cloud Storage via Replit's sidecar
"""
from google.cloud import storage
from google.auth.credentials import Credentials
from google.auth.transport import requests as google_requests
from google.oauth2 import service_account
import requests
import os
from typing import Optional
from datetime import datetime, timedelta
import uuid

REPLIT_SIDECAR_ENDPOINT = "http://127.0.0.1:1106"


class ReplitStorageCredentials(Credentials):
    """Custom credentials for Replit's object storage"""
    
    def __init__(self):
        super().__init__()
        self._token = None
        self._expiry = None
        # Initialize token immediately
        self.refresh(google_requests.Request())
        
    def refresh(self, request):
        """Fetch token from Replit sidecar"""
        try:
            response = requests.get(f"{REPLIT_SIDECAR_ENDPOINT}/credential", timeout=5)
            if response.ok:
                data = response.json()
                self._token = data.get('access_token')
                if not self._token:
                    raise Exception("No access_token in credential response")
                self._expiry = datetime.utcnow() + timedelta(hours=1)
            else:
                raise Exception(f"Failed to get credentials - Status {response.status_code}: {response.text}")
        except requests.exceptions.RequestException as e:
            raise Exception(f"Failed to connect to Replit sidecar: {e}")
        except Exception as e:
            raise Exception(f"Credential refresh error: {e}")
    
    def before_request(self, request, method, url, headers):
        """Add authorization header to requests"""
        if self.expired:
            self.refresh(google_requests.Request())
        headers['Authorization'] = f'Bearer {self._token}'
    
    @property
    def token(self):
        return self._token
    
    @token.setter
    def token(self, value):
        self._token = value
    
    @property
    def expiry(self):
        return self._expiry
    
    @expiry.setter
    def expiry(self, value):
        self._expiry = value
    
    @property
    def expired(self):
        if not self._expiry:
            return True
        return datetime.utcnow() >= self._expiry
    
    @property
    def valid(self):
        return self._token is not None and not self.expired


class ObjectStorageService:
    """Service for managing file storage in Replit Object Storage"""
    
    def __init__(self):
        """Initialize storage client with Replit credentials"""
        try:
            credentials = ReplitStorageCredentials()
            self.client = storage.Client(
                credentials=credentials,
                project=""
            )
        except Exception as e:
            print(f"Warning: Could not initialize object storage: {e}")
            self.client = None
    
    def get_bucket_name(self) -> str:
        """Get bucket name from environment variable"""
        bucket_name = os.getenv('OBJECT_STORAGE_BUCKET', 'hr-files')
        return bucket_name
    
    def upload_file(self, file_content: bytes, filename: str, content_type: str = 'application/octet-stream') -> Optional[str]:
        """
        Upload file to object storage
        
        Args:
            file_content: File content as bytes
            filename: Original filename
            content_type: MIME type of the file
            
        Returns:
            Storage path of uploaded file or None if failed
        """
        if not self.client:
            return None
            
        try:
            bucket_name = self.get_bucket_name()
            bucket = self.client.bucket(bucket_name)
            
            # Generate unique filename
            timestamp = datetime.utcnow().strftime('%Y%m%d_%H%M%S')
            unique_id = str(uuid.uuid4())[:8]
            storage_filename = f"uploads/{timestamp}_{unique_id}_{filename}"
            
            # Create blob and upload
            blob = bucket.blob(storage_filename)
            blob.upload_from_string(file_content, content_type=content_type)
            
            # Return the storage path
            return f"/{bucket_name}/{storage_filename}"
            
        except Exception as e:
            print(f"Error uploading file: {e}")
            return None
    
    def get_file(self, storage_path: str) -> Optional[tuple]:
        """
        Get file from object storage
        
        Args:
            storage_path: Path in format /<bucket>/<object_path>
            
        Returns:
            Tuple of (file_content, content_type, filename) or None if not found
        """
        if not self.client:
            return None
            
        try:
            # Parse storage path
            parts = storage_path.strip('/').split('/', 1)
            if len(parts) != 2:
                return None
                
            bucket_name, object_path = parts
            
            bucket = self.client.bucket(bucket_name)
            blob = bucket.blob(object_path)
            
            if not blob.exists():
                return None
            
            # Download file content
            file_content = blob.download_as_bytes()
            content_type = blob.content_type or 'application/octet-stream'
            
            # Extract original filename from path
            filename = object_path.split('/')[-1]
            # Remove timestamp and UUID prefix
            if '_' in filename:
                parts = filename.split('_', 2)
                if len(parts) >= 3:
                    filename = parts[2]
            
            return (file_content, content_type, filename)
            
        except Exception as e:
            print(f"Error getting file: {e}")
            return None
    
    def delete_file(self, storage_path: str) -> bool:
        """
        Delete file from object storage
        
        Args:
            storage_path: Path in format /<bucket>/<object_path>
            
        Returns:
            True if deleted successfully, False otherwise
        """
        if not self.client:
            return False
            
        try:
            # Parse storage path
            parts = storage_path.strip('/').split('/', 1)
            if len(parts) != 2:
                return False
                
            bucket_name, object_path = parts
            
            bucket = self.client.bucket(bucket_name)
            blob = bucket.blob(object_path)
            blob.delete()
            
            return True
            
        except Exception as e:
            print(f"Error deleting file: {e}")
            return False
    
    def generate_signed_url(self, storage_path: str, expiration_minutes: int = 60) -> Optional[str]:
        """
        Generate a signed URL for temporary access to a file
        
        Args:
            storage_path: Path in format /<bucket>/<object_path>
            expiration_minutes: How long the URL should be valid
            
        Returns:
            Signed URL or None if failed
        """
        if not self.client:
            return None
            
        try:
            # Parse storage path
            parts = storage_path.strip('/').split('/', 1)
            if len(parts) != 2:
                return None
                
            bucket_name, object_path = parts
            
            # Use Replit sidecar to sign URL
            request_data = {
                "bucket_name": bucket_name,
                "object_name": object_path,
                "method": "GET",
                "expires_at": (datetime.utcnow() + timedelta(minutes=expiration_minutes)).isoformat()
            }
            
            response = requests.post(
                f"{REPLIT_SIDECAR_ENDPOINT}/object-storage/signed-object-url",
                json=request_data
            )
            
            if response.ok:
                data = response.json()
                return data.get('signed_url')
            
            return None
            
        except Exception as e:
            print(f"Error generating signed URL: {e}")
            return None
