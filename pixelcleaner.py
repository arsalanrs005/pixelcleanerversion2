#!/usr/bin/env python3
"""
PIXEL FORMAT CLEANER

This script cleans CSV files by:
- Removing duplicates based on FIRST_NAME + LAST_NAME
- Picking the first email and phone number
- Filtering phones based on DNC (Y/N) flags (keeping only N)
- Creating PHONE_DNC columns for kept phones
- Removing original DNC columns from output
- Handling large files efficiently
"""

import csv
import re
import sys
from collections import defaultdict, OrderedDict
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


def is_phone_field(field_name: str) -> bool:
    """Check if field name indicates a phone number field (but not DNC)."""
    field_upper = field_name.upper()
    if 'DNC' in field_upper:
        return False
    return any(keyword in field_upper for keyword in ['PHONE', 'MOBILE', 'CELL', 'NUMBER'])


def is_email_field(field_name: str) -> bool:
    """Check if field name indicates an email field."""
    field_upper = field_name.upper()
    return ('EMAIL' in field_upper or 'MAIL' in field_upper) and 'SHA' not in field_upper


def is_dnc_field(field_name: str) -> bool:
    """Check if field name indicates a DNC (Do Not Contact) flag field."""
    field_upper = field_name.upper()
    return 'DNC' in field_upper


def should_skip_field(field_name: str) -> bool:
    """Check if field should be skipped."""
    field_upper = field_name.upper()
    return 'SHA256' in field_upper or field_name == '__FILE_TYPE'


def get_dnc_field_for_phone_field(phone_field: str, fieldnames: List[str]) -> Optional[str]:
    """Find the corresponding DNC field for a phone field."""
    phone_upper = phone_field.upper()
    
    # Try exact match first (e.g., DIRECT_NUMBER -> DIRECT_NUMBER_DNC)
    dnc_field = phone_field + '_DNC'
    if dnc_field in fieldnames:
        return dnc_field
    
    # Try prefix match (e.g., MOBILE_PHONE -> MOBILE_PHONE_DNC)
    for field in fieldnames:
        if is_dnc_field(field):
            # Check if this DNC field corresponds to the phone field
            dnc_base = field.replace('_DNC', '').replace('DNC_', '').upper()
            if dnc_base in phone_upper or phone_upper in dnc_base:
                return field
    
    return None


def filter_phones_with_dnc(phone_dnc_pairs: List[Tuple[str, str]]) -> List[Tuple[str, str]]:
    """Filter phones to keep only those with DNC flag 'N'. Returns list of (phone, dnc_flag) tuples."""
    filtered = []
    for phone, dnc_flag in phone_dnc_pairs:
        flag = (dnc_flag or "").upper()
        if flag == "N" or not flag:
            filtered.append((phone, "N" if flag == "N" else ""))
    return filtered


