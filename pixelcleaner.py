#!/usr/bin/env python3
"""
PIXEL FORMAT CLEANER

This script cleans CSV files by:
- Removing duplicates based on FIRST_NAME + LAST_NAME
- Outputting in specific format: date, name, address, phones, emails
- Handling large files efficiently
"""

import csv
import re
import sys
from datetime import datetime
from collections import defaultdict
from typing import Dict, List, Set, Optional, Tuple


def clean_phone(phone: str) -> Optional[str]:
    """Clean and validate phone number."""
    if not phone or phone.lower() in ['null', 'undefined', 'nan', '']:
        return None
    
    # Remove all non-digit characters
    cleaned = re.sub(r'\D', '', str(phone))
    
    # Remove leading zeros
    cleaned = cleaned.lstrip('0')
    
    # Handle country codes
    if len(cleaned) > 10 and cleaned.startswith('1'):
        cleaned = cleaned[1:]
    if len(cleaned) > 10 and (cleaned.startswith('91') or cleaned.startswith('92')):
        cleaned = cleaned[2:]
    
    # Validate length
    if 7 <= len(cleaned) <= 15:
        return cleaned
    return None


def clean_email(email: str) -> Optional[str]:
    """Clean and validate email address."""
    if not email:
        return None
    
    email = str(email).strip().lower()
    
    if '@' in email and '.' in email and len(email) > 5:
        return email
    return None


def extract_multiple(value: str) -> List[str]:
    """Extract multiple values separated by comma, semicolon, pipe, or newline."""
    if not value:
        return []
    
    values = re.split(r'[,;|\n\r]+', str(value))
    cleaned_values = [v.strip() for v in values if v.strip() and v.strip().lower() not in ['null', 'undefined', 'nan']]
    return cleaned_values


def clean_value(value: str) -> str:
    """Clean a general value by trimming and replacing commas with spaces."""
    if not value:
        return ''
    return str(value).strip().replace(',', ' ')


def is_personal_email(email: str) -> bool:
    """Check if email is personal (gmail, yahoo, hotmail, outlook, etc.)."""
    personal_domains = ['gmail.com', 'yahoo.com', 'hotmail.com', 'outlook.com', 
                       'aol.com', 'icloud.com', 'me.com', 'mac.com', 'msn.com',
                       'live.com', 'protonmail.com', 'mail.com', 'zoho.com']
    email_lower = email.lower()
    return any(domain in email_lower for domain in personal_domains)


def parse_timestamp(timestamp: str) -> Optional[datetime]:
    """Parse timestamp string to datetime object."""
    if not timestamp:
        return None
    
    try:
        # Try ISO format (2026-01-21T10:57:56Z)
        if 'T' in timestamp:
            # Remove 'Z' if present and parse
            timestamp_clean = timestamp.replace('Z', '+00:00')
            if timestamp_clean.endswith('+00:00'):
                return datetime.fromisoformat(timestamp_clean)
            # Try without timezone
            timestamp_clean = timestamp.split('Z')[0]
            return datetime.fromisoformat(timestamp_clean)
        return None
    except:
        return None


