"""
Tests cheat sheet:
src - source/input file
rc - return code
out - output
"""
import argparse
import xml.etree.ElementTree as ET
import codecs  # encoder, decoder
import re  # regEx

# Argument parser (--help, --source=file, --input=file)
parser = argparse.ArgumentParser(
    description='Script loads an XML representation of a program '
                'and interprets it using input based on command-line parameters, generating output.')
parser.add_argument('--source', help="Source XML file")  # Change help
parser.add_argument('--input', help="Input")  # Change help
args = parser.parse_args()


# TODO:
#  check order and arg number via
#  @property and @method.setter
#  or
#  create check decorator

# XML Element Tree
if args.source or args.input:

    tree = ET.parse(args.source)
    root = tree.getroot()

    '''
    Format: instructions = [(instruction, [(type, text)]), ...]
    Example:
    instructions = [
    ('DEFVAR', [('var', 'GF@a')]),
    ('READ', [('var': 'GF@a'), ('type': 'int)])
    ]
    '''
    instructions = (
        (
            instruction.get('opcode'),
            [(arg.get('type'), arg.text.strip()) for arg in instruction]
        )
        for instruction in root.findall('instruction')
    )
