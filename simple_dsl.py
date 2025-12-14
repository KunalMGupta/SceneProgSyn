# dsl_words_math.py
# A super-simple DSL: numbers/operators are written in English words.

import re
from dataclasses import dataclass

# --- 1) Vocabulary -----------------------------------------------------------

NUM_WORDS = {
    "zero": 0, "one": 1, "two": 2, "three": 3, "four": 4,
    "five": 5, "six": 6, "seven": 7, "eight": 8, "nine": 9,
    "ten": 10, "eleven": 11, "twelve": 12, "thirteen": 13, "fourteen": 14,
    "fifteen": 15, "sixteen": 16, "seventeen": 17, "eighteen": 18, "nineteen": 19,
    "twenty": 20,
}

# Operator words -> internal operator token
OP_WORDS = {
    "plus": "+",
    "minus": "-",
    "times": "*",
    "divided_by": "/",
    "power": "**",
}

# Precedence + associativity
PRECEDENCE = {
    "**": (4, "right"),
    "*": (3, "left"),
    "/": (3, "left"),
    "+": (2, "left"),
    "-": (2, "left"),
}

# --- 2) Tokenizer ------------------------------------------------------------

@dataclass(frozen=True)
class Token:
    kind: str  # "NUM", "ID", "OP", "LPAREN", "RPAREN", "EQ"
    value: str

TOKEN_RE = re.compile(
    r"""
    (?P<WS>\s+)
  | (?P<LPAREN>\()
  | (?P<RPAREN>\))
  | (?P<EQ>=)
  | (?P<ID>[A-Za-z_][A-Za-z_0-9]*)
    """,
    re.VERBOSE,
)

def tokenize_expr(expr: str) -> list[Token]:
    """
    Converts 'five plus x times two' into tokens:
    NUM(5), OP(+), ID(x), OP(*), NUM(2)
    """
    tokens: list[Token] = []
    i = 0
    while i < len(expr):
        m = TOKEN_RE.match(expr, i)
        if not m:
            raise SyntaxError(f"Unexpected character at {i}: {expr[i]!r}")

        kind = m.lastgroup
        text = m.group(kind)
        i = m.end()

        if kind == "WS":
            continue
        if kind == "LPAREN":
            tokens.append(Token("LPAREN", text))
            continue
        if kind == "RPAREN":
            tokens.append(Token("RPAREN", text))
            continue
        if kind == "EQ":
            tokens.append(Token("EQ", text))
            continue
        if kind == "ID":
            w = text.lower()
            if w in NUM_WORDS:
                tokens.append(Token("NUM", str(NUM_WORDS[w])))
            elif w in OP_WORDS:
                tokens.append(Token("OP", OP_WORDS[w]))
            else:
                tokens.append(Token("ID", text))
            continue

    return tokens

# --- 3) Parser: Shunting-yard to RPN ----------------------------------------

def to_rpn(tokens: list[Token]) -> list[Token]:
    out: list[Token] = []
    stack: list[Token] = []

    for t in tokens:
        if t.kind in ("NUM", "ID"):
            out.append(t)
        elif t.kind == "OP":
            op = t.value
            p1, assoc1 = PRECEDENCE[op]
            while stack and stack[-1].kind == "OP":
                top = stack[-1].value
                p2, _ = PRECEDENCE[top]
                if (assoc1 == "left" and p1 <= p2) or (assoc1 == "right" and p1 < p2):
                    out.append(stack.pop())
                else:
                    break
            stack.append(t)
        elif t.kind == "LPAREN":
            stack.append(t)
        elif t.kind == "RPAREN":
            while stack and stack[-1].kind != "LPAREN":
                out.append(stack.pop())
            if not stack or stack[-1].kind != "LPAREN":
                raise SyntaxError("Mismatched parentheses")
            stack.pop()  # pop "("
        else:
            raise SyntaxError(f"Unexpected token in expression: {t}")

    while stack:
        if stack[-1].kind in ("LPAREN", "RPAREN"):
            raise SyntaxError("Mismatched parentheses")
        out.append(stack.pop())

    return out

# --- 4) Evaluator ------------------------------------------------------------

def eval_rpn(rpn: list[Token], env: dict[str, int | float]) -> int | float:
    st: list[int | float] = []

    def pop_num() -> int | float:
        if not st:
            raise SyntaxError("Not enough values in expression")
        return st.pop()

    for t in rpn:
        if t.kind == "NUM":
            st.append(int(t.value))
        elif t.kind == "ID":
            if t.value not in env:
                raise NameError(f"Undefined variable: {t.value}")
            st.append(env[t.value])
        elif t.kind == "OP":
            b = pop_num()
            a = pop_num()
            if t.value == "+":
                st.append(a + b)
            elif t.value == "-":
                st.append(a - b)
            elif t.value == "*":
                st.append(a * b)
            elif t.value == "/":
                st.append(a / b)
            elif t.value == "**":
                st.append(a ** b)
            else:
                raise SyntaxError(f"Unknown operator: {t.value}")
        else:
            raise SyntaxError(f"Unexpected token in RPN: {t}")

    if len(st) != 1:
        raise SyntaxError("Expression did not reduce to a single value")
    return st[0]

def eval_expr(expr: str, env: dict[str, int | float]) -> int | float:
    tokens = tokenize_expr(expr)
    rpn = to_rpn(tokens)
    return eval_rpn(rpn, env)

# --- 5) Statement runner -----------------------------------------------------

def run_dsl(program: str) -> dict[str, int | float]:
    """
    Supports:
      - assignment: name = <expr>
      - print:      print <expr>
    """
    env: dict[str, int | float] = {}
    for lineno, raw in enumerate(program.splitlines(), start=1):
        line = raw.strip()
        if not line or line.startswith("#"):
            continue

        if line.lower().startswith("print "):
            expr = line[6:].strip()
            val = eval_expr(expr, env)
            print(val)
            continue

        # assignment: <id> = <expr>
        if "=" in line:
            left, right = line.split("=", 1)
            name = left.strip()
            if not re.fullmatch(r"[A-Za-z_][A-Za-z_0-9]*", name):
                raise SyntaxError(f"Line {lineno}: Invalid variable name: {name!r}")
            val = eval_expr(right.strip(), env)
            env[name] = val
            continue

        raise SyntaxError(f"Line {lineno}: Unknown statement: {line!r}")

    return env

if __name__ == "__main__":
    demo = """
    # Demo of the English-math DSL
    x = five plus six times two
    y = ( five plus six ) times two
    z = two power three plus four
    print x
    print y
    print z
    """
    run_dsl(demo)