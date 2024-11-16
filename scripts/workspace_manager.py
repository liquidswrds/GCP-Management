import os
import csv
from itertools import groupby
from operator import itemgetter

class WorkspaceManager:
    def __init__(self, service):
        self.service = service

    def validate_password(self, password):
        return (12 <= len(password) <= 100 and
                any(char.isdigit() for char in password) and
                any(char.isupper() for char in password) and
                any(char.islower() for char in password) and
                any(char in "@#$%^&+=-_!? " for char in password))

    def list_org_units(self):
        try:
            result = self.service.orgunits().list(customerId='my_customer', type='all').execute()
            org_units = result.get('organizationUnits', [])

            if not org_units:
                print('No organizational units found.')
                return

            # Print header
            print("Organizational Units:")
            print("Number  Name  OrgUnitPath")

            # Print org unit details
            for i, ou in enumerate(org_units):
                print(f"{i+1:<6}  {ou['name']}  {ou['orgUnitPath']}")

            return org_units

        except Exception as e:
            print(f'An error occurred: {e}')

    def list_all_users(self):
        try:
            request = self.service.users().list(customer='my_customer', orderBy='email')
            users = []

            while request is not None:
                results = request.execute()
                users.extend(results.get('users', []))
                request = self.service.users().list_next(previous_request=request, previous_response=results)

            if not users:
                print('No users found.')
                return

            # Get admin status and org unit for each user
            for user in users:
                full_info = self.service.users().get(userKey=user['id'], projection='full').execute()
                user['isAdmin'] = full_info.get('isAdmin', False)
                user['orgUnit'] = full_info.get('orgUnitPath', '/')

            # Sort and group users by orgUnit
            users.sort(key=itemgetter('orgUnit'))
            users_grouped = groupby(users, key=itemgetter('orgUnit'))

            # Calculate column widths
            number_width = len(str(len(users)))
            email_width = max(len('Email'), max(len(user['primaryEmail']) for user in users))
            name_width = max(len('Full Name'), max(len(user['name']['fullName']) for user in users))
            admin_width = max(len('is Admin'), max(len(str(user['isAdmin'])) for user in users))
            org_unit_width = max(len('Org Unit'), max(len(user['orgUnit']) for user in users))

            # Print header
            print(f"{'No.':<{number_width}} {'Email':<{email_width}} {'Full Name':<{name_width}} {'Admin  ':<{admin_width}} {'Org Unit':<{org_unit_width}}")
            print(f"{'-' * number_width} {'-' * email_width} {'-' * name_width} {'-' * admin_width} {'-' * org_unit_width}")

            # Print user details grouped by orgUnit
            for org_unit, group in users_grouped:
                for i, user in enumerate(group, start=1):
                    print(f"{i:<{number_width}} {user['primaryEmail']:<{email_width}} {user['name']['fullName']:<{name_width}} {str(user['isAdmin']):<{admin_width}} {user['orgUnit']:<{org_unit_width}}")
        except Exception as e:
            print(f"An error occurred: {e}")

    def delete_user(self):
        try:
            email = input("Enter email of user to delete: ")
            self.service.users().delete(userKey=email).execute()
            print(f'User {email} deleted successfully.')

        except Exception as e:
            print(f'An error occurred: {e}')

    
    def create_user(self):
        try:
            first_name = input("Enter first name: ")
            last_name = input("Enter last name: ")
            student_response = input("Is this a student? (Y/n): ").strip().lower()

            email_suffix = ".stu@223cos.net" if student_response != 'n' else "@223cos.net"
            email = first_name.lower() + "." + last_name.lower() + email_suffix

            while True:
                password = input('Enter password (12-100 characters, including numbers, uppercase and lowercase letters, and special characters): ')
                confirm_password = input('Confirm password: ')

                if password != confirm_password:
                    print("Passwords do not match, please try again.")
                    continue

                if self.validate_password(password):
                    break
                else:
                    print("Invalid password, please try again.")

            org_units = self.list_org_units()
            ou = ''
            if org_units:
                ou_choice = input("Select Organizational Unit by number (leave blank for default): ")
                if ou_choice.isdigit() and 0 < int(ou_choice) <= len(org_units):
                    ou = org_units[int(ou_choice) - 1]['orgUnitPath']
                elif ou_choice:
                    print("Invalid Organizational Unit selection.")
                    return

            user = {
                "name": {
                    "givenName": first_name,
                    "familyName": last_name
                },
                "primaryEmail": email,
                "password": password,
                "changePasswordAtNextLogin": True,
                "orgUnitPath": ou or '/',
                "includeInGlobalAddressList": True
            }

            self.service.users().insert(body=user).execute()
            print(f'User {email} created successfully.')

        except Exception as e:
            print(f'An error occurred: {e}')

    def bulk_users(self):
        try:
            csv_file = input("Enter the path to the CSV file: ")
            csv_file = os.path.abspath(csv_file)
            if not os.path.isfile(csv_file):
                print("File does not exist.")
                return

            student_response = input("Is this a student? (Y/n): ").strip().lower()
            email_suffix = ".stu@223cos.net" if student_response != 'n' else "@223cos.net"

            while True:
                password = input('Enter password: ')
                confirm_password = input('Confirm password: ')

                if password != confirm_password:
                    print("Passwords do not match, please try again.")
                    continue

                if self.validate_password(password):
                    break
                else:
                    print("Invalid password, please try again.")

            org_units = self.list_org_units()
            ou = ''
            if org_units:
                ou_choice = input("Select Organizational Unit by number (leave blank for default): ")
                if ou_choice.isdigit() and 0 < int(ou_choice) <= len(org_units):
                    ou = org_units[int(ou_choice) - 1]['orgUnitPath']
                elif ou_choice:
                    print("Invalid Organizational Unit selection.")
                    return

            with open(csv_file, 'r') as file:
                reader = csv.reader(file)
                next(reader)  # Skip header row

                for row in reader:
                    first_name, last_name  = row
                    email = first_name.lower() + "." + last_name.lower() + email_suffix
                    user = {
                        "name": {
                            "givenName": first_name,
                            "familyName": last_name
                        },
                        "primaryEmail": email,
                        "password": password,
                        "changePasswordAtNextLogin": True,
                        "orgUnitPath": ou,
                        "includeInGlobalAddressList": True
                    }

                    self.service.users().insert(body=user).execute()
                    print(f'User {email} created successfully.')
        
        except Exception as e:
              print(f'An error occurred: {e}')

    def bulk_delete(self):
        try:
            # List all OUs and allow the user to select one
            org_units = self.list_org_units()
            if not org_units:
                print("No organizational units available.")
                return

            ou_choice = input("Select Organizational Unit by number: ")
            if not ou_choice.isdigit() or not 0 < int(ou_choice) <= len(org_units):
                print("Invalid Organizational Unit selection.")
                return

            selected_ou = org_units[int(ou_choice) - 1]['orgUnitPath']

            # Query all users in the selected OU
            request = self.service.users().list(customer='my_customer', query=f'orgUnitPath={selected_ou}', orderBy='email')
            users = []
            while request is not None:
                results = request.execute()
                users.extend(results.get('users', []))
                request = self.service.users().list_next(previous_request=request, previous_response=results)

            if not users:
                print("No users found in the selected OU.")
                return

            # Display user emails
            for user in users:
                print(user['primaryEmail'])

            # Confirm deletion
            confirm = input("Are you sure you want to delete all users in this OU? (y/N): ").strip().lower()
            if confirm != 'y':
                print("Operation cancelled.")
                return

            # Delete all users in the OU
            for user in users:
                user_email = user['primaryEmail']
                self.service.users().delete(userKey=user_email).execute()
                print(f'User {user_email} deleted successfully.')

        except Exception as e:
            print(f'An error occurred: {e}')



        