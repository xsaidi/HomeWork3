import sys
import yaml
import re
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding='utf-8')
class ParseError(Exception):
    pass
''' Лексер
-------------------------------------------------------
Токены:
def, :=, =, ;, [ , ], q( ... ), $ ... $ (константные выражения), числа, имена, операции + - *
Примерный порядок:
def, имя, :=, значение, ;
имя, =, значение, ;
Значения: число, строка q(...), массив [ ... ], конст. выражение $...$
Конст. выражения: $+ имя 1$, $* имя 2$, $- имя 3$, $chr 65$
-------------------------------------------------------
'''
TOKEN_REGEX = r'''
(?P<WS>\s+)
|(?P<DEF>\bdef\b)
|(?P<ASSIGN_CONST>:=)
|(?P<ASSIGN>=)
|(?P<SEMICOLON>;)
|(?P<LBRACK>\[)
|(?P<RBRACK>\])
|(?P<QSTR>q\([^)]*\))
|(?P<EXPR>\$[^$]*\$)
|(?P<NAME>[_A-Za-z][_0-9A-Za-z]*)
|(?P<NUMBER>-?\d+)
'''

token_pattern = re.compile(TOKEN_REGEX, re.VERBOSE)

def tokenize(s):
    pos = 0
    tokens = []
    while pos < len(s):
        match = token_pattern.match(s, pos)
        if match:
            pos = match.end()
            # Игнорируем пробелы
            if match.lastgroup == 'WS':
                continue
            tokens.append((match.lastgroup, match.group(match.lastgroup)))
        else:
            # Если не можем разобрать токен
            raise ParseError(f"Unexpected character at position {pos}: {s[pos:pos+10]}")
    return tokens

'''
Парсер
-------------------------------------------------------
Грамматика (примерная):
Program: Statement*
Statement: DefStatement | KeyValueStatement
DefStatement: 'def' NAME ':=' Value ';'
KeyValueStatement: NAME '=' Value ';'
Value: Number | Qstr | Array | Expr | NAME
Array: '[' Value* ']'
Expr: '$' ... '$' - константное выражение
Константное выражение: $op arg1 arg2$ или $chr num$
op ∈ {+, -, *}, arg1, arg2 – либо имя константы, либо число
chr – функция chr(num)
-------------------------------------------------------
'''
class Parser:
    def __init__(self, tokens):
        self.tokens = tokens
        self.pos = 0

    def peek(self):
        if self.pos < len(self.tokens):
            return self.tokens[self.pos]
        return None

    def expect(self, type_):
        tok = self.peek()
        if not tok or tok[0] != type_:
            raise ParseError(f"Expected {type_}, got {tok}")
        self.pos += 1
        return tok

    def match(self, type_):
        if self.pos < len(self.tokens) and self.tokens[self.pos][0] == type_:
            self.pos += 1
            return True
        return False

    def parse_program(self):
        statements = []
        while self.peek():
            statements.append(self.parse_statement())
        return statements

    def parse_statement(self):
        # Определение константы или ключ-значение
        # def NAME := Value ;
        # NAME = Value ;
        if self.match('DEF'):
            # def statement
            name = self.expect('NAME')[1]
            self.expect('ASSIGN_CONST')
            val = self.parse_value()
            self.expect('SEMICOLON')
            return ('def', name, val)
        else:
            # NAME = Value ;
            name = self.expect('NAME')[1]
            self.expect('ASSIGN')
            val = self.parse_value()
            self.expect('SEMICOLON')
            return ('assign', name, val)

    def parse_value(self):
        # Value: NUMBER | QSTR | ARRAY | EXPR | NAME
        tok = self.peek()
        if not tok:
            raise ParseError("Unexpected end of input in value")

        ttype, tval = tok
        if ttype == 'NUMBER':
            self.pos += 1
            return ('number', int(tval))
        elif ttype == 'QSTR':
            self.pos += 1
            # q(...) -> строка
            # Формат: q(....)
            inner = tval[2:-1]  # убрать q( и )
            return ('string', inner)
        elif ttype == 'LBRACK':
            return self.parse_array()
        elif ttype == 'EXPR':
            self.pos += 1
            return self.parse_expr(tval)
        elif ttype == 'NAME':
            self.pos += 1
            # Может быть просто имя как значение
            return ('name', tval)
        else:
            raise ParseError(f"Unexpected token {tok} in value")

    def parse_expr(self, expr_str):
        # expr_str включает $ в начале и конце, уберём их
        inner = expr_str[1:-1].strip()
        # Формат: "+ var 1", "- var 2", "* var 3", "chr 65"
        parts = inner.split()
        if not parts:
            raise ParseError("Empty expression")
        if parts[0] in ['+', '-', '*']:
            if len(parts) != 3:
                raise ParseError(f"Wrong number of arguments for expression {inner}")
            op = parts[0]
            arg1 = parts[1]
            arg2 = parts[2]
            return ('expr_op', op, self.parse_expr_arg(arg1), self.parse_expr_arg(arg2))
        elif parts[0] == 'chr':
            if len(parts) != 2:
                raise ParseError(f"Wrong number of arguments for chr in {inner}")
            arg = self.parse_expr_arg(parts[1])
            return ('expr_chr', arg)
        else:
            raise ParseError(f"Unknown expression type {inner}")

    def parse_expr_arg(self, a):
        # arg может быть числом или именем
        if re.match(r'^-?\d+$', a):
            return ('number', int(a))
        else:
            # имя
            return ('name', a)

    def parse_array(self):
        self.expect('LBRACK')
        values = []
        while True:
            if self.match('RBRACK'):
                break
            val = self.parse_value()
            values.append(val)
        return ('array', values)

