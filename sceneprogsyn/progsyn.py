from sceneprogllm import LLM
from .debugger import SceneProgDebugger

class SceneProgSyn:
    '''
    SceneProgSyn writes a program to solve a user query. It comes with a built-in debugger.
    The code is executed with an execution environment such as Blender. 
    '''
    def __init__(self, system_desc, model_name="gpt-5", reasoning_effort="medium"):

        self.core = LLM(
            system_desc=system_desc,
            response_format="code",
            model_name=model_name,
            reasoning_effort=reasoning_effort
        )

        self.debugger = None

    def add_debugger(self, debugger):
        if not isinstance(debugger, SceneProgDebugger):
            raise ValueError("Debugger must be an instance of SceneProgDebugger")
        self.debugger = debugger

    def build_context(self, query, feedback=None):
        prompt = f"""
User query: {query}
"""
        if feedback:
            prompt += f"""
You had previously written the following program to solve the query:
{self.program}
The following feedback was provided based on its execution:
{feedback}
Please write a new program to solve the query, taking into account the feedback provided.
"""
        return prompt

    def __call__(self, query, debugger_context=None, feedback=None, **kwargs):
        if feedback and not self.program:
            raise ValueError("Feedback provided but no previous program to improve upon.")
        
        prompt = self.build_context(query, feedback)
        program = self.core(prompt)
        if self.debugger:
            program = self.debugger(program, placeholders=debugger_context, **kwargs)

        self.program = program
        return program
    