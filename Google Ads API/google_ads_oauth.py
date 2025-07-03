"""
Google Ads API OAuth2 Authentication Module

This module provides functions to authenticate with the Google Ads API using OAuth2
and obtain refresh tokens for long-term access.

Requirements:
- google-auth
- google-auth-oauthlib
- google-auth-httplib2
- google-api-python-client
"""

import os
import json
import pickle
from typing import Dict, Optional, Tuple
from pathlib import Path

try:
    from google.auth.transport.requests import Request
    from google.oauth2.credentials import Credentials
    from google_auth_oauthlib.flow import InstalledAppFlow
    from googleapiclient.discovery import build
    from googleapiclient.errors import HttpError
except ImportError as e:
    print(f"Missing required dependency: {e}")
    print("Please install required packages:")
    print("pip install google-auth google-auth-oauthlib google-auth-httplib2 google-api-python-client")
    raise

# Google Ads API OAuth2 scopes
SCOPES = [
    'https://www.googleapis.com/auth/adwords',
    'https://www.googleapis.com/auth/userinfo.email',
    'https://www.googleapis.com/auth/userinfo.profile'
]

# Google Ads API version
GOOGLE_ADS_API_VERSION = 'v16'

class GoogleAdsOAuth2:
    """
    Google Ads API OAuth2 authentication handler
    """
    
    def __init__(self, client_secrets_file: str, token_file: str = 'token.pickle'):
        """
        Initialize the OAuth2 handler
        
        Args:
            client_secrets_file (str): Path to the client secrets JSON file
            token_file (str): Path to store/load the token pickle file
        """
        self.client_secrets_file = client_secrets_file
        self.token_file = token_file
        self.credentials = None
        
    def authenticate(self) -> Credentials:
        """
        Authenticate with Google Ads API and return credentials
        
        Returns:
            Credentials: Valid OAuth2 credentials
        """
        # Load existing credentials if available
        if os.path.exists(self.token_file):
            with open(self.token_file, 'rb') as token:
                self.credentials = pickle.load(token)
        
        # If no valid credentials available, let the user log in
        if not self.credentials or not self.credentials.valid:
            if self.credentials and self.credentials.expired and self.credentials.refresh_token:
                try:
                    self.credentials.refresh(Request())
                except Exception as e:
                    print(f"Error refreshing token: {e}")
                    self.credentials = None
            
            if not self.credentials:
                self._get_new_credentials()
                
            # Save the credentials for the next run
            with open(self.token_file, 'wb') as token:
                pickle.dump(self.credentials, token)
        
        return self.credentials
    
    def _get_new_credentials(self):
        """Get new credentials through OAuth2 flow"""
        if not os.path.exists(self.client_secrets_file):
            raise FileNotFoundError(
                f"Client secrets file not found: {self.client_secrets_file}\n"
                "Please download your OAuth2 client credentials from Google Cloud Console"
            )
        
        flow = InstalledAppFlow.from_client_secrets_file(
            self.client_secrets_file, SCOPES
        )
        
        # Run the OAuth2 flow
        self.credentials = flow.run_local_server(port=0)
        
        print("✅ Authentication successful!")
        print(f"Access token expires at: {self.credentials.expiry}")
        print(f"Refresh token available: {self.credentials.refresh_token is not None}")
    
    def get_refresh_token(self) -> Optional[str]:
        """
        Get the refresh token from current credentials
        
        Returns:
            str: Refresh token if available, None otherwise
        """
        if not self.credentials:
            self.authenticate()
        
        return self.credentials.refresh_token
    
    def get_token_info(self) -> Dict:
        """
        Get comprehensive token information
        
        Returns:
            Dict: Token information including access token, refresh token, expiry, etc.
        """
        if not self.credentials:
            self.authenticate()
        
        return {
            'access_token': self.credentials.token,
            'refresh_token': self.credentials.refresh_token,
            'token_uri': self.credentials.token_uri,
            'client_id': self.credentials.client_id,
            'client_secret': self.credentials.client_secret,
            'scopes': self.credentials.scopes,
            'expiry': self.credentials.expiry.isoformat() if self.credentials.expiry else None,
            'expired': self.credentials.expired if hasattr(self.credentials, 'expired') else None
        }
    
    def revoke_credentials(self):
        """Revoke current credentials"""
        if self.credentials:
            try:
                self.credentials.revoke(Request())
                print("✅ Credentials revoked successfully")
            except Exception as e:
                print(f"Error revoking credentials: {e}")
        
        # Remove token file
        if os.path.exists(self.token_file):
            os.remove(self.token_file)
            print(f"✅ Token file removed: {self.token_file}")


