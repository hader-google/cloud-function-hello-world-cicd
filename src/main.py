# Imports Python standard library logging
import logging
import requests
import json
import functions_framework
from datetime import datetime, timedelta
from google.cloud import secretmanager
from concurrent.futures import ThreadPoolExecutor, as_completed

version_id = "latest"

def convert_datetime(obj):
    """Default function to encode datetimes into a serializable string for json encoding"""
    
    if isinstance(obj, datetime):
        return obj.isoformat()
    raise TypeError()  

def store_token_in_secret(project_id, location_id, secret_id, token):
    """ Stores authentication token in a GSM Secret"""
    
    client = secretmanager.SecretManagerServiceClient()
    # parent = f"projects/{project_id}/secrets/{secret_id}"
    parent = f"projects/{project_id}/locations/{location_id}/secrets/{secret_id}"

    token_json = json.dumps(token, default=convert_datetime)

    response = client.add_secret_version(
        request={"parent": parent, "payload": {"data": token_json.encode("UTF-8")}}
    )


def get_secret(project_id, secret_id):
    """Retrieves a secret from Secret Manager, creating it if it doesn't exist.

    Args:
        project_id: The ID of the GCP project.
        secret_id: The ID of the secret.

    Returns:
        The value of the secret, or an empty string if the secret was created.
    """

    client = secretmanager.SecretManagerServiceClient()
    name = f"projects/{project_id}/secrets/{secret_id}/versions/latest"

    if check_secret_exists(project_id, secret_id): 
        response = client.access_secret_version(name=name)
        return response.payload.data.decode('UTF-8')
    else:
        parent = f"projects/{project_id}"
        _ = client.create_secret(
        request={
            "parent": parent,
            "secret_id": secret_id,
            "secret": {"replication": {"automatic": {}}}
        }
    )   

        return "{}"

def check_secret_exists(project_id, secret_id):
    """Checks if a secret exists in Secret Manager.

    Args:
        project_id: The ID of the GCP project.
        secret_id: The ID of the secret.

    Returns:
        True if the secret exists, False otherwise.
    """

    client = secretmanager.SecretManagerServiceClient()
    name = f"projects/{project_id}/secrets/{secret_id}"

    try:
        client.get_secret(request={"name": name})
        return True
    except Exception as e:
        if "NOT_FOUND" in str(e):
            return False

def check_token_expiration(token_data):
    if len(token_data.keys()) > 0:
        expiration_date = datetime.strptime(token_data["expires_at"], '%Y-%m-%dT%H:%M:%S.%f')
        if expiration_date > datetime.utcnow():
            return True
        return False
    return False

def check_token_scope(token_data, config):
    token = token_data["access_token"]
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
    
    if response.status_code == 200:
        return True
    return False
    
def get_scope(config):
    scope = config.get("scope")
    return scope
    
def get_oauth_token(api_name, config):
    """Retrieves and caches OAuth tokens, refreshing them if expired."""
    
    PROJECT_ID = '786354113445'
    auth_type = config.get('auth_type').lower()

    # #Extract these values using GSM regional version
    client_id = get_regional_secret(PROJECT_ID,"us-central-1", f"{auth_type}_client_id")
    client_secret = get_regional_secret(PROJECT_ID,"us-central-1", f"{auth_type}_client_secret")
    auth_url = get_regional_secret(PROJECT_ID,"us-central-1", f"{auth_type}_url")

    print(client_id)
    print(client_secret)
    print(auth_url)

    # Token is missing or expired, request a new one
    if auth_type == "sat":
        scope = get_scope(config)
        token_data = json.loads(get_regional_secret(PROJECT_ID,"us-central-1",f"{auth_type}_token"))
        
        if check_token_expiration(token_data):
            if check_token_scope(token_data, config):
                return token_data["access_token"]
            

        token_response = requests.post(
            auth_url,
            data={
                "grant_type": "client_credentials",
                "client_id": client_id,
                "client_secret": client_secret,
                "scope": scope
            },
            headers={"Content-Type":"application/x-www-form-urlencoded"}
        )
    else:
        token_data = json.loads(get_regional_secret(PROJECT_ID,"us-central-1", f"{auth_type}_token"))

        if check_token_expiration(token_data):
            return token_data["access_token"]
        
        token_response = requests.post(
            auth_url,  
            data={
                "grant_type": "client_credentials",
                "client_id": client_id,
                "client_secret": client_secret,
            },
        )

    token_response.raise_for_status()  # Raise an error for bad responses
    token_data = token_response.json()

    
    # Calculate expiration time with a safety margin
    expires_at = datetime.utcnow() + timedelta(seconds=token_data["expires_in"] - 60)
    token_data["expires_at"] = expires_at

    if auth_type == "sat":    
        scope = get_scope(config)
        store_token_in_secret(PROJECT_ID,
                              "us-central-1", 
                            f"{auth_type}_token", 
                            token_data)
    else:
        store_token_in_secret(PROJECT_ID,
                              "us-central-1", 
                            f"{auth_type}_token", 
                            token_data)


    return token_data["access_token"]



def create_regional_secret(
    project_id: str,
    location_id: str,
    secret_id: str
            ) -> secretmanager.Secret:
    """
    Creates a new regional secret with the given name.
    """

    # Endpoint to call the regional secret manager sever
    api_endpoint = f"secretmanager.{location_id}.rep.googleapis.com"

    # Create the Secret Manager client.
    client = secretmanager.SecretManagerServiceClient(
        client_options={"api_endpoint": api_endpoint},
    )

    # Build the resource name of the parent project.
    parent = f"projects/{project_id}/locations/{location_id}"

    try:
        # Create the secret.
        response = client.create_secret(
            request={
                "parent": parent,
                "secret_id": secret_id,
                "secret": {"ttl": timedelta(days=5000)},
            }
        )
    except Exception as e:
        print(e)
        raise ValueError("Gotcha!")

    # Print the new secret name.
    print(f"Created secret: {response.name}")

    return response


def get_regional_secret(
    project_id: str, location_id: str, secret_id: str
         ) -> secretmanager.GetSecretRequest:
    """
    Gets information about the given secret. This only returns metadata about
    the secret container, not any secret material.
    """

    # Endpoint to call the regional Secret Manager API
    api_endpoint = f"secretmanager.{location_id}.rep.googleapis.com"
    print(secret_id)
    print(api_endpoint)
    # Create the Secret Manager client.
    client = secretmanager.SecretManagerServiceClient(
        client_options={"api_endpoint": api_endpoint},
    )

    # Build the resource name of the secret.
    name = f"projects/{project_id}/locations/{location_id}/secrets/{secret_id}/versions/{version_id}"

    try:
        response = client.access_secret_version(request={"name": name})
        print(response)
        print("Inside try")
    except Exception as e:
        print("Inside except")
        _ = create_regional_secret(project_id, location_id, secret_id)
        print("After the creation")
        response = client.access_secret_version(request={"name": name})
        print(response)
    return response.payload.data.decode('UTF-8')


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

@functions_framework.http
def secret_manager_access_test(request):
    """Function to test secret manager access."""
    project_id = "hader-poc-001"
    location_id = "us-central1"
    secret_id = "my_secret_value_test"
    return get_regional_secret(project_id, location_id, secret_id)
