import os
import dotenv

from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build

from scripts.workspace_manager import WorkspaceManager

# Load environment variables from .env file
dotenv.load_dotenv()

# OAuth 2.0 Client ID JSON file
OAUTH_CLIENT_SECRETS_FILE = os.getenv('OAUTH_CLIENT_SECRETS_FILE')

# Define the scopes
SCOPES = [
    'https://www.googleapis.com/auth/admin.directory.user',
    'https://www.googleapis.com/auth/admin.directory.orgunit'
]

def get_credentials():
    """Get user credentials for Google API."""
    creds = None

    if os.path.exists('token.json'):
        creds = Credentials.from_authorized_user_file('token.json', SCOPES)

    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(
                OAUTH_CLIENT_SECRETS_FILE, SCOPES)
            creds = flow.run_local_server(port=0)

        with open('token.json', 'w') as token:
            token.write(creds.to_json())

    return creds

def initialize_service(api_name, api_version, credentials):
    """Initialize a Google API service."""
    return build(api_name, api_version, credentials=credentials)

def main():
    credentials = get_credentials()
    if not credentials:
        print("Failed to obtain credentials.")
        return

    admin_service = initialize_service('admin', 'directory_v1', credentials)
    wm = WorkspaceManager(admin_service)

    while True:
        print("\n      Main Menu:     ")
        print("-----------------------")
        print("1. User Management")
        print("2. Run Script 2")
        print("3. Exit")
        main_choice = input("Enter choice: ")

        if main_choice == '1':
            while True:
                print("\nUser Management Menu:")
                print("-----------------------")
                print("1. List all users")
                print("2. Create a new user")
                print("3. Bulk create users")
                print("4. Delete a user")
                print("5. Bulk delete users")
                print("6. Back to main menu")
                print("7. Exit Program")

                user_mgmt_choice = input("Enter choice: ")

                if user_mgmt_choice == '1':
                    wm.list_all_users()
                elif user_mgmt_choice == '2':
                    wm.create_user()
                elif user_mgmt_choice == '3':
                    wm.bulk_users()
                elif user_mgmt_choice == '4':
                    wm.delete_user()
                elif user_mgmt_choice == '5':
                    wm.bulk_delete()
                elif user_mgmt_choice == '6':
                    break
                elif user_mgmt_choice == '7':
                    return
                else:
                    print("Invalid choice, please try again.")
        elif main_choice == '2':
            # Placeholder for other script functionalities
            pass
        elif main_choice == '3':
            break
        else:
            print("Invalid choice, please try again.")

if __name__ == '__main__':
    main()
