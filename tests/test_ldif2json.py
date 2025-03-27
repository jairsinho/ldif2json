import sys
import os
import pytest
from ldif2json import parse_ldif, nest_entries

# Añadir el directorio src al path para las importaciones
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../src')))

def test_parse_ldif_simple_entry():
    """Test para analizar una entrada LDIF simple."""
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
    """Test para atributos con múltiples valores."""
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
    assert len(result[0]['telephoneNumber']) == 2

def test_parse_ldif_with_comments():
    """Test que ignora líneas de comentario."""
    ldif_data = [
        "# Comentario inicial\n",
        "dn: cn=comment,dc=example\n",
        "# Otro comentario\n",
        "cn: comment\n",
        "description: # Esto no es un comentario\n"
    ]
    result = parse_ldif(ldif_data)
    
    assert len(result) == 1
    assert "#" not in result[0].values()
    assert result[0]['description'] == "# Esto no es un comentario"

def test_parse_ldif_empty_input():
    """Test para entrada vacía."""
    assert parse_ldif([]) == []

def test_parse_ldif_with_decoding():
    """Test Base64 decoding option."""
    ldif_data = [
        "dn: cn=test,dc=example\n",
        "secret:: QWxhZGRpbjpvcGVuIHNlc2FtZQ==\n"  # "Aladdin:open sesame"
    ]
    
    # With decoding
    decoded = parse_ldif(ldif_data, decode_base64=True)
    assert "Aladdin:open sesame" in decoded[0]['secret']
    
    # Without decoding
    raw = parse_ldif(ldif_data, decode_base64=False)
    assert ":: QWxhZGRpbjpvcGVuIHNlc2FtZQ==" in raw[0]['secret']

def test_parse_ldif_special_chars():
    """Test para valores con caracteres especiales."""
    ldif_data = [
        "dn:: Y249c3BlY2lhbCxkYz1leGFtcGxl\n",
        "description: Este es un valor con $%&/()=\n",
        "info:: QWxhZGRpbjpvcGVuIHNlc2FtZQ==\n"
    ]
    result = parse_ldif(ldif_data, decode_base64=True)
    
    assert "cn=special,dc=example" in result[0]['dn']
    assert "$%&/()=" in result[0]['description']
    assert "Aladdin:open sesame" in result[0]['info']

def test_nest_entries_basic():
    """Test básico para anidamiento de entradas."""
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

def test_nest_entries_custom_attribute():
    """Test para anidamiento con atributo personalizado."""
    entries = [
        {"dn": "o=org"},
        {"dn": "ou=dept,o=org"}
    ]
    nested = nest_entries(entries, parent_attribute="children")
    
    assert "children" in nested[0]
    assert not nested[0].get('subEntries')

@pytest.fixture
def sample_ldif_entries():
    """Fixture que devuelve entradas LDIF de muestra."""
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
    """Test de integración: parsear y luego anidar."""
    parsed = parse_ldif(sample_ldif_entries)
    nested = nest_entries(parsed)
    
    assert len(nested) == 1
    assert nested[0]['dn'] == "dc=test"
    assert len(nested[0]['subEntries']) == 1
    assert nested[0]['subEntries'][0]['dn'] == "ou=users,dc=test"
    assert len(nested[0]['subEntries'][0]['subEntries']) == 1
