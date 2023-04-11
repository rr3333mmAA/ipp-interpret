"""
Allowed libs
    argparse OR getopt
    codecs
    re
    xml.dom.minidom
    xml.etree.ElementTree
    xml.parsers.expat
    xml.sax.handler

Tests cheat sheet:
src - source/input file
rc - return code
out - output
"""
import argparse

# Argument parser (--help, --source=file, --input=file)
parser = argparse.ArgumentParser(
    description='Script loads an XML representation of a program '
                'and interprets it using input based on command-line parameters, generating output.')
parser.add_argument('--source', help="Source XML file")  # Change help
parser.add_argument('--input', help="Input")  # Change help
args = parser.parse_args()


