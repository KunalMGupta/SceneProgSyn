# SceneProgSyn

SceneProgSyn is an LLM-based module for generating Python-like code in any domain-specific language. This project depends on other SceneProg packages.

---

## Installation

Install the package and its dependencies with:

```bash
pip install sceneprogsyn
```

---

## Getting Started

### Importing the package
```python
from sceneprogsyn import SceneProgSyn, SceneProgDebugger
```

The package contains two key components:
- SceneProgSyn: the main LLM-based coder
- SceneProgDebugger: a powerful debugger that iterates through CodeRefine and TraceRefine steps to debug code

---

## Working with an Example DSL

### Language
SceneProgSyn shines when working with a custom DSL (Domain Specific Language), such as Blender Shader nodes, an Interior Design Inspired DSL (IDSDL, Gupta et al., 3D Vision 2026), CARLA, and more. For demonstration, we use an English Math DSL—a minimal, Python-like DSL that uses English words for numbers and operators to illustrate language design and interpretation.

This DSL supports:
- Numbers written in words (e.g., one, two, three, …, twenty)
- Arithmetic using English words (plus, minus, times, divided_by, power)
- Variable assignments using Python-style syntax
- Parentheses for precedence
- Output via a print statement

Note: This DSL prioritizes clarity and simplicity to support educational demos and quick prototyping.

```python
doc = """
**Numbers**  
Numbers are written using English words instead of digits.  
Examples: `zero`, `one`, `two`, `three`, `four`, `five`, … `twenty`  
(Unlike traditional numeric literals such as `0`, `1`, `2`.)

**Arithmetic Operations**  
Arithmetic operators are expressed as English words rather than symbols.

- `plus` — addition (instead of `+`)
- `minus` — subtraction (instead of `-`)
- `times` — multiplication (instead of `*`)
- `divided_by` — division (instead of `/`)
- `power` — exponentiation (instead of `**`)

**Variables**  
Variables follow Python-style naming rules and are assigned using `=`.

x = five plus three
"""
```

---

### Execution Environment
Below is a simple execution environment for running the DSL. The `__call__` method returns a status/output reflecting the execution state.

```python
class Exec:
    def __init__(self):
        pass
    def __call__(self, code):
        return run_dsl(code)
```

---

## Setting Up SceneProgSyn

First, initialize the SceneProgSyn object:

```python
progsyn = SceneProgSyn(
    system_desc=f"""
You write Python programs in a custom DSL to solve user queries.
{doc}
""",
)
```

Next, configure the SceneProgDebugger. This involves writing a template that specifies the pieces required for writing programs in the DSL and provides prompts for the LLM-based debugging. To achieve this, define a `SceneProgTemplate`.

```python
from sceneprogllm import SceneProgTemplate

template = SceneProgTemplate(
"""
<h>

</h>

<cr> 
You are an expert in Python scripting in a custom DSL. I want you to debug the following code by referring to the provided API doc.
$doc
An example of a valid output is:

a = two
b = three
c = a plus b
print c

</cr>

<tr>
You are an expert in Python scripting in a custom DSL. I want you to debug the following code by referring to the provided API doc.
$doc
You will be given a Python script that, along with the traceback, contains errors obtained by running the script.
Your task is to fix the code. An example of a valid output is:

a = two
b = three
c = a plus b
print c

</tr>

<f>

</f>
""",
)
```

- `<h> ... </h>` is the program header, which typically contains imports and other setup crucial for execution but not strictly required to generate the full program.
- `<cr> ... </cr>` and `<tr> ... </tr>` are the system prompts for CodeRefine and TraceRefine LLMs, respectively.
- `<f> ... </f>` can be used to specify footer code (e.g., exporting results). Like the header, it is not required for program generation.
- The `SceneProgTemplate` supports injecting runtime variables via `$`, which is useful for passing information to the debuggers.

Putting this together with SceneProgSyn:

```python
debugger = SceneProgDebugger(Exec(), template, visualize=False)
progsyn.add_debugger(debugger)
```

---

## A Simple DSL Program

Now, let's try writing a simple program in our DSL.

```python
code = progsyn(
    "Write code to compute the function x^3 + 2*x^2 + x + 1",
    debugger_context={"doc": doc}
)
print("Generated Code:\n", code)
```

Example (generated DSL code):

```python
# Define polynomial coefficients as variables
a = one
b = one
c = two
d = zero
e = one

# Evaluate polynomial f(x) = x^3 + 2x^2 + x + 1 using only expressions
x = three

x2 = x times x
x3 = x power three

term1 = x3
term2 = c times x2
term3 = b times x
term4 = a

result = term1 plus term2 plus term3 plus term4

print result
```

Notes:
- The example demonstrates how the DSL uses English words to express numbers and operations.
- The debugger template and the debugger workflow are designed to iteratively refine code to meet the DSL’s API and semantics.