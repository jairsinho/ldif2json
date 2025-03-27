# LDIF to JSON Converter

[![PyPI version](https://badge.fury.io/py/ldif2json.svg)](https://pypi.org/project/ldif2json/)
[![Python versions](https://img.shields.io/pypi/pyversions/ldif2json.svg)](https://pypi.org/project/ldif2json/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![CI](https://github.com/jairsinho/ldif2json/actions/workflows/release.yml/badge.svg)](https://github.com/jairsinho/ldif2json/actions)

A robust Python tool for converting LDAP Data Interchange Format (LDIF) files to JSON with support for hierarchical nesting and Base64 decoding.

## Features

- **LDIF Parsing**: Convert LDIF files to structured JSON
- **Base64 Handling**: Optional decoding of Base64-encoded attributes (`-d` flag)
- **Hierarchical Nesting**: Organize entries by DN structure (`-n` option)
- **Flexible I/O**: Works with files or stdin/stdout
- **Custom Formatting**: Control JSON indentation (`-i` option)

## Installation

```bash
pip install ldif2json
```

## Usage

Basic conversion:
```bash
ldif2json input.ldif -o output.json
```

With hierarchical nesting:
```bash
ldif2json input.ldif --nest -o output.json
```

With Base64 decoding:
```bash
ldif2json input.ldif --decode -o output.json
```

Using pipes:
```bash
ldapsearch -x -b "dc=example,dc=com" | ldif2json --nest children
```

## Options

```
usage: ldif2json.py [-h] [-o OUTPUT] [-i INDENT] [-n [ATTRIBUTE]] [-d] [input_file]

Convert LDIF to JSON with optional Base64 decoding and nesting

positional arguments:
  input_file            Input LDIF file (default: stdin)

options:
  -h, --help            show this help message and exit
  -o OUTPUT, --output OUTPUT
                        Output JSON file (default: stdout)
  -i INDENT, --indent INDENT
                        JSON indentation spaces (0 for compact output) (default: 2)
  -n [ATTRIBUTE], --nest [ATTRIBUTE]
                        Enable hierarchical nesting under specified attribute (default: None)
  -d, --decode          Decode Base64-encoded attributes (marked with ::) (default: False)

```

## License

MIT License
