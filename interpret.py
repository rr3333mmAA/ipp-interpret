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
 wrong opcode check
 find pass
 write (bool, None)
 bad source file
 wrong number of args
 wrong args
 arg order
 32 and 52 error
 type() change to isinstance()
 docs: add concats
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
            try:
                int(text)
            except ValueError:
                exit(32)  # Error
        elif arg_type == 'string':
            matches = set(re.findall(r'\\[0-9]{3}', text))
            for match in matches:
                text = text.replace(match, chr(int(match[1:])))
        elif arg_type == 'type':
            text = text.lower()
            if text not in {'int', 'string', 'bool', 'float'}:
                exit(56)  # Error
        elif arg_type == 'float':
            try:
                text = float.fromhex(text)
            except ValueError:
                pass  # Error

            try:
                float.hex(float(text))
            except ValueError:
                exit(32)  # Error
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

    # Redesign
    @classmethod
    def get_instructions_from_xml(cls, src: str) -> list:
        """
        Parsing an XML file and returning structured instructions.
        :param src: XML source file
        :return: List with all instructions
        """
        try:
            root = ET.parse(src).getroot()
        except ET.ParseError:
            exit(31)  # Error

        if root.tag != 'program' or root.attrib['language'] != 'IPPcode23':
            exit(32)  # Error

        for instr in root:
            if instr.tag != 'instruction' or 'order' not in instr.attrib or 'opcode' not in instr.attrib:
                exit(32)  # Error
            args = []
            for num in range(len(instr)):
                arg = instr.find(f'arg{num + 1}')
                if arg is None or 'type' not in arg.attrib:
                    exit(32)  # Error
                arg.text = arg.text.strip() if arg.text is not None else ''
                args.append(Argument.add(arg.get('type'), arg.text))

            try:
                order = int(instr.get('order'))
            except ValueError:
                exit(32)

            Instruction(
                order=order,
                opcode=instr.get('opcode'),
                args=args
            )

        return cls.all_


