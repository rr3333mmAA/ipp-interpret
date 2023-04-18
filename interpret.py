#
# Abayev Amirkhan (xabaye00)
#
import argparse
import xml.etree.ElementTree as ET
import re
import sys


class Argument:
    """
    Instruction argument class
    """

    def __init__(self, arg_type: str, text: str) -> None:
        # Initializes an instance of Argument with an argument type and text
        self.type_ = arg_type
        self.text = text

    @classmethod
    def add(cls, arg_type: str, text: str) -> any:
        # Filters the argument type and text and creates a new Argument instance
        arg_type, text = cls._filter_arg(arg_type, text)
        return Argument(arg_type, text)

    @classmethod
    def _filter_arg(cls, arg_type: str, text: str) -> list:
        # Filters the argument type and text depending on its type
        if arg_type == 'bool':
            text = cls._filter_bool(text)
        elif arg_type == 'int':
            cls._filter_int(text)
        elif arg_type == 'string':
            text = cls._filter_string(text)
        elif arg_type == 'type':
            text = cls._filter_type(text)
        elif arg_type == 'float':
            text = cls._filter_float(text)
        return [arg_type, text]

    @staticmethod
    def _filter_bool(text: str) -> str:
        # Filters a boolean argument and returns either 'true' or 'false'
        return 'true' if text.lower() == 'true' else 'false'

    @staticmethod
    def _filter_int(text: str) -> None:
        # Filters an integer argument and exits with error code 32 if not valid
        try:
            int(text)
        except ValueError:
            exit(32)  # Error

    @staticmethod
    def _filter_string(text: str) -> str:
        # Filters a string argument and replaces all unicode escape sequences with their corresponding characters
        matches = set(re.findall(r'\\[0-9]{3}', text))
        for match in matches:
            text = text.replace(match, chr(int(match[1:])))
        return text

    @staticmethod
    def _filter_type(text: str) -> str:
        # Filters a type argument and exits with error code 56 if not valid
        text = text.lower()
        if text not in {'int', 'string', 'bool', 'float'}:
            exit(56)  # Error
        return text

    @staticmethod
    def _filter_float(text: str) -> float:
        # Filters a float argument and exits with error code 32 if not valid
        float_value = None
        try:
            float_value = float.fromhex(text)
        except ValueError:
            pass
        try:
            float.hex(float(float_value))
        except ValueError:
            exit(32)  # Error
        return float_value


class Instruction:
    """
    Instruction class
    """
    all_ = []

    def __init__(self, order: int, opcode: str, args: list) -> None:
        # Initialize an instance of Instruction with an order, opcode and list of arguments
        self.order = order
        self.opcode = opcode
        self.args = args

        Instruction.all_.append(self)

    @classmethod
    def get_instructions_from_xml(cls, src: str) -> list:
        # Parse an XML file and return structured instructions
        root = cls._parse_xml(src)
        cls._validate_root(root)

        for instr in root:
            cls._parse_instruction(instr)

        return cls.all_

    # Secondary functions
    @classmethod
    def _parse_instruction(cls, instr: ET.Element) -> None:
        # Parse an instruction and append it to the 'all_' list
        args = []
        for num in range(len(instr)):
            arg = instr.find(f'arg{num + 1}')
            arg_num, arg_value = cls._validate_argument(arg, num)
            args.append(arg_value)
        order, opcode = cls._validate_instruction(instr)
        Instruction(order=order, opcode=opcode, args=args)

    @staticmethod
    def _parse_xml(src: str) -> ET.Element:
        # Parse an XML file and return its root
        try:
            root = ET.parse(src).getroot()
        except ET.ParseError:
            exit(31)  # Error
        return root

    @staticmethod
    def _validate_root(root: ET.Element) -> None:
        # Check if the root tag and language attribute are valid
        if root.tag != 'program' or root.attrib['language'] != 'IPPcode23':
            exit(32)  # Error

    @staticmethod
    def _validate_instruction(instr: ET.Element) -> tuple:
        # Check if the instruction tag, 'order' and 'opcode' attributes are valid
        if instr.tag != 'instruction' or 'order' not in instr.attrib or 'opcode' not in instr.attrib:
            exit(32)  # Error
        try:
            order = int(instr.get('order'))
        except ValueError:
            exit(32)  # Error
        return order, instr.get('opcode')

    @staticmethod
    def _validate_argument(arg: ET.Element, num: int) -> tuple:
        # Check if the argument is valid and return its index and an instance of Argument class
        if arg is None or 'type' not in arg.attrib:
            exit(32)  # Error
        text = arg.text.strip() if arg.text is not None else ''
        return num, Argument.add(arg.get('type'), text)


