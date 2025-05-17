import requests
import jwt
import csv
import getpass
from datetime import datetime

# Read tenant URLs from CSV file
csv_input_file = 'black.csv'
tenant_urls = []

# Adjust the column name to match your CSV header (assumed to be "url")
with open(csv_input_file, mode='r', newline='') as csvfile:
    reader = csv.DictReader(csvfile)
    for row in reader:
        url = row.get('url')
        if url:
            tenant_urls.append(url.strip())

if not tenant_urls:
    print("No tenant URLs found in the CSV file.")
    exit(1)


# Function to log in and retrieve auth token
def login(tenant_url, username, password):
    url = f"{tenant_url}/api/v1/auth/login"
    headers = {
        "Cache-Control": "no-cache",
        "Content-Type": "application/x-www-form-urlencoded",
        "Accept": "application/json",
    }
    data = {"username": username, "password": password}
    
    resp = requests.post(url, headers=headers, data=data, verify=True)
    resp.raise_for_status()
    return resp.headers.get('Authorization')

# Function to get MQTT tokens and zone name from a tenant
def get_mqtt_tokens_and_zone(tenant_url, auth_token):
    url = f"{tenant_url}/api/v2/connector-configs/"
    headers = {
        "Authorization": auth_token,
        "Accept": "application/json"
    }

    try:
        response = requests.get(url, headers=headers, verify=True)
        response.raise_for_status()
        data = response.json()

        # Ensure "data" is a list
        connector_configs = data.get("data", [])
        if not isinstance(connector_configs, list):
            print(f"Unexpected response format from {tenant_url}: {data}")
            return []

        records = []

        # Loop through connector configs and extract MQTT tokens and zone names
        for config in connector_configs:
            attributes = config.get("attributes", {})
            zone = attributes.get("zone", "Unknown")  # Extract zone name
            
            mqtt_config = attributes.get("MQTTConfig", {})
            token = mqtt_config.get("token")
            if token:
                records.append((token, zone))

        if not records:
            print(f"No MQTT tokens found in connector configs for {tenant_url}.")

        return records

    except requests.exceptions.RequestException as e:
        print(f"Failed to fetch connector config for {tenant_url}: {e}")
        return []

# Function to decode JWT token and extract expiry date
def get_token_expiry(token):
    try:
        decoded_token = jwt.decode(token, options={"verify_signature": False})
        exp_timestamp = decoded_token.get("exp")
        if exp_timestamp:
            return datetime.utcfromtimestamp(exp_timestamp).strftime('%Y-%m-%d %H:%M:%S')
        return "Unknown Expiry"
    except jwt.DecodeError:
        return "Invalid Token"

# Prompt for credentials
username = "admin@datahub.com"
password = getpass.getpass(prompt='Enter your tenant password: ')

# Prepare CSV output
csv_filename = "blackrock_mqtt_tokens.csv"
with open(csv_filename, mode='w', newline='') as file:
    writer = csv.writer(file)
    writer.writerow(["Tenant URL", "Zone", "Token", "Expiry Date"])

    for tenant_url in tenant_urls:
        print(f"Processing {tenant_url}...")

        # Step 1: Authenticate
        try:
            auth_token = login(tenant_url, username, password)
        except requests.exceptions.RequestException as e:
            print(f"Login failed for {tenant_url}: {e}")
            continue

        # Step 2: Get MQTT Tokens and Zone Names
        records = get_mqtt_tokens_and_zone(tenant_url, auth_token)

        # Step 3: Extract expiry and write to CSV
        for token, zone in records:
            expiry_date = get_token_expiry(token)
            writer.writerow([tenant_url, zone, token, expiry_date])

print(f"CSV file '{csv_filename}' generated successfully.")