class Function:
    def __init__(self, stdin) -> None:
        self.stdin = stdin
        self.frames = {
            "GF": {},
            "LF": None
        }
        self.frame_stack = []
        self.stack = []
        self.position = 0
        self.call_stack = []
        self.labels = {}

    def instr_move(self, var: str, symb: str) -> None:
        value = self._get_value(symb)
        self._set_value(var, value)

    def instr_createframe(self) -> None:
        self.frames["TF"] = {}

    def instr_pushframe(self) -> None:
        if "TF" not in self.frames:
            exit(55)  # Error
        self.frame_stack.append(self.frames["LF"])
        self.frames["LF"] = self.frames["TF"]
        self.frames["TF"] = None

    def instr_popframe(self) -> None:
        if not self.frame_stack:
            exit(55)  # Error
        self.frames["TF"] = self.frames["LF"]
        self.frames["LF"] = self.frame_stack.pop()

    def instr_defvar(self, var: str) -> None:
        frame, name = self._var_split(var)
        if frame not in {'GF', 'LF', 'TF'}:
            exit(52)  # Error (May be)
        if frame == 'TF' and 'TF' not in self.frames:
            exit(55)  # Error
        if name in self.frames[frame]:
            exit(52)  # Error
        self.frames[frame][name] = None

    def instr_call(self, label: str) -> None:
        self.call_stack.append(self.position)
        self.instr_jump(label)

    def instr_return(self) -> None:
        if not self.call_stack:
            exit(56)  # Error
        self.position = self.call_stack[-1]
        self.call_stack.pop()

    def instr_pushs(self, symb: str) -> None:
        value = self._get_value(symb)
        self.stack.append(value)

    def instr_pops(self, var: str) -> None:
        if not self.stack:
            exit(56)  # Error
        value = self.stack[-1]
        self._set_value(var, value)
        self.stack.pop()

    def instr_clears(self) -> None:
        self.stack = []

    def instr_add(self, var: str, symb1: str, symb2: str) -> None:
        value = self._operator(symb1, symb2, '+')
        self._set_value(var, value)

    def instr_adds(self) -> None:
        value1, value2 = self._get_values_from_stack(2)
        if type(value1) != type(value2) != int:
            exit(53)  # Error
        value = value1 + value2
        self._replace_stack_value(value, 2)

    def instr_sub(self, var: str, symb1: str, symb2: str) -> None:
        value = self._operator(symb1, symb2, '-')
        self._set_value(var, value)

    def instr_subs(self) -> None:
        value1, value2 = self._get_values_from_stack(2)
        if type(value1) != type(value2) != int:
            exit(53)  # Error
        value = value2 - value1
        self._replace_stack_value(value, 2)

    def instr_mul(self, var: str, symb1: str, symb2: str) -> None:
        value = self._operator(symb1, symb2, '*')
        self._set_value(var, value)

    def instr_muls(self) -> None:
        value1, value2 = self._get_values_from_stack(2)
        if type(value1) != type(value2) != int:
            exit(53)  # Error
        value = value1 * value2
        self._replace_stack_value(value, 2)

    def instr_div(self, var: str, symb1: str, symb2: str) -> None:
        value = self._operator(symb1, symb2, '/')
        self._set_value(var, value)

    def instr_idiv(self, var: str, symb1: str, symb2: str) -> None:
        value = self._operator(symb1, symb2, '//')
        self._set_value(var, value)

    def instr_idivs(self) -> None:
        value1, value2 = self._get_values_from_stack(2)
        if type(value1) != type(value2) != int:
            exit(53)  # Error
        value = value2 // value1
        self._replace_stack_value(value, 2)

    def instr_lt(self, var: str, symb1: str, symb2: str) -> None:
        value = self._operator(symb1, symb2, '<')
        self._set_value(var, value)

    def instr_lts(self) -> None:
        value1, value2 = self._get_values_from_stack(2)
        if type(value1) != type(value2) or value1 is None:
            exit(53)  # Error
        value = value2 < value1
        self._replace_stack_value(value, 2)

    def instr_gt(self, var: str, symb1: str, symb2: str) -> None:
        value = self._operator(symb1, symb2, '>')
        self._set_value(var, value)

    def instr_gts(self) -> None:
        value1, value2 = self._get_values_from_stack(2)
        if type(value1) != type(value2) or value1 is None:
            exit(53)  # Error
        value = value2 > value1
        self._replace_stack_value(value, 2)

    def instr_eq(self, var: str, symb1: str, symb2: str) -> None:
        value = self._operator(symb1, symb2, '==')
        self._set_value(var, value)

    def instr_eqs(self) -> None:
        value1, value2 = self._get_values_from_stack(2)
        if type(value1) != type(value2) and value1 is not None and value2 is not None:
            exit(53)  # Error
        value = value1 == value2
        self._replace_stack_value(value, 2)

    def instr_and(self, var: str, symb1: str, symb2: str) -> None:
        value = self._operator(symb1, symb2, 'and')
        self._set_value(var, value)

    def instr_ands(self) -> None:
        value1, value2 = self._get_values_from_stack(2)
        if not isinstance(value1, bool) or not isinstance(value2, bool):
            exit(53)  # Error
        value = value1 and value2
        self._replace_stack_value(value, 2)

    def instr_or(self, var: str, symb1: str, symb2: str) -> None:
        value = self._operator(symb1, symb2, 'or')
        self._set_value(var, value)

    def instr_ors(self) -> None:
        value1, value2 = self._get_values_from_stack(2)
        if not isinstance(value1, bool) or not isinstance(value2, bool):
            exit(53)  # Error
        value = value1 or value2
        self._replace_stack_value(value, 2)

    # Redesign
    def instr_not(self, var: str, symb1: str) -> None:
        value = self._get_value(symb1)
        if not isinstance(value, bool):
            exit(53)  # Error
        self._set_value(var, not bool(value))

    def instr_nots(self) -> None:
        value = self._get_values_from_stack(1)
        if not isinstance(value, bool):
            exit(53)  # Error
        value = not(value)
        self._replace_stack_value(value, 1)

    def instr_int2char(self, var: str, symb: str) -> None:
        value = self._get_value(symb)
        if type(value) is not int:
            exit(53)  # Error
        try:
            self._set_value(var, chr(value))
        except ValueError:
            exit(58)  # Error

    def instr_int2chars(self) -> None:
        value = self._get_values_from_stack(1)
        if type(value) is not int:
            exit(53)  # Error
        try:
            value = chr(value)
        except ValueError:
            exit(58)  # Error
        self._replace_stack_value(value, 1)

    def instr_int2float(self, var: str, symb: str) -> None:
        value = self._get_value(symb)
        if type(value) is not int:
            exit(53)  # Error
        try:
            self._set_value(var, float(value))
        except ValueError:
            exit(58)  # Error

    def instr_float2int(self, var: str, symb: str) -> None:
        value = self._get_value(symb)

        if type(value) is not float:
            exit(53)  # Error
        try:
            self._set_value(var, int(value))
        except ValueError:
            exit(58)  # Error

    def instr_stri2int(self, var: str, symb1: str, symb2: str) -> None:
        value, index = self._get_some_values(symb1, symb2)
        if not isinstance(value, str) or type(index) is not int:
            exit(53)  # Error
        elif index >= len(value):
            exit(58)  # Error
        self._set_value(var, str(ord(value[index])))

    def instr_stri2ints(self) -> None:
        index, value = self._get_values_from_stack(2)
        if not isinstance(value, str) or type(index) is not int:
            exit(53)  # Error
        elif index >= len(value):
            exit(58)  # Error
        value = str(ord(value[index]))
        self._replace_stack_value(value, 2)

    def instr_read(self, var: str, type_: str) -> None:
        value = input() if self.stdin is None else self.stdin
        value = value.replace('\n', '')

        if value == '':
            value = None
        elif type_ == 'bool':
            value = 'false' if value.lower() != 'true' else 'true'
        elif type_ == 'int':
            try:
                value = int(value)
            except ValueError:
                value = None
        elif type_ == 'float':
            try:
                value = float.fromhex(value)
            except ValueError:
                value = None
        self._set_value(var, value)

    def instr_write(self, symb: str) -> None:
        value = self._get_value(symb)
        if isinstance(value, bool):
            print('true' if value else 'false', end='')
        elif value is None:
            print('', end='')
        elif type(value) is float:
            print(float.hex(value), end='')
        else:
            print(value, end='')

    def instr_concat(self, var: str, symb1: str, symb2: str) -> None:
        value = self._operator(symb1, symb2, '.')
        self._set_value(var, value)

    def instr_strlen(self, var: str, symb: str) -> None:
        value = self._get_value(symb)
        if not isinstance(value, str):
            exit(53)  # Error
        self._set_value(var, len(value))

    def instr_getchar(self, var: str, symb1: str, symb2: str) -> None:
        value, index = self._get_some_values(symb1, symb2)
        if type(index) is not int or not isinstance(value, str):
            exit(53)  # Error
        elif index >= len(value):
            exit(58)  # Error
        self._set_value(var, value[index])

    def instr_setchar(self, var: str, symb1: str, symb2: str) -> None:
        index, char = self._get_some_values(symb1, symb2)
        var_value = self._get_value(var)
        if type(index) is not int or not isinstance(char, str):
            exit(53)  # Error
        elif index >= len(var_value):
            exit(58)  # Error
        value = var_value[:index] + char + var_value[index + 1:]
        self._set_value(var, value)

    def instr_type(self, var: str, symb: str) -> None:  # change name
        value = self._get_value(symb)
        if type(value) is int:
            self._set_value(var, 'int')
        if type(value) is str:
            self._set_value(var, 'string')
        if type(value) is bool:
            self._set_value(var, 'bool')
        if value is None:
            self._set_value(var, 'nil')

    def instr_label(self, label: str) -> None:
        pass

    def instr_jump(self, label: str) -> None:
        if label not in self.labels:
            exit(52)  # Error
        self.position = self.labels[label]

    def instr_jumpifeq(self, label: str, symb1: str, symb2: str) -> None:
        value1, value2 = self._get_some_values(symb1, symb2)
        if type(value1) != type(value2) and value1 is not None and value2 is not None:
            exit(53)  # Error
        if value1 == value2:
            self.instr_jump(label)

    def instr_jumpifeqs(self, label: str) -> None:
        value2, value1 = self._get_values_from_stack(2)
        if type(value1) != type(value2) and value1 is not None and value2 is not None:
            exit(53)  # Error
        if value1 == value2:
            self.instr_jump(label)
        self.stack.pop()
        self.stack.pop()

    def instr_jumpifneq(self, label: str, symb1: str, symb2: str) -> None:
        value1, value2 = self._get_some_values(symb1, symb2)
        if type(value1) != type(value2) and value1 is not None and value2 is not None:
            exit(53)  # Error
        if value1 != value2:
            self.instr_jump(label)

    def instr_jumpifneqs(self, label: str) -> None:
        value2, value1 = self._get_values_from_stack(2)
        if type(value1) != type(value2) and value1 is not None and value2 is not None:
            exit(53)  # Error
        if value1 != value2:
            self.instr_jump(label)
        self.stack.pop()
        self.stack.pop()

    def instr_exit(self, symb: str) -> None:
        value = self._get_value(symb)
        if type(value) is not int:
            exit(53)  # Error
        if value < 0 or value > 49:
            exit(57)  # Error
        exit(value)

    def instr_dprint(self, symb: str) -> None:
        value = self._get_value(symb)
        print(value, file=sys.stderr)

    def instr_break(self) -> None:
        pass

    def _get_value(self, symb: str) -> any:
        value = symb.split('@', 1)
        if value[0] in {'GF', 'LF', 'TF'}:
            if value[0] not in self.frames or self.frames[value[0]] is None:
                exit(55)  # Error
            elif value[1] not in self.frames[value[0]]:
                exit(54)  # Error
            return self.frames[value[0]][value[1]]
        elif value[0] == 'int':
            return int(value[1])
        elif value[0] == 'bool':
            return value[1].lower() == 'true'
        elif value[0] == 'nil':
            return None
        elif value[0] == 'float':
            return float(value[1])
        return value[1]

    def _get_some_values(self, *args: str) -> list:
        return [self._get_value(arg) for arg in args]

    def _get_values_from_stack(self, count: int) -> any:
        values = [self.stack[-num-1] for num in range(count)]
        return values if len(values) != 1 else values[0]

    def _replace_stack_value(self, value: any, count: int) -> None:
        for _ in range(count):
            self.stack.pop()
        self.stack.append(value)

    def _set_value(self, var: str, value: any) -> None:
        var_frame, var_name = self._var_split(var)
        if var_frame not in self.frames:
            exit(55)
        elif var_name not in self.frames[var_frame]:
            exit(54)  # Error
        self.frames[var_frame][var_name] = value

    # Redesign
    def _operator(self, symb1: str, symb2: str, op: str) -> any:
        value1, value2 = self._get_some_values(symb1, symb2)

        if op in {'+', '-', '*'}:
            if type(value1) != type(value2) or type(value1) not in (int, float) or type(value2) not in (int, float):
                exit(53)  # Error
            return eval(f'value1 {op} value2')
        if op in {'<', '>'}:
            if type(value1) != type(value2) or value1 is None:
                exit(53)  # Error
            return eval(f'value1 {op} value2')
        if op == '==':
            if type(value1) != type(value2) and value1 is not None and value2 is not None:
                exit(53)  # Error
            return value1 == value2
        elif op == '//':
            if type(value1) != type(value2) or type(value1) not in (int, float) or type(value2) not in (int, float):
                exit(53)  # Error
            elif value2 == 0:
                exit(57)  # Error
            return value1 // value2
        elif op == '/':
            if type(value1) != type(value2) or type(value1) not in (int, float) or type(value2) not in (int, float):
                exit(53)  # Error
            elif value2 == 0:
                exit(57)  # Error
            return value1 / value2
        elif op == '.':
            if not isinstance(value1, str) or not isinstance(value2, str):
                exit(53)  # Error
            return value1 + value2
        elif op in {'and', 'or'}:
            if not isinstance(value1, bool) or not isinstance(value2, bool):
                exit(53)  # Error
            return eval(f'value1 {op} value2')

    @staticmethod
    def _var_split(var: str) -> list:
        return var.split("@", 1)