class Function:
    """
    Function class
    """
    def __init__(self, stdin) -> None:
        # Initialize the interpreter with the given input
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
        # Move the value of a symb to a variable
        value = self._get_value(symb)
        self._set_value(var, value)

    def instr_createframe(self) -> None:
        # Create a new temporary frame
        self.frames["TF"] = {}

    def instr_pushframe(self) -> None:
        # Push the temporary frame onto the frame stack
        if "TF" not in self.frames:
            exit(55)  # Error
        self.frame_stack.append(self.frames["LF"])
        self.frames["LF"] = self.frames["TF"]
        self.frames["TF"] = None

    def instr_popframe(self) -> None:
        # Pop the top frame off the frame stack
        if not self.frame_stack:
            exit(55)  # Error
        self.frames["TF"] = self.frames["LF"]
        self.frames["LF"] = self.frame_stack.pop()

    def instr_defvar(self, var: str) -> None:
        # Define a new variable in the given frame
        frame, name = self._var_split(var)
        if frame not in {'GF', 'LF', 'TF'}:
            exit(52)  # Error
        if frame == 'TF' and 'TF' not in self.frames:
            exit(55)  # Error
        if name in self.frames[frame]:
            exit(52)  # Error
        self.frames[frame][name] = None

    def instr_call(self, label: str) -> None:
        # Call a function with the given label
        self.call_stack.append(self.position)
        self.instr_jump(label)

    def instr_return(self) -> None:
        # Return from a function call
        if not self.call_stack:
            exit(56)  # Error
        self.position = self.call_stack[-1]
        self.call_stack.pop()

    def instr_pushs(self, symb: str) -> None:
        # Push a symb value onto the stack
        value = self._get_value(symb)
        self.stack.append(value)

    def instr_pops(self, var: str) -> None:
        # Pop the top value off the stack and move it to a variable
        if not self.stack:
            exit(56)  # Error
        value = self.stack[-1]
        self._set_value(var, value)
        self.stack.pop()

    def instr_clears(self) -> None:
        # Clear the stack
        self.stack = []

    def instr_add(self, var: str, symb1: str, symb2: str) -> None:
        # Add two symbs together and store the result in a variable
        value = self._operator(symb1, symb2, '+')
        self._set_value(var, value)

    def instr_adds(self) -> None:
        # Adds two values from the top of the stack and replaces them with their sum
        value1, value2 = self._get_values_from_stack(2)
        if type(value1) != type(value2) != int:
            exit(53)  # Error
        value = value1 + value2
        self._replace_stack_value(value, 2)

    def instr_sub(self, var: str, symb1: str, symb2: str) -> None:
        # Subtracts two symbs and sets the result to a given variable
        value = self._operator(symb1, symb2, '-')
        self._set_value(var, value)

    def instr_subs(self) -> None:
        # Subtracts two values from the top of the stack and replaces them with their difference
        value1, value2 = self._get_values_from_stack(2)
        if type(value1) != type(value2) != int:
            exit(53)  # Error
        value = value2 - value1
        self._replace_stack_value(value, 2)

    def instr_mul(self, var: str, symb1: str, symb2: str) -> None:
        # Multiplies two symbs and sets the result to a given variable
        value = self._operator(symb1, symb2, '*')
        self._set_value(var, value)

    def instr_muls(self) -> None:
        # Multiplies two values from the top of the stack and replaces them with their product
        value1, value2 = self._get_values_from_stack(2)
        if type(value1) != type(value2) != int:
            exit(53)  # Error
        value = value1 * value2
        self._replace_stack_value(value, 2)

    def instr_div(self, var: str, symb1: str, symb2: str) -> None:
        # Divides two symbs and sets the result to a given variable
        value = self._operator(symb1, symb2, '/')
        self._set_value(var, value)

    def instr_idiv(self, var: str, symb1: str, symb2: str) -> None:
        # Integer divides two symbs and sets the result to a given variable
        value = self._operator(symb1, symb2, '//')
        self._set_value(var, value)

    def instr_idivs(self) -> None:
        # Integer divides two values from the top of the stack and replaces them with their quotient
        value1, value2 = self._get_values_from_stack(2)
        if type(value1) != type(value2) != int:
            exit(53)  # Error
        value = value2 // value1
        self._replace_stack_value(value, 2)

    def instr_lt(self, var: str, symb1: str, symb2: str) -> None:
        # Compares two symbs and sets the result to a given variable if the first value is less than the second
        value = self._operator(symb1, symb2, '<')
        self._set_value(var, value)

    def instr_lts(self) -> None:
        # Compares two values from the top of the stack and replaces them with a boolean indicating
        # if the second value is less than the first
        value1, value2 = self._get_values_from_stack(2)
        if type(value1) != type(value2) or value1 is None:
            exit(53)  # Error
        value = value2 < value1
        self._replace_stack_value(value, 2)

    def instr_gt(self, var: str, symb1: str, symb2: str) -> None:
        # Compares two symbs and sets the result to a given variable if the first value is greater than the second
        value = self._operator(symb1, symb2, '>')
        self._set_value(var, value)

    def instr_gts(self) -> None:
        # Compares two values from the top of the stack and replaces them with a boolean indicating
        # if the second value is greater than the first
        value1, value2 = self._get_values_from_stack(2)
        if type(value1) != type(value2) or value1 is None:
            exit(53)  # Error
        value = value2 > value1
        self._replace_stack_value(value, 2)

    def instr_eq(self, var: str, symb1: str, symb2: str) -> None:
        # Compares two symbs and sets the result to a given variable if values are equal
        value = self._operator(symb1, symb2, '==')
        self._set_value(var, value)

    def instr_eqs(self) -> None:
        # Compares two values from the top of the stack and replaces them with a boolean indicating
        # if values are equal
        value1, value2 = self._get_values_from_stack(2)
        if type(value1) != type(value2) and value1 is not None and value2 is not None:
            exit(53)  # Error
        value = value1 == value2
        self._replace_stack_value(value, 2)

    def instr_and(self, var: str, symb1: str, symb2: str) -> None:
        # Performs a logical AND operation on two symbs and sets the result to a variable
        value = self._operator(symb1, symb2, 'and')
        self._set_value(var, value)

    def instr_ands(self) -> None:
        # Performs a logical AND operation on the top two values in the stack and replaces them with the result
        value1, value2 = self._get_values_from_stack(2)
        if not isinstance(value1, bool) or not isinstance(value2, bool):
            exit(53)  # Error
        value = value1 and value2
        self._replace_stack_value(value, 2)

    def instr_or(self, var: str, symb1: str, symb2: str) -> None:
        # Performs a logical OR operation on two symbs and sets the result to a variable
        value = self._operator(symb1, symb2, 'or')
        self._set_value(var, value)

    def instr_ors(self) -> None:
        # Performs a logical OR operation on the top two values in the stack and replaces them with the result
        value1, value2 = self._get_values_from_stack(2)
        if not isinstance(value1, bool) or not isinstance(value2, bool):
            exit(53)  # Error
        value = value1 or value2
        self._replace_stack_value(value, 2)

    def instr_not(self, var: str, symb1: str) -> None:
        # Performs a logical NOT operation on a symb and sets the result to a variable
        value = self._get_value(symb1)
        if not isinstance(value, bool):
            exit(53)  # Error
        self._set_value(var, not bool(value))

    def instr_nots(self) -> None:
        # Performs a logical NOT operation on the top value in the stack and replaces it with the result
        value = self._get_values_from_stack(1)
        if not isinstance(value, bool):
            exit(53)  # Error
        value = not value
        self._replace_stack_value(value, 1)

    def instr_int2char(self, var: str, symb: str) -> None:
        # Get the value of symb and check if it is an integer
        value = self._get_value(symb)
        if type(value) is not int:
            exit(53)  # Error
        try:
            # Convert the integer value to a character and set it to var
            self._set_value(var, chr(value))
        except ValueError:
            exit(58)  # Error

    def instr_int2chars(self) -> None:
        # Get the value from the top of the stack and check if it is an integer
        value = self._get_values_from_stack(1)
        if type(value) is not int:
            exit(53)  # Error
        try:
            # Convert the integer value to a character and replace it on the stack
            value = chr(value)
        except ValueError:
            exit(58)  # Error
        self._replace_stack_value(value, 1)

    def instr_int2float(self, var: str, symb: str) -> None:
        # Get the value of symb and check if it is an integer
        value = self._get_value(symb)
        if type(value) is not int:
            exit(53)  # Error
        try:
            # Convert the integer value to a float and set it to var
            self._set_value(var, float(value))
        except ValueError:
            exit(58)  # Error

    def instr_float2int(self, var: str, symb: str) -> None:
        # Get the value of symb and check if it is a float
        value = self._get_value(symb)

        if type(value) is not float:
            exit(53)  # Error
        try:
            # Convert the float value to an integer and set it to var
            self._set_value(var, int(value))
        except ValueError:
            exit(58)  # Error

    def instr_stri2int(self, var: str, symb1: str, symb2: str) -> None:
        # Get the values of symb1 and symb2, and check their types
        value, index = self._get_some_values(symb1, symb2)
        if not isinstance(value, str) or type(index) is not int:
            exit(53)  # Error
        elif index >= len(value):
            exit(58)  # Error
        # Convert the character at the given index to its ASCII code and set it to var
        self._set_value(var, str(ord(value[index])))

    def instr_stri2ints(self) -> None:
        # Get the values from the top of the stack, and check their types
        index, value = self._get_values_from_stack(2)
        if not isinstance(value, str) or type(index) is not int:
            exit(53)  # Error
        elif index >= len(value):
            exit(58)  # Error
        value = str(ord(value[index]))
        # Convert the character at the given index to its ASCII code and replace it on the stack
        self._replace_stack_value(value, 2)

    def instr_read(self, var: str, type_: str) -> None:
        # Read input from standard input or use stdin if input file provided
        value = input() if self.stdin is None else self.stdin
        # Remove newline character from input
        value = value.replace('\n', '')

        # Check if input is empty and set value to None if so
        if value == '':
            value = None
        # Convert input to boolean if type is 'bool'
        elif type_ == 'bool':
            value = value.lower() == 'true'
        # Convert input to integer if type is 'int'
        elif type_ == 'int':
            try:
                value = int(value)
            except ValueError:
                value = None
        # Convert input to float if type is 'float'
        elif type_ == 'float':
            try:
                value = float.fromhex(value)
            except ValueError:
                value = None
        # Set the variable value
        self._set_value(var, value)

    def instr_write(self, symb: str) -> None:
        # Get the value of the symb
        value = self._get_value(symb)
        # Print the value depending on its type
        if isinstance(value, bool):
            print('true' if value else 'false', end='')
        elif value is None:
            print('', end='')
        elif type(value) is float:
            print(float.hex(value), end='')
        else:
            print(value, end='')

    def instr_concat(self, var: str, symb1: str, symb2: str) -> None:
        # Concatenate the values of two symbs and set the result as the value of the variable
        value = self._operator(symb1, symb2, '.')
        self._set_value(var, value)

    def instr_strlen(self, var: str, symb: str) -> None:
        # Get the value of the symb and check that it is a string
        value = self._get_value(symb)
        if not isinstance(value, str):
            exit(53)  # Error
        # Set the variable value to the length of the string
        self._set_value(var, len(value))

    def instr_getchar(self, var: str, symb1: str, symb2: str) -> None:
        # Get the values of the two symbs and check that they are of the correct types
        value, index = self._get_some_values(symb1, symb2)
        if type(index) is not int or not isinstance(value, str):
            exit(53)  # Error
        # Check that the index is within bounds
        elif index >= len(value):
            exit(58)  # Error
        # Set the variable value to the character at the specified index in the string
        self._set_value(var, value[index])

    def instr_setchar(self, var: str, symb1: str, symb2: str) -> None:
        # Get the values of the two symbs and check that they are of the correct types
        index, char = self._get_some_values(symb1, symb2)
        var_value = self._get_value(var)
        if type(index) is not int or not isinstance(char, str):
            exit(53)  # Error
        # Check that the index is within bounds
        elif index >= len(var_value):
            exit(58)  # Error
        # Replace the character at the specified index in the string with the new character
        value = var_value[:index] + char + var_value[index + 1:]
        self._set_value(var, value)

    def instr_type(self, var: str, symb: str) -> None:
        # Dynamically detects the symb type and writes a string denoting that type to variable
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
        # Labels are placed in advance, pass is left so that there is no error
        pass

    def instr_jump(self, label: str) -> None:
        # Jump instruction, which sets the program's position
        # to the position of the specified label
        if label not in self.labels:
            exit(52)  # Error
        self.position = self.labels[label]

    def instr_jumpifeq(self, label: str, symb1: str, symb2: str) -> None:
        # Jumps to the specified label if the values of the two specified symbs are equal
        value1, value2 = self._get_some_values(symb1, symb2)
        if type(value1) != type(value2) and value1 is not None and value2 is not None:
            exit(53)  # Error
        if value1 == value2:
            self.instr_jump(label)

    def instr_jumpifeqs(self, label: str) -> None:
        # Jumps to the specified label if the values of the top two values on the stack are equal
        value2, value1 = self._get_values_from_stack(2)
        if type(value1) != type(value2) and value1 is not None and value2 is not None:
            exit(53)  # Error
        if value1 == value2:
            self.instr_jump(label)
        self.stack.pop()
        self.stack.pop()

    def instr_jumpifneq(self, label: str, symb1: str, symb2: str) -> None:
        # Jumps to the specified label if the values of the two specified symbs are not equal
        value1, value2 = self._get_some_values(symb1, symb2)
        if type(value1) != type(value2) and value1 is not None and value2 is not None:
            exit(53)  # Error
        if value1 != value2:
            self.instr_jump(label)

    def instr_jumpifneqs(self, label: str) -> None:
        # Jumps to the specified label if the values of the top two values on the stack are not equal
        value2, value1 = self._get_values_from_stack(2)
        if type(value1) != type(value2) and value1 is not None and value2 is not None:
            exit(53)  # Error
        if value1 != value2:
            self.instr_jump(label)
        self.stack.pop()
        self.stack.pop()

    def instr_exit(self, symb: str) -> None:
        # Exits program with a given value (must be an integer in range 0-49)
        value = self._get_value(symb)
        if type(value) is not int:
            exit(53)  # Error
        if value < 0 or value > 49:
            exit(57)  # Error
        exit(value)

    def instr_dprint(self, symb: str) -> None:
        # Prints value of a given symb to standard error stream
        value = self._get_value(symb)
        print(value, file=sys.stderr)

    def instr_break(self) -> None:
        # Prints current position to standard error stream
        print(self.position, file=sys.stderr)

    # Secondary functions
    def _get_value(self, symb: str) -> any:
        # This method retrieves a value from a given symbl string
        value = symb.split('@', 1)
        # Possible types are 'GF', 'LF', 'TF', 'int', 'bool', 'nil', 'float'
        if value[0] in {'GF', 'LF', 'TF'}:
            if value[0] not in self.frames or self.frames[value[0]] is None:
                # Raises errors if the frame or variable does not exist, or if the value is not in a valid format
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
        # Returns a list of values obtained by getting the values of each argument using _get_value()
        return [self._get_value(arg) for arg in args]

    def _get_values_from_stack(self, count: int) -> any:
        # Returns the values from the stack for the specified count,
        # where count is the number of values to get from the stack
        values = [self.stack[-num-1] for num in range(count)]
        return values if len(values) != 1 else values[0]

    def _replace_stack_value(self, value: any, count: int) -> None:
        # Remove count number of values from the stack and add the new value
        for _ in range(count):
            self.stack.pop()
        self.stack.append(value)

    def _set_value(self, var: str, value: any) -> None:
        # Set the value of the variable
        var_frame, var_name = self._var_split(var)
        if var_frame not in self.frames:
            exit(55)  # Error
        elif var_name not in self.frames[var_frame]:
            exit(54)  # Error
        self.frames[var_frame][var_name] = value

    # Redesign
    def _operator(self, symb1: str, symb2: str, op: str) -> any:
        #  It retrieves the values associated with these symbs using the _get_some_values method
        #  and performs an operation based on the operator provided
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
        # Splits variable into a list of frame and variable name
        return var.split("@", 1)


