# Google Ads API OAuth2 Authentication

This project provides a complete OAuth2 authentication solution for the Google Ads API, allowing you to obtain refresh tokens for long-term access to Google Ads data.

## 🚀 Features

- **OAuth2 Authentication**: Complete OAuth2 flow for Google Ads API
- **Refresh Token Management**: Automatic token refresh and storage
- **Token Persistence**: Save and load credentials between sessions
- **Comprehensive Error Handling**: Detailed error messages and troubleshooting
- **Multiple Usage Examples**: Basic and advanced usage patterns

## 📋 Prerequisites

1. **Google Cloud Project**: You need a Google Cloud project with the Google Ads API enabled
2. **OAuth2 Credentials**: Download your OAuth2 client credentials from Google Cloud Console
3. **Python 3.7+**: The code requires Python 3.7 or higher

## 🛠️ Installation

1. **Install Dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

2. **Get OAuth2 Credentials**:
   - Go to [Google Cloud Console](https://console.cloud.google.com/)
   - Create a new project or select an existing one
   - Enable the **Google Ads API**
   - Go to **APIs & Services > Credentials**
   - Click **Create Credentials > OAuth 2.0 Client ID**
   - Choose **Desktop application** as the application type
   - Download the JSON file and rename it to `client_secrets.json`
   - Place it in the same directory as the scripts

## 📁 Files Overview

- `google_ads_oauth.py` - Main OAuth2 authentication module
- `example_usage.py` - Usage examples and demonstrations
- `requirements.txt` - Python dependencies
- `README.md` - This documentation

## 🔐 Quick Start

### Basic Usage

```python
from google_ads_oauth import setup_google_ads_oauth

# Setup authentication
oauth_handler, credentials = setup_google_ads_oauth()

# Get refresh token
refresh_token = oauth_handler.get_refresh_token()
print(f"Refresh Token: {refresh_token}")
```

### Advanced Usage

```python
from google_ads_oauth import GoogleAdsOAuth2

# Create custom OAuth2 handler
oauth_handler = GoogleAdsOAuth2(
    client_secrets_file='client_secrets.json',
    token_file='my_token.pickle'
)

# Authenticate
credentials = oauth_handler.authenticate()

# Get comprehensive token information
token_info = oauth_handler.get_token_info()
print(f"Token expires at: {token_info['expiry']}")
```

## 🏃‍♂️ Running the Examples

### Run the main authentication script:
```bash
python google_ads_oauth.py
```

### Run the usage examples:
```bash
python example_usage.py
```

## 🔧 Configuration

### OAuth2 Scopes

The default scopes included are:
- `https://www.googleapis.com/auth/adwords` - Google Ads API access
- `https://www.googleapis.com/auth/userinfo.email` - User email access
- `https://www.googleapis.com/auth/userinfo.profile` - User profile access

### File Locations

- **Client Secrets**: `client_secrets.json` (download from Google Cloud Console)
- **Token Storage**: `token.pickle` (created automatically)
- **Refresh Token**: `refresh_token.txt` (saved separately for easy access)

## 🔄 Token Management

### Getting a Refresh Token

```python
from google_ads_oauth import GoogleAdsOAuth2

oauth_handler = GoogleAdsOAuth2('client_secrets.json')
refresh_token = oauth_handler.get_refresh_token()

if refresh_token:
    print(f"Refresh token: {refresh_token}")
    # Save for future use
    with open('refresh_token.txt', 'w') as f:
        f.write(refresh_token)
```

### Using a Refresh Token

```python
from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request

# Load your saved refresh token
with open('refresh_token.txt', 'r') as f:
    refresh_token = f.read().strip()

# Create credentials from refresh token
credentials = Credentials(
    None,  # No access token initially
    refresh_token=refresh_token,
    token_uri="https://oauth2.googleapis.com/token",
    client_id="YOUR_CLIENT_ID",
    client_secret="YOUR_CLIENT_SECRET",
    scopes=['https://www.googleapis.com/auth/adwords']
)

# Refresh the access token
credentials.refresh(Request())
```

### Revoking Credentials

```python
oauth_handler = GoogleAdsOAuth2('client_secrets.json')
oauth_handler.revoke_credentials()
```

## 🚨 Troubleshooting

### Common Issues

1. **"Client secrets file not found"**
   - Ensure `client_secrets.json` is in the same directory
   - Verify the file name is correct

2. **"Authentication failed"**
   - Check your internet connection
   - Verify Google Ads API is enabled in your project
   - Ensure you're using a valid Google account

3. **"No refresh token available"**
   - This usually happens on the first authentication
   - Run the authentication flow again
   - Check if your OAuth2 client is configured for desktop applications

4. **Import errors**
   - Install all required dependencies: `pip install -r requirements.txt`
   - Ensure you're using Python 3.7+

### Getting Help

1. Check the error messages in the console output
2. Verify your Google Cloud Console setup
3. Ensure all dependencies are installed correctly
4. Check that your OAuth2 client is configured properly

## 🔒 Security Best Practices

1. **Never commit credentials**: Add `client_secrets.json` and `*.pickle` to `.gitignore`
2. **Store tokens securely**: Use environment variables or secure storage for production
3. **Rotate tokens regularly**: Revoke and regenerate tokens periodically
4. **Limit scopes**: Only request the scopes you actually need

## 📚 Next Steps

After obtaining your refresh token, you can:

1. **Use with google-ads library**:
   ```python
   from google.ads.googleads.client import GoogleAdsClient
   
   client = GoogleAdsClient.load_from_storage({
       "developer_token": "YOUR_DEVELOPER_TOKEN",
       "client_id": "YOUR_CLIENT_ID",
       "client_secret": "YOUR_CLIENT_SECRET",
       "refresh_token": "YOUR_REFRESH_TOKEN",
       "use_proto_plus": True,
   })
   ```

2. **Make API calls**:
   ```python
   customer_service = client.get_service("CustomerService")
   resource_names = customer_service.list_accessible_customers()
   ```

3. **Build applications**: Use the refresh token in your applications for automated access

## 📄 License

This project is provided as-is for educational and development purposes. Please ensure you comply with Google's API terms of service when using this code. 