def process_csv(input_file: str, output_file: str):
    """Process CSV file and generate cleaned output."""
    print('🟢 PIXEL CLEANER ACTIVATED')
    
    # Dictionary to store person data keyed by FIRST_NAME|LAST_NAME
    people_map: Dict[str, Dict] = defaultdict(lambda: {
        'FIRST_NAME': '',
        'LAST_NAME': '',
        'phone_dnc_pairs': [],  # List of (phone, dnc_flag) tuples, preserving order
        'emails': set(),
        'other_data': {}
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
            
            # Collect phones with their DNC flags by matching field pairs
            phone_dnc_pairs_for_row = []
            
            for field in fieldnames:
                if is_phone_field(field):
                    phone_value = row.get(field, '')
                    if phone_value:
                        phones = extract_multiple(phone_value)
                        
                        # Find corresponding DNC field
                        dnc_field = get_dnc_field_for_phone_field(field, fieldnames)
                        dnc_value = row.get(dnc_field, '') if dnc_field else ''
                        dnc_flags = extract_multiple(dnc_value) if dnc_value else []
                        
                        # Match phones with DNC flags by position
                        for i, phone_str in enumerate(phones):
                            cleaned_phone = clean_phone(phone_str)
                            if cleaned_phone:
                                dnc_flag = dnc_flags[i].upper() if i < len(dnc_flags) else ''
                                phone_dnc_pairs_for_row.append((cleaned_phone, dnc_flag))
            
            # Also check SKIPTRACE fields
            skiptrace_wireless = row.get('SKIPTRACE_WIRELESS_NUMBERS', '')
            skiptrace_dnc = row.get('SKIPTRACE_DNC', '').strip().upper()
            if skiptrace_wireless:
                phones = extract_multiple(skiptrace_wireless)
                for phone_str in phones:
                    cleaned_phone = clean_phone(phone_str)
                    if cleaned_phone:
                        phone_dnc_pairs_for_row.append((cleaned_phone, skiptrace_dnc))
            
            # Add all phone-DNC pairs (avoid duplicates based on phone number)
            seen_phones = {p[0] for p in person['phone_dnc_pairs']}
            for phone, dnc_flag in phone_dnc_pairs_for_row:
                if phone not in seen_phones:
                    person['phone_dnc_pairs'].append((phone, dnc_flag))
                    seen_phones.add(phone)
            
            # Handle email fields - only first email
            for field in fieldnames:
                if should_skip_field(field):
                    continue
                
                if is_email_field(field):
                    if len(person['emails']) == 0:
                        value = row.get(field, '')
                        if value:
                            for email_str in extract_multiple(value):
                                cleaned_email = clean_email(email_str)
                                if cleaned_email:
                                    person['emails'].add(cleaned_email)
                                    break  # Only first email
            
            # Store other fields (first occurrence, excluding DNC columns)
            for field in fieldnames:
                if should_skip_field(field):
                    continue
                
                if field in ['FIRST_NAME', 'LAST_NAME']:
                    continue
                
                if is_dnc_field(field):
                    continue  # Skip DNC columns - we'll create new ones
                
                if is_phone_field(field) or is_email_field(field):
                    continue  # Already processed
                
                if field not in person['other_data']:
                    value = row.get(field, '')
                    if value:
                        cleaned = clean_value(value)
                        if cleaned:
                            person['other_data'][field] = cleaned
    
    print(f'✅ Processed {row_count} input rows')
    print(f'📊 Found {len(people_map)} unique people')
    
    # Filter phones based on DNC flags and prepare output
    output_rows = []
    
    for key, person in people_map.items():
        # Filter: keep only phones with DNC='N' or no DNC flag
        filtered_pairs = filter_phones_with_dnc(person['phone_dnc_pairs'])
        
        # Remove duplicate phones while preserving order
        seen_phones = set()
        unique_pairs = []
        for phone, dnc_flag in filtered_pairs:
            if phone not in seen_phones:
                seen_phones.add(phone)
                unique_pairs.append((phone, dnc_flag))
        
        # Build output row
        output_row = {
            'FIRST_NAME': person['FIRST_NAME'],
            'LAST_NAME': person['LAST_NAME'],
        }
        
        # Add phones
        if unique_pairs:
            output_row['PRIMARY_PHONE'] = unique_pairs[0][0]
            for i in range(1, min(len(unique_pairs), 200)):  # Support up to PHONE_200
                output_row[f'PHONE_{i}'] = unique_pairs[i][0]
        else:
            output_row['PRIMARY_PHONE'] = ''
        
        # Add only the first phone DNC flag (one column)
        if unique_pairs and unique_pairs[0][1]:
            output_row['PHONE_DNC'] = unique_pairs[0][1]
        
        # Add emails
        emails_list = list(person['emails'])
        output_row['PRIMARY_EMAIL'] = emails_list[0] if emails_list else ''
        
        # Add additional emails
        for i, email in enumerate(emails_list[1:6]):  # EMAIL_1 through EMAIL_5
            output_row[f'EMAIL_{i + 1}'] = email
        
        # Add other fields
        for field, value in person['other_data'].items():
            output_row[field] = value
        
        output_rows.append(output_row)
    
    # Write output CSV
    print(f'💾 Writing output file: {output_file}')
    
    if not output_rows:
        print('⚠️  Warning: No output rows to write')
        return
    
    # Get all unique field names from output rows
    all_fields = set()
    all_fields.update(['FIRST_NAME', 'LAST_NAME', 'PRIMARY_PHONE', 'PRIMARY_EMAIL'])
    
    for row in output_rows:
        all_fields.update(row.keys())
    
    # Sort fields: put standard fields first, then others
    standard_fields = ['FIRST_NAME', 'LAST_NAME', 'PRIMARY_PHONE', 'PRIMARY_EMAIL']
    email_fields = sorted([f for f in all_fields if f.startswith('EMAIL_')])
    phone_fields = sorted([f for f in all_fields if f.startswith('PHONE_') and not f.startswith('PHONE_DNC')])
    dnc_field = ['PHONE_DNC'] if 'PHONE_DNC' in all_fields else []
    other_fields = sorted([f for f in all_fields if f not in standard_fields + email_fields + phone_fields + dnc_field])
    
    # Order: standard, emails, phones, DNC field, others
    fieldnames_output = standard_fields + email_fields + phone_fields + dnc_field + other_fields
    
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
