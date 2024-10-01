import ollama

class Agent:
    def __init__(self, model_name="llama3.1"):
        self.model_name = model_name

    def analyze_pr(self, pr_data):
        print(f"Analyzing PR with {len(pr_data['files'])} files...")
        file_prompt = self._prepare_file_prompt(pr_data['files'])
        print(f"REQUEST:\n{file_prompt}\nENDOFREQUEST")
        response = ollama.generate(model=self.model_name, prompt=file_prompt)['response']
        # print(f"RESPONSE:\n{response}\nENDOFRESPONSE")
        return response

    def _prepare_file_prompt(self, files):
        file_changes = []
        for file in files:
            file_changes.append(f"""
    Filename: {file['filename']}
    Status: {file['status']}
    Additions: {file['additions']}
    Deletions: {file['deletions']}
    Changes:
{file['patch']}
""")
        all_file_changes = "\n---\n".join(file_changes)

        prompt = f"""
    Analyze the following file changes in a Pull Request:
{all_file_changes}

    Please provide specific comments only for changed lines (additions or deletions), where you see potential issues, improvements or suggestions for the developer.
    Format your response as follows:
    FILENAME: All your comment about this file
    FILENAME: Another comment about a different file

    Your response:
        """
        return prompt

class CodeReviewAgent(Agent):
    def __init__(self):
        super().__init__(model_name="llama3.1")