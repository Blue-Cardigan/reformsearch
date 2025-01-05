import csv
import requests
import time
from pathlib import Path
from bs4 import BeautifulSoup

def get_csrf_token():
    """Get CSRF token and cookies from the main page"""
    session = requests.Session()
    
    # First get the page to get the cookies
    response = session.get('https://donate.reformparty.uk/branches')
    
    # The actual CSRF token is in the page content, not the cookie
    # Look for a meta tag with name="csrf-token"
    soup = BeautifulSoup(response.text, 'html.parser')
    csrf_meta = soup.find('meta', {'name': 'csrf-token'})
    
    if csrf_meta:
        csrf_token = csrf_meta.get('content')
        print(f"Found CSRF token: {csrf_token}")
        return session, csrf_token
    else:
        raise Exception("Could not find CSRF token in page")

def get_branch_info(session, csrf_token, address):
    url = 'https://donate.reformparty.uk/branches/find'
    headers = {
        'Content-Type': 'application/json',
        'X-CSRF-TOKEN': csrf_token,
        'Origin': 'https://donate.reformparty.uk',
        'Referer': 'https://donate.reformparty.uk/branches'
    }
    
    try:
        response = session.post(url, json={'address': address}, headers=headers)
        response.raise_for_status()
        return response.json()
    except Exception as e:
        print(f"Error fetching data for {address}: {str(e)}")
        if response.status_code == 419:
            print(f"Response content: {response.text}")
        return None

def write_branch_rows(writer, constituency, branch_data, is_primary=False):
    """Write a single branch to the CSV file"""
    if branch_data is None:
        # Write a row with empty values if no branch data
        row = {
            'constituency_searched': constituency,
            'branch_name': '',
            'constituency_name': '',
            'chair_name': '',
            'chair_email': '',
            'distance_km': '',
            'is_primary': is_primary
        }
    else:
        row = {
            'constituency_searched': constituency,
            'branch_name': branch_data.get('name', ''),
            'constituency_name': branch_data.get('constituency_name', ''),
            'chair_name': branch_data.get('chair_name', ''),
            'chair_email': branch_data.get('chair_email', ''),
            'distance_km': branch_data.get('distance_km', '') if not is_primary else '',
            'is_primary': is_primary
        }
    writer.writerow(row)

def main():
    # Get initial session and CSRF token
    session, csrf_token = get_csrf_token()
    
    # Read constituencies from CSV
    constituencies = []
    with open('data/constituencies.csv', 'r') as f:
        reader = csv.DictReader(f)
        constituencies = [row['name'] for row in reader]
    
    # Prepare CSV output
    fieldnames = [
        'constituency_searched',
        'branch_name',
        'constituency_name',
        'chair_name',
        'chair_email',
        'distance_km',
        'is_primary'
    ]
    
    # Create or append to CSV file
    file_exists = Path('branch_results.csv').exists()
    
    with open('branch_results.csv', 'a', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        
        # Write header only if file is new
        if not file_exists:
            writer.writeheader()
        
        # Process each constituency
        for constituency in constituencies:
            print(f"Processing: {constituency}")
            
            # Add ", UK" to make the search more accurate
            search_term = f"{constituency}, UK"
            
            # Get branch info
            branch_data = get_branch_info(session, csrf_token, search_term)
            
            # If we get a 419, try refreshing the token once
            if branch_data is None:
                print("Refreshing CSRF token...")
                session, csrf_token = get_csrf_token()
                branch_data = get_branch_info(session, csrf_token, search_term)
            
            # Write data even if branch_data is None
            if branch_data:
                # Write primary branch
                primary_branch = branch_data.get('primary_branch')
                write_branch_rows(writer, constituency, primary_branch, is_primary=True)
                
                # Write nearby branches
                for branch in branch_data.get('branches', []):
                    write_branch_rows(writer, constituency, branch, is_primary=False)
            else:
                # Write a row with empty values if no data was found
                write_branch_rows(writer, constituency, None, is_primary=False)
            
            # Be nice to the server
            time.sleep(1)

if __name__ == "__main__":
    main()