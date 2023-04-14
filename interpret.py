"""
Tests cheat sheet:
 src - source/input file
 rc - return code
 out - output

TODO:
 check order and arg number via
 @property and @method.setter
 or
 create check decorator
"""
import argparse
import xml.etree.ElementTree as ET
import codecs  # encoder, decoder
import re  # regEx


# Instruction argument class
class Argument:
    def __init__(self, type_: str, text: str) -> None:
        self.type_ = type_
        self.text = text


# Instruction class
class Instruction:
    all_ = []

    def __init__(self, order: int, opcode: str, args: list) -> None:
        self.order = order
        self.opcode = opcode
        self.args = args

        Instruction.all_.append(self)

    @classmethod
    def get_instructions_from_xml(cls, src: str) -> None:
        root = ET.parse(src).getroot()

        for instr in root.findall('instruction'):
            Instruction(
                order=int(instr.get('order')),
                opcode=instr.get('opcode'),
                args=[Argument(arg.get('type'), arg.text.strip()) for arg in instr]
            )


# Command line argument parser (--help, --source=file, --input=file)
parser = argparse.ArgumentParser(description='The script loads an XML representation of a program '
                                             'interprets the program using input according to command line parameters '
                                             'and generates output.')

parser.add_argument('--source', help="Source XML file")  # Change help
parser.add_argument('--input', help="Input")  # Change help

cline_args = parser.parse_args()  # Change var name (?)


# Getting all instructions from source XML
Instruction.get_instructions_from_xml(cline_args.source)
instructions = Instruction.all_
