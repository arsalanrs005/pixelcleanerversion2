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
        'direct_phone': '',  # From DIRECT_NUMBER - empty string if not found
        'mobile_phone': '',  # From MOBILE_PHONE - empty string if not found
        'personal_phone': '',  # From PERSONAL_PHONE - empty string if not found
        'personal_email': '',
        'business_email': '',
        'phone_dnc': '',  # DNC value for direct phone
        'found_direct': False,  # Track if we've found direct phone
        'found_mobile': False,  # Track if we've found mobile phone
        'found_personal': False,  # Track if we've found personal phone
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
            
            # Store names
            if not person['FIRST_NAME']:
                person['FIRST_NAME'] = row.get('FIRST_NAME', '')
                person['LAST_NAME'] = row.get('LAST_NAME', '')
            
            # Extract date from ActivityStartDate (first occurrence)
            if not person['DATE']:
                activity_date = row.get('ActivityStartDate', '')
                if activity_date:
                    person['DATE'] = extract_date_from_timestamp(activity_date)
            
            # Extract address fields (first occurrence)
            if not person['ADDRESS']:
                person['ADDRESS'] = clean_value(row.get('PERSONAL_ADDRESS', ''))
            if not person['CITY']:
                person['CITY'] = clean_value(row.get('PERSONAL_CITY', ''))
            if not person['STATE']:
                person['STATE'] = clean_value(row.get('PERSONAL_STATE', ''))
            if not person['ZIP']:
                person['ZIP'] = clean_value(row.get('PERSONAL_ZIP', ''))
            
            # Extract DIRECT_NUMBER (direct phone) - ONLY from DIRECT_NUMBER field
            if not person['found_direct']:
                direct_number = row.get('DIRECT_NUMBER', '')
                if direct_number:
                    phones = extract_multiple(direct_number)
                    for phone_str in phones:
                        cleaned_phone = clean_phone(phone_str)
                        if cleaned_phone:
                            person['direct_phone'] = cleaned_phone
                            person['found_direct'] = True
                            # Get DNC value for direct phone
                            direct_dnc = row.get('DIRECT_NUMBER_DNC', '').strip().upper()
                            if direct_dnc:
                                dnc_flags = extract_multiple(direct_dnc)
                                if dnc_flags:
                                    person['phone_dnc'] = dnc_flags[0]
                            break
            
            # Extract MOBILE_PHONE - ONLY from MOBILE_PHONE field
            if not person['found_mobile']:
                mobile_number = row.get('MOBILE_PHONE', '')
                if mobile_number:
                    phones = extract_multiple(mobile_number)
                    for phone_str in phones:
                        cleaned_phone = clean_phone(phone_str)
                        if cleaned_phone:
                            person['mobile_phone'] = cleaned_phone
                            person['found_mobile'] = True
                            break
            
            # Extract PERSONAL_PHONE - ONLY from PERSONAL_PHONE field
            if not person['found_personal']:
                personal_number = row.get('PERSONAL_PHONE', '')
                if personal_number:
                    phones = extract_multiple(personal_number)
                    for phone_str in phones:
                        cleaned_phone = clean_phone(phone_str)
                        if cleaned_phone:
                            person['personal_phone'] = cleaned_phone
                            person['found_personal'] = True
                            break
            
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
        output_row = {
            'Date': person['DATE'],
            'First Name': person['FIRST_NAME'],
            'Last Name': person['LAST_NAME'],
            'Address': person['ADDRESS'],
            'City': person['CITY'],
            'State': person['STATE'],
            'Zip': person['ZIP'],
            'Direct Phone': person['direct_phone'] or '',
            'Mobile Phone': person['mobile_phone'] or '',
            'Personal Phone': person['personal_phone'] or '',
            'Personal Email': person['personal_email'] or '',
            'Business Email': person['business_email'] or '',
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
        'Business Email'
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
