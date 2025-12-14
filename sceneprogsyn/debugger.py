import os
from uuid import uuid4
from sceneprogllm import LLM, SceneProgTemplate

class SceneProgDebugger:
    def __init__(self, 
                 executor,
                 template: SceneProgTemplate, 
                 model_name="gpt-5", 
                 reasoning_effort="minimal", 
                 max_tries=8, 
                 visualize=False):
        
        self.template = template
        self.MAX_TRIES = max_tries
        self.visualize = visualize
        self.exec = executor
        self.name = self.template.name

        self.code_refine_llm = LLM(
            system_desc=self.get_code_refiner_prompt(),
            response_format="code",
            model_name=model_name,
            reasoning_effort=reasoning_effort
        )

        self.trace_refine_llm = LLM(
            system_desc=self.get_trace_refiner_prompt(),
            response_format="code",
            model_name=model_name,
            reasoning_effort=reasoning_effort
        )

        self.checker_llm = LLM(
            system_desc="""
Given the stdout obtained from the execution of a script.
Check if the script executed successfully or not. Ignore all warnings.
Only check for code crashes! Return True if successful, else False.
Note that if you see no errors in the stdout, it means the code executed successfully.
""",
            response_format="pydantic",
            model_name=model_name,
            reasoning_effort=reasoning_effort
        )

    def header(self):
        try:
            return self.template.get_section("<h>", "</h>")
        except ValueError:
            return ""
        
    def footer(self):
        try:
            return self.template.get_section("<f>", "</f>")
        except ValueError:
            return ""
        
    def example_program(self):
        try:
            return self.template.get_section("<p>", "</p>")
        except ValueError:
            return ""
        
    def runner(self):
        self.using_runner = True
        try:
            return self.template.get_section("<r>", "</r>")
        except ValueError:
            self.using_runner = False
            return f"""
{self.header()}
{self.program}
{self.footer()}
"""     

    def get_code_refiner_prompt(self):
         
        try:
            return self.template.get_section("<cr>", "</cr>")
        except ValueError:
            return (
                "You are an expert in debugging Python and Blender code. "
                "Go through the following code and check for any errors. "
                "Respond with the corrected code only. Don't add any explanations or extra text."
            )
    
    def get_trace_refiner_prompt(self):
        try:
            return self.template.get_section("<tr>", "</tr>")
        except ValueError:
            return (
                "You are an expert in debugging Python and Blender code. "
                "Given the code and the stdout after execution, fix the errors. "
                "Return only the corrected code. Don't add any explanations or extra text."
            )
        
    def fail(self, placeholders):
        try:    
            msg = self.template.get_section("<fail>", "</fail>")
            msg = SceneProgTemplate.format(msg, placeholders)
            return msg
        
        except ValueError:
            return f"Could not debug the code after {self.MAX_TRIES} tries. Reference: {self.name}"

    def is_correct(self, result):
        from pydantic import BaseModel, Field

        class Check(BaseModel):
            success: bool = Field(description="True if the code executed successfully, False otherwise.")
        
        result = self.checker_llm(result, pydantic_object=Check)
        if result.success:
            filename = f"{self.name}.py"
            if os.path.exists(filename):
                os.remove(filename)
        return result.success
    
    def coderefine(self, system_desc_keys):
        prompt = f"""
{self.program}
Refine this code.
"""
        self.program = self.code_refine_llm(prompt, system_desc_keys=system_desc_keys)

    def tracerefine(self, system_desc_keys):
        prompt = f"""
{self.program}
The following script throws an error when executed:
{self.status}
Refine this code.
"""
        self.program = self.trace_refine_llm(prompt, system_desc_keys=system_desc_keys)

    def run(self, placeholders):
        to_run = self.runner()
        to_run = SceneProgTemplate.format(to_run, placeholders)

        filename = f"{self.name}.py"
        if self.using_runner:
            script = f"""
{self.header()}
{self.program}
{self.footer()}
"""
            script = SceneProgTemplate.format(script, placeholders)
            if self.visualize:
                    print("Using runner code with the following script")
                    print(script)

            with open(filename, "w") as f:
                f.write(script)

        elif self.visualize:
            print("Using the following code for execution")
            print(to_run)

        self.status = self.exec(to_run)

        if self.visualize:
            print("Execution status:")
            print(self.status)
            breakpoint()

        return self.status
    
    def __call__(self, program, placeholders=None):
        placeholders['SELF'] = self.name
        self.program = program

        if self.visualize:
            print("Provided placeholders:")
            print(placeholders)
            breakpoint()

        self.coderefine(placeholders)
        count = 0

        while count < self.MAX_TRIES:
            count += 1
            if self.visualize:
                print(f"Try {count} of {self.MAX_TRIES}")
                print("Current program:")
                print(self.program)
                breakpoint()

            self.status = self.run(placeholders)

            if self.is_correct(self.status):
                return self.program

            self.tracerefine(placeholders)

        self.status = self.fail(placeholders)

        return self.status