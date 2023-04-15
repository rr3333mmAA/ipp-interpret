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


class Argument:
    """
    Instruction argument class
    """
    def __init__(self, arg_type: str, text: str) -> None:
        self.type_ = arg_type
        self.text = text


class Instruction:
    """
    Instruction class
    """
    all_ = []

    def __init__(self, order: int, opcode: str, args: list) -> None:
        self.order = order
        self.opcode = opcode
        self.args = args

        Instruction.all_.append(self)

    @classmethod
    def get_instructions_from_xml(cls, src: str) -> list:
        """
        Parsing an XML file and returning structured instructions.
        :param src: XML source file
        :return: List with all instructions
        """
        root = ET.parse(src).getroot()

        for instr in root.findall('instruction'):
            Instruction(
                order=int(instr.get('order')),
                opcode=instr.get('opcode'),
                args=[Argument(arg.get('type'), arg.text.strip()) for arg in instr]
            )

        return cls.all_


class Function:
    def __init__(self) -> None:
        self.frames = {
            "GF": {},
            "LF": None
        }
        self.stack = []

    def move(self, var: str, symb: list) -> None:
        value = self._get_value(symb)
        self._set_value(var, value)

    def create_frame(self) -> None:
        self.frames["TF"] = {}

    def push_frame(self) -> None:
        if self.frames["TF"] is None:
            exit()  # Error
        self.frames["LF"] = self.frames["TF"]
        self.frames["TF"] = None
        self.stack.append(self.frames["LF"])

    def pop_frame(self) -> None:
        if not self.stack:
            exit()  # Error
        self.frames["TF"] = self.frames["LF"]
        self.frames["LF"] = self.stack.pop()

    def def_var(self, var: str) -> None:
        frame, name = self._var_split(var)
        if name in self.frames[frame]:
            exit()  # Error
        self.frames[frame][name] = None

    def read(self, var: str, type_: str) -> None:
        value = input('TEST INPUT: ')
        if value == '':
            value = None
        elif type_ == 'bool':
            value = 'false' if value.lower() != 'true' else 'true'
        elif type_ == 'int':
            value = value if value.isdigit() else None
        self._set_value(var, value)

    def write(self, symb: list) -> None:
        value = self._get_value(symb)
        # value = codecs.decode(value, 'unicode-escape')
        if symb[0] in ['bool', 'nil']:
            print(value)
        else:
            print(value, end='')

    def _get_value(self, symb: list) -> str:
        type_, value = symb
        if type_ == 'var':
            frame, name = self._var_split(value)
            if name not in self.frames[frame]:
                exit()  # Error
            return self.frames[frame][name]
        return value

    def _set_value(self, var: str, value: str) -> None:
        var_frame, var_name = self._var_split(var)
        self.frames[var_frame][var_name] = value

    @staticmethod
    def _var_split(var: str) -> list:
        return var.split("@")


class Interpreter:
    def __init__(self) -> None:
        self.function = Function()

    def interpret(self, interpret_instructions: list) -> None:
        func = self.function
        for instr in interpret_instructions:
            opcode = instr.opcode.upper()
            args = instr.args
            if opcode == "MOVE":
                pass
            elif opcode == "CREATEFRAME":
                func.create_frame()
            elif opcode == "PUSHFRAME":
                func.push_frame()
            elif opcode == "POPFRAME":
                func.pop_frame()
            elif opcode == "DEFVAR":
                var = args[0].text
                func.def_var(var)
            elif opcode == "READ":
                var = args[0].text
                type_ = args[1].text
                func.read(var, type_)
            elif opcode == "WRITE":
                symb = [args[0].type_, args[0].text]
                func.write(symb)
            else:
                exit()  # Error


def main() -> None:
    # Command line argument parser (--help, --source=file, --input=file)
    parser = argparse.ArgumentParser(
        description='The script loads an XML representation of a program '
                    'interprets the program using input according to command line parameters '
                    'and generates output.'
    )
    parser.add_argument('--source', help="Source XML file")  # Change help
    parser.add_argument('--input', help="Input")  # Change help
    cline_args = parser.parse_args()  # Change var name (?)

    # Debug
    cline_args.source = "./tests/my_tests/test1.src"
    cline_args.source = "./tests/read_test.src"

    if cline_args.source or cline_args.input:
        # if cline_args.input:
        #     output_file = cline_args.input

        # Getting all instructions from source XML
        instructions = Instruction.get_instructions_from_xml(cline_args.source)
        inter = Interpreter()
        inter.interpret(instructions)


if __name__ == '__main__':
    main()
