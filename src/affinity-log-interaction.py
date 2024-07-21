import requests
import json
import argparse
import sys

BASE_URL = 'https://api.affinity.co'

def find_person_by_name(api_key, name):
    search_endpoint = f'{BASE_URL}/persons'
    headers = {
        'Authorization': f'Bearer {api_key}',
        'Content-Type': 'application/json'
    }
    params = {
        'query': name
    }
    response = requests.get(search_endpoint, headers=headers, params=params)
    if response.status_code == 200:
        return response.json()
    else:
        print('Failed to search for person.')
        print('Status code:', response.status_code)
        print('Response:', response.json())
        sys.exit(1)

def find_person_by_email(api_key, email):
    search_endpoint = f'{BASE_URL}/persons'
    headers = {
        'Authorization': f'Bearer {api_key}',
        'Content-Type': 'application/json'
    }
    params = {
        'query': email
    }
    response = requests.get(search_endpoint, headers=headers, params=params)
    if response.status_code == 200:
        return response.json()
    else:
        print('Failed to search for person.')
        print('Status code:', response.status_code)
        print('Response:', response.json())
        sys.exit(1)

def find_user_by_email(api_key, email):
    users_endpoint = f'{BASE_URL}/users'
    headers = {
        'Authorization': f'Bearer {api_key}',
        'Content-Type': 'application/json'
    }
    params = {
        'email': email
    }
    response = requests.get(users_endpoint, headers=headers, params=params)
    if response.status_code == 200:
        users = response.json()
        for user in users:
            if user['email'] == email:
                return user['id']
        print('No user found with the given email.')
        sys.exit(1)
    else:
        print('Failed to search for user.')
        print('Status code:', response.status_code)
        print('Response:', response.json())
        sys.exit(1)

def affinity_log_interaction(api_key, interaction_data):
    interactions_endpoint = f'{BASE_URL}/interactions'
    headers = {
        'Authorization': f'Bearer {api_key}',
        'Content-Type': 'application/json'
    }
    response = requests.post(interactions_endpoint, headers=headers, data=json.dumps(interaction_data))
    if response.status_code == 201:
        print('Interaction logged successfully.')
        print('Response:', response.json())
    else:
        print('Failed to log interaction.')
        print('Status code:', response.status_code)
        print('Response:', response.json())

def get_person_ids(api_key, identifiers):
    person_ids = []
    for identifier in identifiers:
        if '@' in identifier:
            persons = find_person_by_email(api_key, identifier)
        else:
            persons = find_person_by_name(api_key, identifier)
        if not persons:
            print(f'No persons found with the name/email {identifier}.')
            sys.exit(1)
        elif len(persons) > 1:
            print(f'Multiple persons found for {identifier}:')
            for i, person in enumerate(persons):
                print(f'{i+1}: {person["first_name"]} {person["last_name"]} - {person.get("title", "No title")} - {person.get("organization_name", "No organization")}')
            choice = int(input(f'Select the person by number for {identifier}: ')) - 1
            if choice < 0 or choice >= len(persons):
                print('Invalid selection.')
                sys.exit(1)
            person_ids.append(persons[choice]['id'])
        else:
            person_ids.append(persons[0]['id'])
    return person_ids

def main():
    parser = argparse.ArgumentParser(description='Log an interaction with a person in Affinity CRM.')
    parser.add_argument('--api_key', type=str, required=True, help='Affinity API key')
    parser.add_argument('main_user', type=str, help='Name or email of the main user')
    parser.add_argument('--team_member_email', type=str, required=True, help='Email of the team member interacting')
    parser.add_argument('--type', type=str, required=True, choices=['meeting', 'call', 'message'], help='Type of interaction (meeting, call, message)')
    parser.add_argument('--date', type=str, required=True, help='Date of interaction (ISO 8601 format)')
    parser.add_argument('--content', type=str, required=True, help='Content of the interaction')
    parser.add_argument('--also_add_to', type=str, nargs='*', help='Names or emails of additional persons to include in the interaction')

    # Specific parameters for each interaction type
    parser.add_argument('--meeting_location', type=str, help='Location of the meeting')
    parser.add_argument('--meeting_type', type=str, choices=['f2f', 'virtual'], help='Type of meeting (f2f, virtual)')
    parser.add_argument('--meeting_virtual_platform', type=str, choices=['zoom', 'google_meet', 'microsoft_teams'], help='Platform for virtual meeting')
    
    parser.add_argument('--message_medium', type=str, choices=['text', 'messenger', 'whatsapp', 'telegram'], help='Medium for message interaction')
    parser.add_argument('--message_direction', type=int, choices=[0, 1], help='Direction of the chat message (only applies to messages)')

    args = parser.parse_args()

    api_key = args.api_key

    # Determine if the main user is specified by name or email
    if '@' in args.main_user:
        persons = find_person_by_email(api_key, args.main_user)
    else:
        persons = find_person_by_name(api_key, args.main_user)

    if not persons:
        print('No persons found with the given name/email.')
        sys.exit(1)

    if len(persons) > 1:
        print('Multiple persons found:')
        for i, person in enumerate(persons):
            print(f'{i+1}: {person["first_name"]} {person["last_name"]} - {person.get("title", "No title")} - {person.get("organization_name", "No organization")}')
        choice = int(input('Select the person by number: ')) - 1
        if choice < 0 or choice >= len(persons):
            print('Invalid selection.')
            sys.exit(1)
        main_person_id = persons[choice]['id']
    else:
        main_person_id = persons[0]['id']

    # Find user by email
    user_id = find_user_by_email(api_key, args.team_member_email)

    # Find or validate additional persons
    additional_person_ids = get_person_ids(api_key, args.also_add_to or [])

    # Combine all person IDs
    person_ids = [main_person_id] + additional_person_ids

    # Map interaction type to Affinity type
    interaction_type_map = {
        'meeting': 0,
        'call': 1,
        'message': 2
    }
    interaction_type = interaction_type_map[args.type]

    # Prepare interaction data
    interaction_data = {
        'person_ids': person_ids,
        'type': interaction_type,
        'date': args.date,
        'content': args.content
    }

    # Include additional parameters based on interaction type
    if args.type == 'meeting':
        interaction_data['location'] = args.meeting_location
        interaction_data['meeting_type'] = args.meeting_type
        if args.meeting_type == 'virtual':
            interaction_data['virtual_platform'] = args.meeting_virtual_platform

    if args.type == 'message':
        interaction_data['medium'] = args.message_medium
        if args.message_direction is not None:
            interaction_data['direction'] = args.message_direction

    affinity_log_interaction(api_key, interaction_data)

if __name__ == '__main__':
    main()
