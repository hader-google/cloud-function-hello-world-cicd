import requests
import json
from datetime import datetime, timedelta
from concurrent.futures import ThreadPoolExecutor, as_completed


# Replace with your actual API endpoints, credentials, and scopes

AUTH_TYPES = {
     "AUTH1": {
        "URL": "[URL]",
        "client_id": "[CLIENT_ID]",
        "client_secret": "[CLIENT_SECRET]",
        "token": "",
    },
    "AUTH2": {
        "URL": "[URL]",
        "client_id": "[CLIENT_ID]",
        "client_secret": "[CLIENT_SECRET]",
        "token": "",

    },
}


TOKEN_CACHE = {}  # Moved TOKEN_CACHE outside the function for shared access

def get_oauth_token(api_name, config):
    """Retrieves and caches OAuth tokens, refreshing them if expired."""
    token_data = TOKEN_CACHE.get(api_name)
    auth_type = config.get('auth_type')
    client_id = AUTH_TYPES[auth_type]['client_id']
    client_secret = AUTH_TYPES[auth_type]['client_secret']
    auth_url = AUTH_TYPES[auth_type]['URL']

    if token_data and token_data["expires_at"] > datetime.utcnow():
        return token_data["access_token"]

    # Token is missing or expired, request a new one
    # (Replace with your actual OAuth token retrieval logic)
    with ThreadPoolExecutor(max_workers=1) as executor:  # Thread lock for token refresh
        future = executor.submit(refresh_token, auth_type, auth_url, client_id, client_secret, config)
        token_data = future.result()

    # Calculate expiration time with a safety margin
    expires_at = datetime.utcnow() + timedelta(
        seconds=token_data["expires_in"] - 60
    )
    token_data["expires_at"] = expires_at
    TOKEN_CACHE[api_name] = token_data

    return token_data["access_token"]


def refresh_token(auth_type, auth_url, client_id, client_secret, config):
    """Refreshes the OAuth token."""
    if auth_type == "AUTH1":
        token_response = requests.post(
            auth_url,
            data={
                "grant_type": "client_credentials",
                "client_id": client_id,
                "client_secret": client_secret,
                "scope": config.get('scope'),
            },
        )
    else:
        token_response = requests.post(
            auth_url,
            data={
                "grant_type": "client_credentials",
                "client_id": client_id,
                "client_secret": client_secret,
            },
        )
    token_response.raise_for_status()
    return token_response.json()

def make_api_request(api_name, config):
    """Makes an API request with the appropriate OAuth token."""
    token = get_oauth_token(api_name, config)
    headers = {"Authorization": f"Bearer {token}"}

    if config.get("headers"):
        headers.update(config.get("headers"))

    if config.get("method_type") == "GET":
        response = requests.get(
            config.get('url'), headers=headers, json=config.get("request_body")
        )
    elif config.get("method_type") == "POST":
        response = requests.post(
            config.get('url'), headers=headers, json=config.get("request_body")
        )
    else:
        print("method not supported")
    response.raise_for_status()
    return response.json()


def all_consolidated_apis(request):
    """Cloud Function to handle the consolidated API call."""
    consolidated_response = {}
    API_CONFIGS = request.get_json()
    try:
        threads = []
        with ThreadPoolExecutor(max_workers=10) as executor:  # Adjust max_workers as needed
            for api, config in API_CONFIGS.items():
                threads.append(executor.submit(make_api_request, api, config))

            for task in as_completed(threads):
                api_name = list(API_CONFIGS.keys())[threads.index(task)]  # Get API name
                consolidated_response[api_name] = task.result()

        return consolidated_response

    except requests.exceptions.RequestException as e:
        return {'message':
            f"Error during API request: {e}"}
    except Exception as e:
        return {'message': f"An unexpected error occurred: {e}"}


def hello(request):
    return "Hello world!"