class Interpreter:
    """
    Interpreter class
    """
    def __init__(self, stdin) -> None:
        # Initializing the Interpreter class with input provided by stdin
        self.function = Function(stdin)

        # Variables for statistics
        self.insts = 0
        self.hot_counter = {}
        self.hot = None
        self.vars = 0
        self.frequent = {}

    def interpret(self, instructions: list) -> None:
        # Parses the instructions, executes them, and updates statistics variables
        instructions = self._parse_order(instructions)
        self._parse_labels(instructions)
        self._execute_instructions(instructions)

        # Methods for statistics
        self._frequent(instructions)
        self._sort_hot_counters()
        self._update_hot(instructions)

    # Secondary functions
    def _execute_instructions(self, instructions: list) -> None:
        # Executes the instructions
        func = self.function
        while func.position < len(instructions):
            self._inc_hot_counter(func.position)
            self._count_vars(func)
            instruction = instructions[func.position]
            attr = f'instr_{instruction.opcode.lower()}'
            args = self._get_args(instruction)
            executor = self._get_executor(attr)
            self._op_check(executor, args)
            executor(*args)
            self._inc_insts(instruction)
            func.position += 1

    def _frequent(self, instrs: list) -> None:
        # Count how many times each instruction appears in the instructions list
        for instr in instrs:
            if instr.opcode not in self.frequent:
                self.frequent[instr.opcode] = 1
            else:
                self.frequent[instr.opcode] += 1

    def _inc_insts(self, instr: any) -> None:
        # Increment insts counter if the instruction executed
        if instr.opcode not in {'LABEL', 'DPRINT', 'BREAK'}:
            self.insts += 1

    def _count_vars(self, func: any) -> None:
        # Get the maximum number of initialized variables present at any one time in all valid frames
        res = sum(len(frame) for frame in func.frames)
        if res > self.vars:
            self.vars = res

    def _inc_hot_counter(self, position: int) -> None:
        # Increament hot counte
        if position not in self.hot_counter:
            self.hot_counter[position] = 0
        self.hot_counter[position] += 1

    def _get_executor(self, attr: str):
        # Get executor method from Function class
        try:
            executor = getattr(self.function, attr)
        except AttributeError:
            exit(32)
        return executor

    def _sort_hot_counters(self) -> None:
        # Sort hot counters in descending order by their values
        self.hot_counter = dict(sorted(self.hot_counter.items(), key=lambda x: x[1], reverse=True))

    def _update_hot(self, instructions: list) -> None:
        # Update hot instruction order based on the most executed instruction
        for key in self.hot_counter:
            if instructions[key].opcode not in {'LABEL', 'DPRINT', 'BREAK'}:
                self.hot = instructions[key].order
                return

    def _parse_labels(self, instructions: list) -> None:
        # Sets labels to the labels dictionary
        for position, instruction in enumerate(instructions):
            if instruction.opcode.upper() == 'LABEL':
                if self._get_args(instruction)[0] in self.function.labels:
                    exit(52)  # Error
                self.function.labels[self._get_args(instruction)[0]] = position

    @staticmethod
    def _parse_order(instructions: list) -> list:
        # Parse order of instructions, and sort by their order
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
        # Get formatted arguments
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
        # Check if the instruction arguments are valid
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


