"""
LDIF to JSON Converter

A comprehensive tool for converting LDAP Data Interchange Format (LDIF) files to JSON format
with support for hierarchical nesting and optional Base64 attribute decoding.
"""

import argparse
import base64
import json
import sys
from collections import defaultdict


def parse_ldif(input_data, decode_base64=False):
    """Parse LDIF data into structured dictionaries with optional Base64 decoding.
    
    Args:
        input_data: An iterable (file object or list) containing LDIF data
        decode_base64: If True, decodes Base64-encoded attributes (marked with ::)
        
    Returns:
        list: List of dictionaries where each represents an LDIF entry.
              Multivalued attributes become arrays.
              Base64 handling depends on decode_base64 parameter.
              
    Raises:
        UnicodeDecodeError: If Base64 decoding fails (only when decode_base64=True)
    """
    entries = []
    current_entry = defaultdict(list)
    
    for line in input_data:
        line = line.strip()
        
        # Skip empty lines and comments
        if not line or line.startswith('#'):
            continue
            
        # Start new entry when DN is encountered
        if (line.startswith('dn:') or line.startswith('dn::')) and current_entry:
            entries.append({k: v[0] if len(v) == 1 else v 
                          for k, v in current_entry.items()})
            current_entry = defaultdict(list)
            
        # Handle DN specially to ensure it's always present
        if line.startswith('dn::'):
            _, value = line.split('dn::', 1)
            current_entry['dn'].append(
                base64.b64decode(value.strip()).decode('utf-8') if decode_base64 
                else value.strip()
            )
        elif line.startswith('dn:'):
            _, value = line.split('dn:', 1)
            current_entry['dn'].append(value.strip())
            
        # Handle regular attributes
        elif ':: ' in line:
            attr, value = line.split(':: ', 1)
            if decode_base64:
                try:
                    decoded = base64.b64decode(value.strip()).decode('utf-8')
                    current_entry[attr].append(decoded)
                except (base64.binascii.Error, UnicodeDecodeError):
                    current_entry[attr].append(f":: {value.strip()}")  # Mark failed decode
            else:
                current_entry[attr].append(f":: {value.strip()}")  # Preserve Base64 marker
                
        elif ': ' in line:
            attr, value = line.split(': ', 1)
            current_entry[attr].append(value.strip())
    
    # Add final entry if input doesn't end with newline
    if current_entry:
        entries.append({k: v[0] if len(v) == 1 else v 
                      for k, v in current_entry.items()})
    
    return entries


def nest_entries(entries, parent_attribute='subEntries'):
    """Organize LDIF entries into a hierarchical structure based on DN relationships.
    
    Args:
        entries: List of parsed LDIF entry dictionaries
        parent_attribute: Attribute name to store child entries (default: 'subEntries')
        
    Returns:
        list: Root-level entries with nested children under specified parent_attribute
        
    Note:
        The hierarchy is determined by Distinguished Name (DN) components.
        For example: "ou=people,dc=example" becomes child of "dc=example"
    """
    entries_by_dn = {entry['dn']: entry for entry in entries if 'dn' in entry}
    # Process from most specific (longest) to most general (shortest) DN
    sorted_dns = sorted(entries_by_dn.keys(), 
                       key=lambda x: len(x.split(',')), 
                       reverse=True)
    
    for dn in sorted_dns:
        entry = entries_by_dn[dn]
        parent_dn = ','.join(dn.split(',')[1:])  # Get parent by removing first RDN
        
        if parent_dn in entries_by_dn:
            parent_entry = entries_by_dn[parent_dn]
            if parent_attribute not in parent_entry:
                parent_entry[parent_attribute] = []
            parent_entry[parent_attribute].append(entry)
    
    return [entry for dn, entry in entries_by_dn.items() 
            if not any(dn.endswith(','+parent) 
                     for parent in entries_by_dn.keys() 
                     if parent != dn)]


def main():
    """Command-line interface for LDIF to JSON conversion with configurable processing."""
    parser = argparse.ArgumentParser(
        description='Convert LDIF to JSON with optional Base64 decoding and nesting',
        formatter_class=argparse.ArgumentDefaultsHelpFormatter
    )
    
    # Input/output configuration
    parser.add_argument(
        'input_file',
        nargs='?',
        type=argparse.FileType('r'),
        default=sys.stdin,
        help='Input LDIF file (use "-" for stdin)'
    )
    parser.add_argument(
        '-o', '--output',
        type=argparse.FileType('w'),
        default=sys.stdout,
        help='Output JSON file (default: stdout)'
    )
    
    # Processing options
    parser.add_argument(
        '-i', '--indent',
        type=int,
        default=2,
        help='JSON indentation spaces (0 for compact output)'
    )
    parser.add_argument(
        '-n', '--nest',
        metavar='ATTRIBUTE',
        nargs='?',
        const='subEntries',
        default=None,
        help='Enable hierarchical nesting under specified attribute'
    )
    parser.add_argument(
        '-d', '--decode',
        action='store_true',
        help='Decode Base64-encoded attributes (marked with ::)'
    )
    
    args = parser.parse_args()
    
    try:
        # Process LDIF with configured options
        entries = parse_ldif(args.input_file, decode_base64=args.decode)
        
        if args.nest is not None:
            entries = nest_entries(entries, args.nest)
        
        # Generate JSON output
        json.dump(
            entries,
            args.output,
            indent=args.indent,
            ensure_ascii=False,  # Preserve Unicode characters
            sort_keys=True       # Consistent output ordering
        )
        args.output.write('\n')  # Ensure valid JSON
        
    except Exception as e:
        print(f"Error: {str(e)}", file=sys.stderr)
        sys.exit(1)


if __name__ == '__main__':
    main()