# Интерпретация и вычисление

def evaluate_constants(statements):
    # statements – список ('def', name, val) или ('assign', name, val)
    # Сначала вычислим все def: они должны содержать только константные значения
    # Пройдем по всем def и вычислим их значения.
    constants = {}
    output = {}

    # Сначала извлечём все def
    # def могут ссылаться друг на друга, надо сделать несколько проходов или рекурсию
    # Предполагаем, что нет циклических зависимостей (иначе ParseError).
    def_defs = [(name, val) for (t, name, val) in statements if t == 'def']
    assigns = [(name, val) for (t, name, val) in statements if t == 'assign']

    # Вычислим все def
    # Попытка решить рекурсивно:
    def resolve_value(v):
        vtype = v[0]
        if vtype == 'number':
            return v[1]
        elif vtype == 'string':
            return v[1]
        elif vtype == 'array':
            return [resolve_value(x) for x in v[1]]
        elif vtype == 'name':
            name = v[1]
            if name not in constants:
                raise ParseError(f"Undefined constant {name}")
            return constants[name]
        elif vtype == 'expr_op':
            # ('expr_op', op, arg1, arg2)
            _, op, a1, a2 = v
            val1 = resolve_value(a1)
            val2 = resolve_value(a2)
            if not (isinstance(val1, int) and isinstance(val2, int)):
                raise ParseError("Arithmetic on non-integers")
            if op == '+':
                return val1 + val2
            elif op == '-':
                return val1 - val2
            elif op == '*':
                return val1 * val2
            else:
                raise ParseError(f"Unknown operation {op}")
        elif vtype == 'expr_chr':
            # ('expr_chr', arg)
            _, arg = v
            val = resolve_value(arg)
            if not isinstance(val, int):
                raise ParseError("chr argument not int")
            return chr(val)
        else:
            raise ParseError(f"Unknown value type {vtype}")

    # Разрешим константы
    # Возможна ситуация, что порядок def не гарантирован.
    # Будем пробовать пока не все разрешены:
    unresolved = True
    known = set()
    defs_map = {n: v for (n, v) in def_defs}

    while True:
        progress = False
        for n, v in defs_map.items():
            if n in known:
                continue
            try:
                val = resolve_value(v)
                constants[n] = val
                known.add(n)
                progress = True
            except ParseError:
                # Возможно, пока не можем вычислить из-за зависимости
                pass
        if not progress:
            # Если не продвинулись и есть неопределённые – ошибка
            if len(known) != len(defs_map):
                missing = set(defs_map.keys()) - known
                raise ParseError(f"Cannot resolve constants: {missing}")
            break

    # Теперь вычислим все assign
    for n, v in assigns:
        output[n] = resolve_value(v)

    return output

def main():
    # Считываем весь вход
    input_text = sys.stdin.read()

    # Удаляем комментарии
    lines = input_text.split('\n')
    no_comments = []
    for line in lines:
        # поиск %
        cpos = line.find('%')
        if cpos != -1:
            line = line[:cpos]
        no_comments.append(line)
    filtered_text = '\n'.join(no_comments)

    # Токенизация
    tokens = tokenize(filtered_text)

    # Парсинг
    parser = Parser(tokens)
    statements = parser.parse_program()

    # Вычисляем и преобразуем
    data = evaluate_constants(statements)

    # Выводим в YAML
    output_str = yaml.dump(data, allow_unicode=True, sort_keys=False)
    print(output_str.encode('utf-8', errors='replace').decode('utf-8', errors='replace'))

if __name__ == "__main__":
    main()
