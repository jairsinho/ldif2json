#!/usr/bin/env python3
"""
Test suite for LDIF to JSON converter

Comprehensive unit and integration tests for all major functionality including:
- LDIF parsing
- Base64 decoding
- Hierarchical nesting
- Edge case handling
"""

import sys
import os
import pytest
from ldif2json import parse_ldif, nest_entries

# Add src directory to Python path for imports
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../src')))

def test_parse_ldif_simple_entry():
    """Test parsing of basic LDIF entry with single-value attributes."""
    ldif_data = [
        "dn: cn=test,dc=example\n",
        "objectClass: top\n",
        "objectClass: person\n",
        "cn: test\n"
    ]
    result = parse_ldif(ldif_data)

    assert len(result) == 1
    assert result[0]['dn'] == "cn=test,dc=example"
    assert isinstance(result[0]['objectClass'], list)
    assert result[0]['objectClass'] == ["top", "person"]
    assert result[0]['cn'] == "test"

def test_parse_ldif_multivalued_attributes():
    """Test handling of attributes with multiple values."""
    ldif_data = [
        "dn: cn=multi,dc=example\n",
        "mail: user@example.com\n",
        "mail: user@backup.com\n",
        "telephoneNumber: 123456789\n",
        "telephoneNumber: 987654321\n"
    ]
    result = parse_ldif(ldif_data)

    assert len(result[0]['mail']) == 2
    assert "user@example.com" in result[0]['mail']
    assert "user@backup.com" in result[0]['mail']
    assert len(result[0]['telephoneNumber']) == 2
    assert "123456789" in result[0]['telephoneNumber']

def test_parse_ldif_with_comments():
    """Test proper skipping of comment lines."""
    ldif_data = [
        "# Initial comment\n",
        "dn: cn=comment,dc=example\n",
        "# Another comment\n",
        "cn: comment\n",
        "description: # This is not a comment\n"
    ]
    result = parse_ldif(ldif_data)

    assert len(result) == 1
    assert "#" not in result[0].values()
    assert result[0]['description'] == "# This is not a comment"

def test_parse_ldif_empty_input():
    """Test handling of empty input."""
    assert parse_ldif([]) == []

def test_parse_ldif_with_decoding():
    """Test Base64 decoding functionality."""
    ldif_data = [
        "dn: cn=test,dc=example\n",
        "secret:: QWxhZGRpbjpvcGVuIHNlc2FtZQ==\n"  # "Aladdin:open sesame"
    ]

    # With Base64 decoding enabled
    decoded = parse_ldif(ldif_data, decode_base64=True)
    assert "Aladdin:open sesame" in decoded[0]['secret']

    # With Base64 decoding disabled
    raw = parse_ldif(ldif_data, decode_base64=False)
    assert ":: QWxhZGRpbjpvcGVuIHNlc2FtZQ==" in raw[0]['secret']

def test_parse_ldif_special_chars():
    """Test handling of special characters and Base64-encoded DN."""
    ldif_data = [
        "dn:: Y249c3BlY2lhbCxkYz1leGFtcGxl\n",  # "cn=special,dc=example"
        "description: Value with special $%&/()= chars\n",
        "info:: QWxhZGRpbjpvcGVuIHNlc2FtZQ==\n"  # "Aladdin:open sesame"
    ]
    result = parse_ldif(ldif_data, decode_base64=True)

    assert "cn=special,dc=example" in result[0]['dn']
    assert "$%&/()=" in result[0]['description']
    assert "Aladdin:open sesame" in result[0]['info']

def test_nest_entries_basic():
    """Test basic hierarchical nesting functionality."""
    entries = [
        {"dn": "dc=example"},
        {"dn": "ou=people,dc=example"},
        {"dn": "cn=user1,ou=people,dc=example"}
    ]
    nested = nest_entries(entries)

    assert len(nested) == 1
    assert nested[0]['dn'] == "dc=example"
    assert len(nested[0]['subEntries']) == 1
    assert nested[0]['subEntries'][0]['dn'] == "ou=people,dc=example"
    assert len(nested[0]['subEntries'][0]['subEntries']) == 1
    assert nested[0]['subEntries'][0]['subEntries'][0]['dn'] == "cn=user1,ou=people,dc=example"

def test_nest_entries_custom_attribute():
    """Test nesting with custom parent attribute name."""
    entries = [
        {"dn": "o=org"},
        {"dn": "ou=dept,o=org"}
    ]
    nested = nest_entries(entries, parent_attribute="children")

    assert "children" in nested[0]
    assert not nested[0].get('subEntries')
    assert nested[0]['children'][0]['dn'] == "ou=dept,o=org"

@pytest.fixture
def sample_ldif_entries():
    """Fixture providing sample LDIF data for integration tests."""
    return [
        "dn: dc=test\n",
        "objectClass: domain\n",
        "\n",
        "dn: ou=users,dc=test\n",
        "objectClass: organizationalUnit\n",
        "\n",
        "dn: cn=admin,ou=users,dc=test\n",
        "objectClass: person\n",
        "cn: admin\n"
    ]

def test_integration_parse_and_nest(sample_ldif_entries):
    """Test full integration of parsing and nesting."""
    parsed = parse_ldif(sample_ldif_entries)
    nested = nest_entries(parsed)

    assert len(nested) == 1
    assert nested[0]['dn'] == "dc=test"
    assert len(nested[0]['subEntries']) == 1
    assert nested[0]['subEntries'][0]['dn'] == "ou=users,dc=test"
    assert len(nested[0]['subEntries'][0]['subEntries']) == 1
    assert nested[0]['subEntries'][0]['subEntries'][0]['cn'] == "admin"