class Statistic:
    """
    Statistic class
    """
    def __init__(self) -> None:
        # Initializes a Statistic class with the interpreter and print_arg attributes
        self.interpreter = None
        self.print_arg = None

    def stats(self, interpreter: Interpreter, args: list, file: str, print_arg: list) -> None:
        # Method to calculate and write statistics to a file based on given arguments
        self.interpreter = interpreter
        self.print_arg = print_arg
        with open(file, 'w') as file:
            for arg in args:
                arg = arg.lower().lstrip('--')
                arg = re.sub('=.*', '', arg)
                try:
                    method = getattr(self, f'arg_{arg}')
                    string = str(method())+'\n'
                    file.write(string)
                except (TypeError, AttributeError):
                    pass

    def arg_insts(self):
        # Return insts
        inter = self.interpreter
        return inter.insts

    def arg_hot(self):
        # Return hot
        inter = self.interpreter
        return inter.hot

    def arg_vars(self):
        # Return vars
        inter = self.interpreter
        return inter.vars

    def arg_frequent(self):
        # Return frequent
        inter = self.interpreter
        d = inter.frequent
        max_value = max(d.values())
        keys = [k for k, v in d.items() if v == max_value]
        return ', '.join(keys)

    def arg_print(self):
        # Return print
        res = self.print_arg[0]
        self.print_arg.pop(0)
        return res

    @staticmethod
    def arg_eol():
        # Return EOL
        return '\n'


