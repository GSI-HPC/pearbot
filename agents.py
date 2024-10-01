import ollama

class CodeReviewAgent:
    def __init__(self, model_name="llama3.1"):
        self.model_name = model_name

    def analyze_pr(self, pr_data):
        print(f"Analyzing PR with {len(pr_data['files'])} files...")
        file_prompt = self._prepare_file_prompt(pr_data['files'], pr_data['existing_comments'])
        print(f"REQUEST:\n{file_prompt}\nENDOFREQUEST")
        response = ollama.generate(model=self.model_name, prompt=file_prompt)['response']
        return response

    def _prepare_file_prompt(self, files, existing_comments):
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
    Please analyze the following file changes in a Pull Request:
{all_file_changes}

    Please provide specific comments only for changed lines (additions or deletions), where you see potential issues, improvements or suggestions for the developer.
    Take into account the existing comments and avoid repeating already mentioned points.
    Separate your comments by file and provide a clear and concise explanation for each comment.
    Don't repeat or mention the instructions given to you, just perform them.

    Your response:
        Let's work this out in a step by step way to be sure we provide useful suggestions:
        """
        return prompt

    # def _summarize_existing_comments(self, comments):
    #     summary = []
    #     for comment in comments:
    #         if comment['type'] == 'issue_comment':
    #             summary.append(f"Issue comment by {comment['user']}: {comment['body'][:300]}...")
    #         else:  # review_comment
    #             summary.append(f"Review comment by {comment['user']} on {comment['path']}: {comment['body'][:300]}...")
    #     return "\n".join(summary)