def calculate_estimated_time_spent(timestamps: List[datetime]) -> str:
    """
    Event-Density Model: Estimate time spent based on number of pixel events.
    
    Simple mapping based on event count:
    - 1-2 events → 30-90 seconds
    - 3-5 events → 2-4 minutes
    - 6-10 events → 5-8 minutes
    - 10+ events → 10-15 minutes
    """
    if not timestamps:
        return ''
    
    num_events = len(timestamps)
    
    try:
        # Map event count to estimated time range
        if num_events == 1:
            # Single event: 30 seconds
            estimated_seconds = 30
        elif num_events == 2:
            # 2 events: 60 seconds (middle of 30-90 range)
            estimated_seconds = 60
        elif num_events <= 5:
            # 3-5 events: 3 minutes (middle of 2-4 range)
            estimated_seconds = 3 * 60
        elif num_events <= 10:
            # 6-10 events: 6.5 minutes (middle of 5-8 range)
            estimated_seconds = 6.5 * 60
        else:
            # 10+ events: 12.5 minutes (middle of 10-15 range)
            estimated_seconds = 12.5 * 60
        
        # Format output
        if estimated_seconds < 60:
            return f"{int(estimated_seconds)} seconds"
        elif estimated_seconds < 3600:
            minutes = int(estimated_seconds / 60)
            seconds = int(estimated_seconds % 60)
            if seconds > 0:
                return f"{minutes} minutes {seconds} seconds"
            else:
                return f"{minutes} minutes"
        else:
            hours = int(estimated_seconds / 3600)
            minutes = int((estimated_seconds % 3600) / 60)
            return f"{hours} hours {minutes} minutes"
    except Exception as e:
        return ''


def extract_date_from_timestamp(timestamp: str) -> str:
    """Extract date (YYYY-MM-DD) from ActivityStartDate timestamp."""
    if not timestamp:
        return ''
    
    try:
        # Try ISO format first (2025-09-29T17:59:07Z)
        if 'T' in timestamp:
            date_part = timestamp.split('T')[0]
            # Validate date format
            datetime.strptime(date_part, '%Y-%m-%d')
            return date_part
        # Try other formats if needed
        return timestamp.split()[0] if timestamp else ''
    except:
        return timestamp.split()[0] if timestamp else ''


def get_interest_level(occurrence_count: int) -> str:
    """Determine interest level based on occurrence count."""
    if occurrence_count > 4:
        return 'Highly Interested'
    elif occurrence_count >= 2:
        return 'Medium'
    else:
        return 'Not Interested'