def parse_args() -> argparse.Namespace:
    # This function defines a parser for command line arguments
    # and returns the parsed arguments
    # [--source=SOURCE] [--input=INPUT] [--stats=STATS] [--insts] [--hot] [--vars] [--frequent] [--print=PRINT] [--eol]
    parser = argparse.ArgumentParser(
        description='The script loads an XML representation of a program '
                    'interprets the program using input according to command line parameters '
                    'and generates output.'
    )
    parser.add_argument('--source', type=str, help="An source file with an XML representation of the source code")
    parser.add_argument('--input', type=str, help="Input file for using as standard input")  # Change help
    parser.add_argument('--stats', type=str, help="Get the code interpretation statistics")
    parser.add_argument('--insts', action='store_true', help="Listing the number of executed instructions")
    parser.add_argument('--hot', action='store_true', help="Returns value of the order instruction attribute "
                                                           "that was executed the most times and has the "
                                                           "smallest value of the order attribute")
    parser.add_argument('--vars', action='store_true', help="List the maximum number of initialized variables present "
                                                            "at one time in all valid frames")
    parser.add_argument('--frequent', action='store_true', help="Returns the names of the most common operation codes")
    parser.add_argument('--print', action='append', help="Prints the string string to the statistics")
    parser.add_argument('--eol', action='store_true', help="Prints the end of line")
    try:
        args = parser.parse_args()
    except SystemExit:
        exit(10)

    # Check if stats arguments were called without '--stats'
    if not args.stats and (args.insts or args.hot or args.vars or args.frequent or args.print or args.eol):
        exit(10)

    return args


def get_stdin(input_file: str) -> str:
    # Get standard input from a file specified by the input_file
    try:
        with open(input_file, 'r') as f:
            stdin = f.read()
    except TypeError:
        exit(11)
    return stdin


def main() -> None:
    # Entry point of the program
    args = parse_args()

    source = args.source
    if source is not None:
        input_file = args.input
        stdin = get_stdin(input_file) if input_file is not None else None

        instructions = Instruction.get_instructions_from_xml(source)
        inter = Interpreter(stdin)
        inter.interpret(instructions)

        stats = args.stats
        if stats is not None:
            print_arg = args.print
            Statistic().stats(inter, sys.argv, stats, print_arg)


if __name__ == '__main__':
    main()
