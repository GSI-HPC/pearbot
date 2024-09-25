import ollama

class Agent:
    def __init__(self, model_name="llama3.1"):
        self.model_name = model_name

    def analyze_pr(self, pr_data):
        file_comments = {}
        for file in pr_data['files']:
            file_prompt = self._prepare_file_prompt(file)
            response = ollama.generate(model=self.model_name, prompt=file_prompt)
            file_comments[file['filename']] = self._parse_line_comments(response['response'])
        return file_comments

    def _prepare_file_prompt(self, file):
        prompt = f"""
        Analyze the following file changes in a Pull Request:

        Filename: {file['filename']}
        Status: {file['status']}
        Additions: {file['additions']}
        Deletions: {file['deletions']}
        Changes:
        {file['patch']}

        Please provide specific comments for changed lines. Format your response as follows:
        LINE_NUMBER: Your comment about this line
        LINE_NUMBER: Another comment about a different line

        Focus on potential issues, improvements, and suggestions for the developer.
        If a change looks good, comment with only "LGTM".

        Your response:
        """
        return prompt

    def _parse_line_comments(self, response):
        comments = {}
        for line in response.split('\n'):
            if ':' in line:
                line_number, comment = line.split(':', 1)
                try:
                    line_number = int(line_number.strip())
                    comments[line_number] = comment.strip()
                except ValueError:
                    continue  # Skip lines that don't start with a number
        return comments

class CodeReviewAgent(Agent):
    def __init__(self):
        super().__init__(model_name="llama3.1")

# You can add more specialized agents here in the future
