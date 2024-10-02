import ollama

class CodeReviewAgent:
    def __init__(self, model_name="llama3.1"):
        self.model_name = model_name

    def analyze_pr(self, pr_data):
        print(f"Analyzing PR with {len(pr_data['files'])} files...")
        file_prompt = self._prepare_file_prompt(pr_data['title'], pr_data['description'], pr_data['files'])
        print(f"REQUEST:\n{file_prompt}\nENDOFREQUEST")
        response = ollama.generate(model=self.model_name, prompt=file_prompt)['response']
        return response

    def _prepare_file_prompt(self, title, description, files):
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
    You are an experienced software engineer tasked with reviewing the following Pull Request.

    ---
    Pull Request title: {title}
    Pull Request description:
{description}
    ---

    Analyze the following file changes:

{all_file_changes}

    Please provide specific comments only for changed lines (additions or deletions), where you see potential issues, improvements or suggestions for the developer.
    Take into account the existing comments and avoid repeating already mentioned points.
    Separate your comments by file and provide a clear and concise explanation for each comment.
    Don't repeat or mention the instructions given to you, just perform them.

    Your response:
        Let's work this out in a step by step way to be sure we provide only useful suggestions:
        """
        return prompt