def create_client_secrets_template() -> str:
    """
    Create a template for client_secrets.json file
    
    Returns:
        str: Template content for client_secrets.json
    """
    template = {
        "installed": {
            "client_id": "YOUR_CLIENT_ID.apps.googleusercontent.com",
            "project_id": "your-project-id",
            "auth_uri": "https://accounts.google.com/o/oauth2/auth",
            "token_uri": "https://oauth2.googleapis.com/token",
            "auth_provider_x509_cert_url": "https://www.googleapis.com/oauth2/v1/certs",
            "client_secret": "YOUR_CLIENT_SECRET",
            "redirect_uris": ["http://localhost"]
        }
    }
    
    return json.dumps(template, indent=2)


def setup_google_ads_oauth(
    client_secrets_file: str = 'client_secrets.json',
    token_file: str = 'token.pickle'
) -> Tuple[GoogleAdsOAuth2, Credentials]:
    """
    Setup and authenticate with Google Ads API
    
    Args:
        client_secrets_file (str): Path to client secrets file
        token_file (str): Path to token file
        
    Returns:
        Tuple[GoogleAdsOAuth2, Credentials]: OAuth2 handler and credentials
    """
    # Create OAuth2 handler
    oauth_handler = GoogleAdsOAuth2(client_secrets_file, token_file)
    
    # Authenticate
    credentials = oauth_handler.authenticate()
    
    return oauth_handler, credentials


def main():
    """
    Example usage of the Google Ads OAuth2 module
    """
    print("🔐 Google Ads API OAuth2 Authentication")
    print("=" * 50)
    
    # Check if client_secrets.json exists
    if not os.path.exists('client_secrets.json'):
        print("❌ client_secrets.json not found!")
        print("\n📋 To get your client secrets:")
        print("1. Go to Google Cloud Console (https://console.cloud.google.com/)")
        print("2. Create a new project or select existing one")
        print("3. Enable Google Ads API")
        print("4. Go to APIs & Services > Credentials")
        print("5. Create OAuth 2.0 Client ID (Desktop application)")
        print("6. Download the JSON file and rename to 'client_secrets.json'")
        print("7. Place it in the same directory as this script")
        
        # Create template file
        template_content = create_client_secrets_template()
        with open('client_secrets_template.json', 'w') as f:
            f.write(template_content)
        print(f"\n📄 Template created: client_secrets_template.json")
        print("Use this as a reference for the required format.")
        return
    
    try:
        # Setup authentication
        oauth_handler, credentials = setup_google_ads_oauth()
        
        # Get token information
        token_info = oauth_handler.get_token_info()
        
        print("\n✅ Authentication successful!")
        print(f"📧 Email: {credentials.id_token.get('email', 'N/A') if credentials.id_token else 'N/A'}")
        print(f"🔄 Refresh token: {'✅ Available' if token_info['refresh_token'] else '❌ Not available'}")
        print(f"⏰ Expires at: {token_info['expiry']}")
        
        # Display refresh token if available
        if token_info['refresh_token']:
            print(f"\n🔄 Refresh Token:")
            print(f"{token_info['refresh_token']}")
            
            # Save refresh token to file
            with open('refresh_token.txt', 'w') as f:
                f.write(token_info['refresh_token'])
            print(f"\n💾 Refresh token saved to: refresh_token.txt")
        
        # Test API access
        print("\n🧪 Testing API access...")
        try:
            # Note: This is a basic test. For actual Google Ads API calls,
            # you would use the google-ads library instead
            service = build('oauth2', 'v2', credentials=credentials)
            user_info = service.userinfo().get().execute()
            print(f"✅ API access confirmed for: {user_info.get('email', 'N/A')}")
        except Exception as e:
            print(f"⚠️ API test failed: {e}")
            print("This is normal if you haven't enabled the OAuth2 API")
        
    except Exception as e:
        print(f"❌ Authentication failed: {e}")
        print("\n🔧 Troubleshooting:")
        print("1. Ensure client_secrets.json is valid")
        print("2. Check your internet connection")
        print("3. Verify Google Ads API is enabled in your project")
        print("4. Make sure you're using a valid Google account")


if __name__ == "__main__":
    main() 