def process_csv(input_file: str, output_file: str):
    """Process CSV file and generate cleaned output."""
    print('🟢 PIXEL CLEANER ACTIVATED')
    
    # Dictionary to store person data keyed by FIRST_NAME|LAST_NAME
    people_map: Dict[str, Dict] = defaultdict(lambda: {
        'FIRST_NAME': '',
        'LAST_NAME': '',
        'DATE': '',
        'ADDRESS': '',
        'CITY': '',
        'STATE': '',
        'ZIP': '',
        'direct_phones': [],  # All phones from DIRECT_NUMBER field
        'mobile_phones': [],  # All phones from MOBILE_PHONE field
        'personal_phones': [],  # All phones from PERSONAL_PHONE field
        'direct_dnc_flags': [],  # DNC flags for direct phones
        'personal_email': '',
        'business_email': '',
        'linkedin_url': '',  # LinkedIn URL
        'occurrence_count': 0,  # Count of duplicate occurrences
        'timestamps': [],  # All timestamps for event-density calculation
    })
    
    # Read and process input CSV
    print(f'📥 Reading input file: {input_file}')
    row_count = 0
    
    with open(input_file, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        fieldnames = reader.fieldnames
        
        if not fieldnames:
            print('❌ Error: Input file has no headers')
            return
        
        print(f'📋 Found {len(fieldnames)} columns')
        
        for row in reader:
            row_count += 1
            if row_count % 1000 == 0:
                print(f'   Processed {row_count} rows...')
            
            first_name = clean_value(row.get('FIRST_NAME', '')).upper()
            last_name = clean_value(row.get('LAST_NAME', '')).upper()
            
            if not first_name or not last_name:
                continue
            
            key = f"{first_name}|{last_name}"
            person = people_map[key]
            
            # Increment occurrence count
            person['occurrence_count'] += 1
            
            # Store names
            if not person['FIRST_NAME']:
                person['FIRST_NAME'] = row.get('FIRST_NAME', '')
                person['LAST_NAME'] = row.get('LAST_NAME', '')
            
            # Extract date from ActivityStartDate (first occurrence)
            if not person['DATE']:
                activity_date = row.get('ACTIVITY_START_DATE', '') or row.get('ActivityStartDate', '')
                if activity_date:
                    person['DATE'] = extract_date_from_timestamp(activity_date)
            
            # Track timestamps for event-density model
            timestamp_str = row.get('ACTIVITY_START_DATE', '') or row.get('EVENT_TIMESTAMP', '')
            if timestamp_str:
                timestamp = parse_timestamp(timestamp_str)
                if timestamp:
                    person['timestamps'].append(timestamp)
            
            # Extract LinkedIn URL (first occurrence)
            if not person['linkedin_url']:
                linkedin = row.get('LINKEDIN_URL', '').strip()
                if linkedin:
                    person['linkedin_url'] = linkedin
            
            # Extract address fields (first occurrence)
            if not person['ADDRESS']:
                person['ADDRESS'] = clean_value(row.get('PERSONAL_ADDRESS', ''))
            if not person['CITY']:
                person['CITY'] = clean_value(row.get('PERSONAL_CITY', ''))
            if not person['STATE']:
                person['STATE'] = clean_value(row.get('PERSONAL_STATE', ''))
            if not person['ZIP']:
                person['ZIP'] = clean_value(row.get('PERSONAL_ZIP', ''))
            
            # Collect all phones from DIRECT_NUMBER field
            direct_number = row.get('DIRECT_NUMBER', '')
            if direct_number:
                phones = extract_multiple(direct_number)
                direct_dnc = row.get('DIRECT_NUMBER_DNC', '').strip().upper()
                dnc_flags = extract_multiple(direct_dnc) if direct_dnc else []
                for i, phone_str in enumerate(phones):
                    cleaned_phone = clean_phone(phone_str)
                    if cleaned_phone and cleaned_phone not in person['direct_phones']:
                        person['direct_phones'].append(cleaned_phone)
                        # Store corresponding DNC flag
                        dnc_flag = dnc_flags[i].upper() if i < len(dnc_flags) else ''
                        person['direct_dnc_flags'].append(dnc_flag)
            
            # Collect all phones from MOBILE_PHONE field
            mobile_number = row.get('MOBILE_PHONE', '')
            if mobile_number:
                phones = extract_multiple(mobile_number)
                for phone_str in phones:
                    cleaned_phone = clean_phone(phone_str)
                    if cleaned_phone and cleaned_phone not in person['mobile_phones']:
                        person['mobile_phones'].append(cleaned_phone)
            
            # Collect all phones from PERSONAL_PHONE field
            personal_number = row.get('PERSONAL_PHONE', '')
            if personal_number:
                phones = extract_multiple(personal_number)
                for phone_str in phones:
                    cleaned_phone = clean_phone(phone_str)
                    if cleaned_phone and cleaned_phone not in person['personal_phones']:
                        person['personal_phones'].append(cleaned_phone)
            
            # Extract emails - separate personal and business
            if not person['personal_email'] or not person['business_email']:
                # Check BUSINESS_EMAIL
                business_email_val = row.get('BUSINESS_EMAIL', '')
                if business_email_val and not person['business_email']:
                    emails = extract_multiple(business_email_val)
                    for email_str in emails:
                        cleaned_email = clean_email(email_str)
                        if cleaned_email:
                            person['business_email'] = cleaned_email
                            break
                
                # Check PERSONAL_EMAILS
                personal_emails_val = row.get('PERSONAL_EMAILS', '')
                if personal_emails_val:
                    emails = extract_multiple(personal_emails_val)
                    for email_str in emails:
                        cleaned_email = clean_email(email_str)
                        if cleaned_email:
                            if is_personal_email(cleaned_email):
                                if not person['personal_email']:
                                    person['personal_email'] = cleaned_email
                            else:
                                if not person['business_email']:
                                    person['business_email'] = cleaned_email
                
                # Also check BUSINESS_VERIFIED_EMAILS
                if not person['business_email']:
                    business_verified = row.get('BUSINESS_VERIFIED_EMAILS', '')
                    if business_verified:
                        emails = extract_multiple(business_verified)
                        for email_str in emails:
                            cleaned_email = clean_email(email_str)
                            if cleaned_email and not is_personal_email(cleaned_email):
                                person['business_email'] = cleaned_email
                                break
    
    print(f'✅ Processed {row_count} input rows')
    print(f'📊 Found {len(people_map)} unique people')
    
    # Prepare output rows in exact format requested
    output_rows = []
    
    for key, person in people_map.items():
        # Select direct phone (first from DIRECT_NUMBER)
        direct_phone = person['direct_phones'][0] if person['direct_phones'] else ''
        phone_dnc = person['direct_dnc_flags'][0] if person['direct_dnc_flags'] else ''
        
        # Select mobile phone - prefer different from direct phone
        mobile_phone = ''
        if person['mobile_phones']:
            for phone in person['mobile_phones']:
                if phone != direct_phone:
                    mobile_phone = phone
                    break
            # If no different phone found, use first mobile phone
            if not mobile_phone:
                mobile_phone = person['mobile_phones'][0]
        
        # Select personal phone - prefer different from both direct and mobile
        personal_phone = ''
        if person['personal_phones']:
            for phone in person['personal_phones']:
                if phone != direct_phone and phone != mobile_phone:
                    personal_phone = phone
                    break
            # If no different phone found, use first personal phone
            if not personal_phone:
                personal_phone = person['personal_phones'][0]
        
        # Get interest level
        interest_level = get_interest_level(person['occurrence_count'])
        
        # Calculate estimated time spent using event-density model
        estimated_time = calculate_estimated_time_spent(person['timestamps'])
        
        output_row = {
            'Date': person['DATE'],
            'First Name': person['FIRST_NAME'],
            'Last Name': person['LAST_NAME'],
            'Address': person['ADDRESS'],
            'City': person['CITY'],
            'State': person['STATE'],
            'Zip': person['ZIP'],
            'Direct Phone': direct_phone,
            'Mobile Phone': mobile_phone,
            'Personal Phone': personal_phone,
            'Personal Email': person['personal_email'] or '',
            'Business Email': person['business_email'] or '',
            'LinkedIn URL': person['linkedin_url'] or '',
            'Duplicate Occurrences': str(person['occurrence_count']),
            'Estimated Time Spent': estimated_time,
            'Interest Level': interest_level,
        }
        
        output_rows.append(output_row)
    
    # Write output CSV in exact order
    fieldnames_output = [
        'Date',
        'First Name',
        'Last Name',
        'Address',
        'City',
        'State',
        'Zip',
        'Direct Phone',
        'Mobile Phone',
        'Personal Phone',
        'Personal Email',
        'Business Email',
        'LinkedIn URL',
        'Duplicate Occurrences',
        'Estimated Time Spent',
        'Interest Level'
    ]
    
    print(f'💾 Writing output file: {output_file}')
    
    if not output_rows:
        print('⚠️  Warning: No output rows to write')
        return
    
    with open(output_file, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames_output, extrasaction='ignore')
        writer.writeheader()
        writer.writerows(output_rows)
    
    print(f'✅ PIXEL: Returning {len(output_rows)} cleaned rows')
    print(f'🎉 Done! Output written to {output_file}')


def main():
    """Main entry point."""
    if len(sys.argv) < 3:
        print('Usage: python pixelcleaner.py <input_csv> <output_csv>')
        print('Example: python pixelcleaner.py "pixel_export of fix&flow.csv" "cleaned_output.csv"')
        sys.exit(1)
    
    input_file = sys.argv[1]
    output_file = sys.argv[2]
    
    try:
        process_csv(input_file, output_file)
    except Exception as e:
        print(f'❌ Error: {e}')
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == '__main__':
    main()
