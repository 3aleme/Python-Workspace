"""
Example usage of Google Ads OAuth2 authentication

This script demonstrates how to use the google_ads_oauth module
to authenticate and obtain refresh tokens.
"""

from google_ads_oauth import GoogleAdsOAuth2, setup_google_ads_oauth

def example_basic_usage():
    """Basic example of getting a refresh token"""
    print("🔐 Basic OAuth2 Authentication Example")
    print("=" * 40)
    
    try:
        # Setup OAuth2 authentication
        oauth_handler, credentials = setup_google_ads_oauth()
        
        # Get the refresh token
        refresh_token = oauth_handler.get_refresh_token()
        
        if refresh_token:
            print(f"✅ Refresh token obtained successfully!")
            print(f"🔄 Refresh Token: {refresh_token}")
            
            # Save to file for future use
            with open('my_refresh_token.txt', 'w') as f:
                f.write(refresh_token)
            print("💾 Refresh token saved to 'my_refresh_token.txt'")
        else:
            print("❌ No refresh token available")
            
    except Exception as e:
        print(f"❌ Error: {e}")


def example_advanced_usage():
    """Advanced example with detailed token information"""
    print("\n🔐 Advanced OAuth2 Authentication Example")
    print("=" * 45)
    
    try:
        # Create OAuth2 handler with custom file names
        oauth_handler = GoogleAdsOAuth2(
            client_secrets_file='client_secrets.json',
            token_file='my_token.pickle'
        )
        
        # Authenticate
        credentials = oauth_handler.authenticate()
        
        # Get comprehensive token information
        token_info = oauth_handler.get_token_info()
        
        print("📊 Token Information:")
        print(f"  • Access Token: {'✅ Available' if token_info['access_token'] else '❌ Not available'}")
        print(f"  • Refresh Token: {'✅ Available' if token_info['refresh_token'] else '❌ Not available'}")
        print(f"  • Expires At: {token_info['expiry']}")
        print(f"  • Scopes: {', '.join(token_info['scopes'])}")
        print(f"  • Client ID: {token_info['client_id']}")
        
        # Display refresh token if available
        if token_info['refresh_token']:
            print(f"\n🔄 Your Refresh Token:")
            print(f"{token_info['refresh_token']}")
            
    except Exception as e:
        print(f"❌ Error: {e}")


def example_token_management():
    """Example of token management operations"""
    print("\n🔐 Token Management Example")
    print("=" * 35)
    
    try:
        oauth_handler = GoogleAdsOAuth2('client_secrets.json')
        
        # Get current token info
        token_info = oauth_handler.get_token_info()
        print(f"Current refresh token available: {token_info['refresh_token'] is not None}")
        
        # Example: Revoke credentials (uncomment to use)
        # print("\n⚠️ Revoking credentials...")
        # oauth_handler.revoke_credentials()
        
    except Exception as e:
        print(f"❌ Error: {e}")


if __name__ == "__main__":
    # Run examples
    example_basic_usage()
    example_advanced_usage()
    example_token_management()
    
    print("\n" + "=" * 50)
    print("📚 Next Steps:")
    print("1. Use the refresh token with google-ads library")
    print("2. Store the refresh token securely")
    print("3. Use the token for API calls to Google Ads")
    print("4. Refresh the token when it expires") 