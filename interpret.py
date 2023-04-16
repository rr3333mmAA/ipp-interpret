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
 all 'symb: list' change to 'symb: str'
 check var name
"""
import argparse
import xml.etree.ElementTree as ET
import re
import sys


class Argument:
    """
    Instruction argument class
    """
    def __init__(self, arg_type: str, text: str) -> None:
        self.type_ = arg_type
        self.text = text

    @classmethod
    def add(cls, arg_type: str, text: str) -> any:
        arg_type, text = cls._filter(arg_type, text)
        return Argument(arg_type, text)

    @staticmethod
    def _filter(arg_type: str, text: str) -> list:
        if arg_type == 'bool':
            text = 'true' if text.lower() == 'true' else 'false'
        elif arg_type == 'int':
            if not text.isdigit():
                exit(56)  # Error
        elif arg_type == 'string':
            matches = set(re.findall(r'\\[0-9]{3}', text))
            for match in matches:
                text = text.replace(match, chr(int(match[1:])))
        elif arg_type == 'type':
            text = text.lower()
            if text not in {'int', 'string', 'bool'}:
                exit(56)  # Error
        return [arg_type, text]


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
                args=[Argument.add(arg.get('type'), arg.text.strip()) for arg in instr]
            )

        return cls.all_


class Function:
    def __init__(self) -> None:
        self.frames = {
            "GF": {},
            "LF": None
        }
        self.frame_stack = []
        self.stack = []
        # self.call_stack = []
        self.labels = {}

    # @staticmethod
    # def symb_checker(func):
    #     def wrapper(*args):
    #         for arg in args:
    #             if isinstance(arg, list):
    #                 if arg[0] == 'int' and not arg[1].isdigit():
    #                     exit(56)
    #                 elif arg[0] == 'string':
    #                     matches = set(re.findall(r'\\[0-9]{3}', arg[1]))
    #                     for match in matches:
    #                         arg[1] = arg[1].replace(match, chr(int(match[1:])))
    #         return func(*args)
    #     return wrapper

    def instr_move(self, var: str, symb: str) -> None:
        value = self._get_value(symb)
        self._set_value(var, value)

    def instr_createframe(self) -> None:
        self.frames["TF"] = {}

    def instr_pushframe(self) -> None:
        if self.frames["TF"] is None:
            exit()  # Error
        self.frames["LF"] = self.frames["TF"]
        self.frames["TF"] = None
        self.frame_stack.append(self.frames["LF"])

    def instr_popframe(self) -> None:
        if not self.frame_stack:
            exit()  # Error
        self.frames["TF"] = self.frames["LF"]
        self.frames["LF"] = self.frame_stack.pop()

    def instr_defvar(self, var: str) -> None:
        frame, name = self._var_split(var)
        if name in self.frames[frame]:
            exit()  # Error
        self.frames[frame][name] = None

    def instr_call(self, label: str, position: int) -> None:
        pass
        # self.call_stack.append(position)
        # if label not in self.labels:
        #     exit()  # Error

    def instr_return(self) -> None:
        pass

    def instr_pushs(self, symb: str) -> None:
        value = self._get_value(symb)
        self.stack.append(value)

    def instr_pops(self, var: str) -> None:
        # if stack is not empty
        value = self.stack[-1]
        self._set_value(var, value)
        self.stack.pop()

    def instr_add(self, var: str, symb1: str, symb2: str) -> None:
        value = self._operator(symb1, symb2, '+')
        self._set_value(var, value)

    def instr_sub(self, var: str, symb1: str, symb2: str) -> None:
        value = self._operator(symb1, symb2, '-')
        self._set_value(var, value)

    def instr_mul(self, var: str, symb1: str, symb2: str) -> None:
        value = self._operator(symb1, symb2, '*')
        self._set_value(var, value)

    def instr_idiv(self, var: str, symb1: str, symb2: str) -> None:
        value = self._operator(symb1, symb2, '/')
        self._set_value(var, value)

    def instr_lt(self, var: str, symb1: str, symb2: str) -> None:
        value = self._operator(symb1, symb2, '<')
        self._set_value(var, value)

    def instr_gt(self, var: str, symb1: str, symb2: str) -> None:
        value = self._operator(symb1, symb2, '>')
        self._set_value(var, value)

    def instr_eq(self, var: str, symb1: str, symb2: str) -> None:
        value = self._operator(symb1, symb2, '==')
        self._set_value(var, value)

    def instr_and(self, var: str, symb1: str, symb2: str) -> None:
        value = self._operator(symb1, symb2, 'and')
        self._set_value(var, value)

    def instr_or(self, var: str, symb1: str, symb2: str) -> None:
        value = self._operator(symb1, symb2, 'or')
        self._set_value(var, value)

    def instr_not(self, var: str, symb1: str, symb2: str) -> None:
        value = self._operator(symb1, symb2, 'not')
        self._set_value(var, value)

    def instr_int2char(self, var: str, symb: str) -> None:
        value = self._get_value(symb)
        self._set_value(var, chr(int(value)))

    def instr_stri2int(self, var: str, symb1: str, symb2: str) -> None:
        value, index = self._get_some_values(symb1, symb2)
        index = int(index)
        self._set_value(var, str(ord(value[index])))

    def instr_read(self, var: str, type_: str) -> None:
        value = input('TEST INPUT: ')
        if value == '':
            value = None
        elif type_ == 'bool':
            value = 'false' if value.lower() != 'true' else 'true'
        elif type_ == 'int':
            value = value if value.isdigit() else None
        self._set_value(var, value)

    def instr_write(self, symb: str) -> None:
        value = self._get_value(symb)
        if symb[0] in ['bool', 'nil']:
            print(value)
        else:
            print(value, end='')

    def instr_concat(self, var: str, symb1: str, symb2: str) -> None:
        value = self._operator(symb1, symb2, '+')
        self._set_value(var, value)

    def instr_strlen(self, var: str, symb: str) -> None:
        value = self._get_value(symb)
        self._set_value(var, str(len(value)))

    def instr_getchar(self, var: str, symb1: str, symb2: str) -> None:
        value, index = self._get_some_values(symb1, symb2)
        index = int(index)
        self._set_value(var, value[index])

    def instr_setchar(self, var: str, symb1: str, symb2: str) -> None:
        index, char = self._get_some_values(symb1, symb2)
        index = int(index)
        var_value = self._var_split(var)[1]
        value = var_value[:index] + char + var_value[index+1:]
        self._set_value(var, value)

    def instr_type(self, var: str, symb: str) -> None:  # change name
        self._set_value(var, symb[0])

    def instr_label(self, label: str) -> None:
        # if label in labels
        self.labels[label] = None

    def instr_jump(self, label: str) -> None:
        pass

    def instr_jumpifeq(self, label: str, symb1: str, symb2: str) -> None:
        value1, value2 = self._get_some_values(symb1, symb2)
        if value1 == value2:
            pass

    def instr_jumpifneq(self, label: str, symb1: str, symb2: str) -> None:
        value1, value2 = self._get_some_values(symb1, symb2)
        if value1 != value2:
            pass

    def instr_exit(self, symb: str) -> None:
        value = self._get_value(symb)
        exit(value)

    def instr_dprint(self, symb: str) -> None:
        value = self._get_value(symb)
        print(value, file=sys.stderr)

    def instr_break(self) -> None:
        pass

    def _get_value(self, symb: str) -> str:
        value = symb.split('@', 1)
        if value[0] in {'GF', 'LF', 'TF'}:
            return self.frames[value[0]][value[1]]
        return value[1]

    def _get_some_values(self, *args: str) -> list:
        return [self._get_value(arg) for arg in args]

    def _set_value(self, var: str, value: str) -> None:
        var_frame, var_name = self._var_split(var)
        self.frames[var_frame][var_name] = value

    def _operator(self, symb1: str, symb2: str, op: str) -> str:
        value1, value2 = self._get_some_values(symb1, symb2)

        if op in {'+', '-', '*', '<', '>', '=='}:
            return eval(f'str(value1 {op} value2)')
        elif op == '/':
            return str(int(value1 / value2))
        elif op in {'and', 'or', 'not'}:
            value1 = value1.lower() == 'true'
            value2 = value2.lower() == 'true'
            return eval(f'str(value1 {op} value2)')

    @staticmethod
    def _var_split(var: str) -> list:
        return var.split("@", 1)

    # @staticmethod
    # def _decode(string: str) -> str:
    #     if string != '':
    #         matches = set(re.findall(r'\\[0-9]{3}', string))
    #         for match in matches:
    #             string = string.replace(match, chr(int(match[1:])))
    #         return string


class Interpreter:
    def __init__(self) -> None:
        self.function = Function()
        self.position = 0

    def interpret(self, instructions: list) -> None:  # Change this method (mb by using getattr() and lower())
        func = self.function
        while self.position < len(instructions):
            instruction = instructions[self.position]
            attr = f'instr_{instruction.opcode.lower()}'
            args = self._get_args(instruction)
            executor = getattr(func, attr)
            executor(*args)
            self.position += 1
        # while self.position < len(interpret_instructions):
        #     instr = interpret_instructions[self.position]
        #     opcode = instr.opcode.upper()
        #     args = instr.args
        #     if opcode == "MOVE":
        #         var = args[0].text
        #         symb = [args[1].type_, args[1].text]
        #         func.move(var, symb)
        #     elif opcode == "CREATEFRAME":
        #         func.create_frame()
        #     elif opcode == "PUSHFRAME":
        #         func.push_frame()
        #     elif opcode == "POPFRAME":
        #         func.pop_frame()
        #     elif opcode == "DEFVAR":
        #         var = args[0].text
        #         func.def_var(var)
        #     elif opcode == "CALL":
        #         pass
        #         # label = args[0].text
        #         # func.call(label, position)
        #     elif opcode == "RETURN":
        #         pass
        #     elif opcode == "PUSHS":
        #         symb = [args[0].type_, args[0].text]
        #         func.pushs(symb)
        #     elif opcode == "POPS":
        #         var = args[0].text
        #         func.pops(var)
        #     elif opcode in {"ADD", "CONCAT"}:  # Change
        #         var = args[0].text
        #         symb1 = [args[1].type_, args[1].text]
        #         symb2 = [args[2].type_, args[2].text]
        #         func.add(var, symb1, symb2)
        #     elif opcode == "SUB":
        #         var = args[0].text
        #         symb1 = [args[1].type_, args[1].text]
        #         symb2 = [args[2].type_, args[2].text]
        #         func.sub(var, symb1, symb2)
        #     elif opcode == "MUL":
        #         var = args[0].text
        #         symb1 = [args[1].type_, args[1].text]
        #         symb2 = [args[2].type_, args[2].text]
        #         func.mul(var, symb1, symb2)
        #     elif opcode == "IDIV":
        #         var = args[0].text
        #         symb1 = [args[1].type_, args[1].text]
        #         symb2 = [args[2].type_, args[2].text]
        #         func.idiv(var, symb1, symb2)
        #     elif opcode == "LT":
        #         var = args[0].text
        #         symb1 = [args[1].type_, args[1].text]
        #         symb2 = [args[2].type_, args[2].text]
        #         func.lt(var, symb1, symb2)
        #     elif opcode == "GT":
        #         var = args[0].text
        #         symb1 = [args[1].type_, args[1].text]
        #         symb2 = [args[2].type_, args[2].text]
        #         func.lt(var, symb1, symb2)
        #     elif opcode == "EQ":
        #         var = args[0].text
        #         symb1 = [args[1].type_, args[1].text]
        #         symb2 = [args[2].type_, args[2].text]
        #         func.lt(var, symb1, symb2)
        #     elif opcode == "AND":
        #         var = args[0].text
        #         symb1 = [args[1].type_, args[1].text]
        #         symb2 = [args[2].type_, args[2].text]
        #         func.and_(var, symb1, symb2)
        #     elif opcode == "OR":
        #         var = args[0].text
        #         symb1 = [args[1].type_, args[1].text]
        #         symb2 = [args[2].type_, args[2].text]
        #         func.or_(var, symb1, symb2)
        #     elif opcode == "NOT":
        #         var = args[0].text
        #         symb1 = [args[1].type_, args[1].text]
        #         symb2 = [args[2].type_, args[2].text]
        #         func.not_(var, symb1, symb2)
        #     elif opcode == "INT2CHAR":
        #         var = args[0].text
        #         symb = [args[1].type_, args[1].text]
        #         func.int2char(var, symb)
        #     elif opcode == "STRI2INT":
        #         var = args[0].text
        #         symb1 = [args[1].type_, args[1].text]
        #         symb2 = [args[2].type_, args[2].text]
        #         func.stri2int(var, symb1, symb2)
        #     elif opcode == "READ":
        #         var = args[0].text
        #         type_ = args[1].text
        #         func.read(var, type_)
        #     elif opcode == "WRITE":
        #         symb = [args[0].type_, args[0].text]
        #         func.write(symb)
        #     elif opcode == "STRLEN":
        #         var = args[0].text
        #         symb = [args[1].type_, args[1].text]
        #         func.strlen(var, symb)
        #     elif opcode == "GETCHAR":
        #         var = args[0].text
        #         symb1 = [args[1].type_, args[1].text]
        #         symb2 = [args[2].type_, args[2].text]
        #         func.getchar(var, symb1, symb2)
        #     elif opcode == "SETCHAR":
        #         var = args[0].text
        #         symb1 = [args[1].type_, args[1].text]
        #         symb2 = [args[2].type_, args[2].text]
        #         func.setchar(var, symb1, symb2)
        #     elif opcode == "TYPE":
        #         var = args[0].text
        #         symb = [args[1].type_, args[1].text]
        #         func.type__(var, symb)
        #     elif opcode == "LABEL":
        #         label = args[0].text
        #         func.label(label)
        #     elif opcode == "JUMP":
        #         label = args[0].text
        #         func.jump(label)
        #     elif opcode == "JUMPIFEQ":
        #         label = args[0].text
        #         symb1 = [args[1].type_, args[1].text]
        #         symb2 = [args[2].type_, args[2].text]
        #         func.jumpifeq(label, symb1, symb2)
        #     elif opcode == "JUMPIFNEQ":
        #         label = args[0].text
        #         symb1 = [args[1].type_, args[1].text]
        #         symb2 = [args[2].type_, args[2].text]
        #         func.jumpifneq(label, symb1, symb2)
        #     elif opcode == "EXIT":
        #         symb = [args[0].type_, args[0].text]
        #         func.exit_(symb)
        #     elif opcode == "DPRINT":
        #         symb = [args[0].type_, args[0].text]
        #         func.dprint(symb)
        #     elif opcode == "BREAK":
        #         func.break_()
        #     else:
        #         exit()  # Error
        #     self.position+= 1
        # for position, instr in enumerate(interpret_instructions):
            # opcode = instr.opcode.upper()
            # args = instr.args
            # if opcode == "MOVE":
            #     var = args[0].text
            #     symb = [args[1].type_, args[1].text]
            #     func.move(var, symb)
            # elif opcode == "CREATEFRAME":
            #     func.create_frame()
            # elif opcode == "PUSHFRAME":
            #     func.push_frame()
            # elif opcode == "POPFRAME":
            #     func.pop_frame()
            # elif opcode == "DEFVAR":
            #     var = args[0].text
            #     func.def_var(var)
            # elif opcode == "CALL":
            #     pass
            #     # label = args[0].text
            #     # func.call(label, position)
            # elif opcode == "RETURN":
            #     pass
            # elif opcode == "PUSHS":
            #     symb = [args[0].type_, args[0].text]
            #     func.pushs(symb)
            # elif opcode == "POPS":
            #     var = args[0].text
            #     func.pops(var)
            # elif opcode in {"ADD", "CONCAT"}:  # Change
            #     var = args[0].text
            #     symb1 = [args[1].type_, args[1].text]
            #     symb2 = [args[2].type_, args[2].text]
            #     func.add(var, symb1, symb2)
            # elif opcode == "SUB":
            #     var = args[0].text
            #     symb1 = [args[1].type_, args[1].text]
            #     symb2 = [args[2].type_, args[2].text]
            #     func.sub(var, symb1, symb2)
            # elif opcode == "MUL":
            #     var = args[0].text
            #     symb1 = [args[1].type_, args[1].text]
            #     symb2 = [args[2].type_, args[2].text]
            #     func.mul(var, symb1, symb2)
            # elif opcode == "IDIV":
            #     var = args[0].text
            #     symb1 = [args[1].type_, args[1].text]
            #     symb2 = [args[2].type_, args[2].text]
            #     func.idiv(var, symb1, symb2)
            # elif opcode == "LT":
            #     var = args[0].text
            #     symb1 = [args[1].type_, args[1].text]
            #     symb2 = [args[2].type_, args[2].text]
            #     func.lt(var, symb1, symb2)
            # elif opcode == "GT":
            #     var = args[0].text
            #     symb1 = [args[1].type_, args[1].text]
            #     symb2 = [args[2].type_, args[2].text]
            #     func.lt(var, symb1, symb2)
            # elif opcode == "EQ":
            #     var = args[0].text
            #     symb1 = [args[1].type_, args[1].text]
            #     symb2 = [args[2].type_, args[2].text]
            #     func.lt(var, symb1, symb2)
            # elif opcode == "AND":
            #     var = args[0].text
            #     symb1 = [args[1].type_, args[1].text]
            #     symb2 = [args[2].type_, args[2].text]
            #     func.and_(var, symb1, symb2)
            # elif opcode == "OR":
            #     var = args[0].text
            #     symb1 = [args[1].type_, args[1].text]
            #     symb2 = [args[2].type_, args[2].text]
            #     func.or_(var, symb1, symb2)
            # elif opcode == "NOT":
            #     var = args[0].text
            #     symb1 = [args[1].type_, args[1].text]
            #     symb2 = [args[2].type_, args[2].text]
            #     func.not_(var, symb1, symb2)
            # elif opcode == "INT2CHAR":
            #     var = args[0].text
            #     symb = [args[1].type_, args[1].text]
            #     func.int2char(var, symb)
            # elif opcode == "STRI2INT":
            #     var = args[0].text
            #     symb1 = [args[1].type_, args[1].text]
            #     symb2 = [args[2].type_, args[2].text]
            #     func.stri2int(var, symb1, symb2)
            # elif opcode == "READ":
            #     var = args[0].text
            #     type_ = args[1].text
            #     func.read(var, type_)
            # elif opcode == "WRITE":
            #     symb = [args[0].type_, args[0].text]
            #     func.write(symb)
            # elif opcode == "STRLEN":
            #     var = args[0].text
            #     symb = [args[1].type_, args[1].text]
            #     func.strlen(var, symb)
            # elif opcode == "GETCHAR":
            #     var = args[0].text
            #     symb1 = [args[1].type_, args[1].text]
            #     symb2 = [args[2].type_, args[2].text]
            #     func.getchar(var, symb1, symb2)
            # elif opcode == "SETCHAR":
            #     var = args[0].text
            #     symb1 = [args[1].type_, args[1].text]
            #     symb2 = [args[2].type_, args[2].text]
            #     func.setchar(var, symb1, symb2)
            # elif opcode == "TYPE":
            #     var = args[0].text
            #     symb = [args[1].type_, args[1].text]
            #     func.type__(var, symb)
            # elif opcode == "LABEL":
            #     label = args[0].text
            #     func.label(label)
            # elif opcode == "JUMP":
            #     label = args[0].text
            #     func.jump(label)
            # elif opcode == "JUMPIFEQ":
            #     label = args[0].text
            #     symb1 = [args[1].type_, args[1].text]
            #     symb2 = [args[2].type_, args[2].text]
            #     func.jumpifeq(label, symb1, symb2)
            # elif opcode == "JUMPIFNEQ":
            #     label = args[0].text
            #     symb1 = [args[1].type_, args[1].text]
            #     symb2 = [args[2].type_, args[2].text]
            #     func.jumpifneq(label, symb1, symb2)
            # elif opcode == "EXIT":
            #     symb = [args[0].type_, args[0].text]
            #     func.exit_(symb)
            # elif opcode == "DPRINT":
            #     symb = [args[0].type_, args[0].text]
            #     func.dprint(symb)
            # elif opcode == "BREAK":
            #     func.break_()
            # else:
            #     exit()  # Error

    @staticmethod
    def _get_args(instruction: Instruction) -> list:
        """
        Get formatted arguments
        """
        result = []
        for arg in instruction.args:
            if arg.type_.lower() in {'var', 'label', 'type'}:
                result.append(arg.text)
            elif arg.type_.lower() in {'int', 'bool', 'string'}:
                result.append(f'{arg.type_}@{arg.text}')
            elif arg.type_.lower() == 'nil':
                result.append('nil@nil')
            else:
                exit(56)  # Error
        return result


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
    # cline_args.source = "./tests/my_tests/test1.src"
    # cline_args.source = "./tests/read_test.src"
    # cline_args.source = "./tests/spec_example.src"

    if cline_args.source or cline_args.input:
        # if cline_args.input:
        #     output_file = cline_args.input

        # Getting all instructions from source XML
        instructions = Instruction.get_instructions_from_xml(cline_args.source)
        inter = Interpreter()
        inter.interpret(instructions)


if __name__ == '__main__':
    main()