class Interpreter:
    def __init__(self, stdin) -> None:
        self.function = Function(stdin)

    def interpret(self, instructions: list) -> None:
        instructions = self._parse_order(instructions)
        self._parse_labels(instructions)
        func = self.function
        while func.position < len(instructions):
            instruction = instructions[func.position]
            attr = f'instr_{instruction.opcode.lower()}'
            args = self._get_args(instruction)
            try:
                executor = getattr(func, attr)
            except AttributeError:
                exit(32)
            self._op_check(executor, args)
            executor(*args)
            func.position += 1

    def _parse_labels(self, instructions: list) -> None:
        for position, instruction in enumerate(instructions):
            if instruction.opcode.upper() == 'LABEL':
                if self._get_args(instruction)[0] in self.function.labels:
                    exit(52)  # Exit
                self.function.labels[self._get_args(instruction)[0]] = position

    @staticmethod
    def _parse_order(instructions: list) -> list:
        orders = []
        for instruction in instructions:
            if instruction.order < 1:
                exit(32)  # Error
            orders.append(instruction.order)
        if len(set(orders)) != len(orders):
            exit(32)  # Error

        return sorted(instructions, key=lambda x: x.order)

    @staticmethod
    def _get_args(instruction: Instruction) -> list:
        """
        Get formatted arguments
        """
        result = []
        for arg in instruction.args:
            if arg.type_.lower() in {'var', 'label', 'type'}:
                result.append(arg.text)
            elif arg.type_.lower() in {'int', 'bool', 'string', 'float'}:
                result.append(f'{arg.type_}@{arg.text}')
            elif arg.type_.lower() == 'nil':
                result.append('nil@nil')
            else:
                exit(56)  # Error
        return result

    @staticmethod
    def _op_check(function: any, args: list) -> None:
        func_code = function.__code__
        argcount = func_code.co_argcount
        func_args = func_code.co_varnames[1:argcount]
        if len(args) != argcount - 1:
            exit(32)  # Error
        for num, arg in enumerate(func_args):
            if arg == 'var' and args[num].split('@')[0] not in {'GF', 'LF', 'TF'}:
                exit(52)  # Error
            elif 'symb' in arg and args[num].split('@')[0] not in {'GF', 'LF', 'TF', 'int',
                                                                   'bool', 'string', 'nil', 'float'}:
                exit(52)  # Error
            elif arg == 'type_' and args[num] not in {'int', 'string', 'bool', 'label', 'nil', 'float'}:
                exit(32)  # Error


def main() -> None:
    stdin = None

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
    # cline_args.input = './tests/read_test.in'
    # cline_args.input = "./tests/my_tests/test1.in"

    # cline_args.source = "./tests/error_string_out_of_range.src"
    # cline_args.source = "./tests/read_test.src"
    # cline_args.source = "./tests/spec_example.src"
    # cline_args.source = "./tests/stack_test.src"
    # cline_args.source = "./tests/write_test.src"
    # cline_args.source = "./tests/my_tests/test1.src"

    try:
        file = cline_args.input
        with open(file, 'r') as f:
            stdin = f.read()
    except TypeError:
        pass

    if cline_args.source or cline_args.input:
        instructions = Instruction.get_instructions_from_xml(cline_args.source)
        inter = Interpreter(stdin)
        inter.interpret(instructions)


if __name__ == '__main__':
    main()
