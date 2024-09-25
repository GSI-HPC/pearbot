import ollama
from unidiff import PatchSet
import io

class Agent:
    def __init__(self, model_name="llama3.1"):
        self.model_name = model_name

    def analyze_pr(self, pr_data):
        file_comments = {}
        for file in pr_data['files']:
            file_prompt = self._prepare_file_prompt(file)
            print(f"REQUEST:\n{file_prompt}\nENDOFREQUEST")
            response = ollama.generate(model=self.model_name, prompt=file_prompt)
            print(f"RESPONSE:\n{response['response']}\nENDOFRESPONSE")
            file_comments[file['filename']] = self._parse_line_comments(response['response'])
        return file_comments

    def _prepare_file_prompt(self, file):
        parsed_changes = self._parse_patch(file['patch'], file['filename'])
        formatted_changes = self._format_changes(parsed_changes)

        prompt = f"""
        Analyze the following file changes in a Pull Request:
        Filename: {file['filename']}
        Status: {file['status']}
        Additions: {file['additions']}
        Deletions: {file['deletions']}
        Changes (including context):
{formatted_changes}

        Please provide specific comments for changed lines. Format your response as follows:
        LINE_NUMBER: Your comment about this line
        LINE_NUMBER: Another comment about a different line
        Focus on potential issues, improvements, and suggestions for the developer.
        If a change looks good, comment with only "LGTM" and nothing else.
        Your response:
        """
        return prompt

    def _parse_patch(self, patch_content, filename):
        header = f"diff --git a/{filename} b/{filename}\n"
        full_patch = header + patch_content

        patch_set = PatchSet(io.StringIO(full_patch))

        changes = []

        for patched_file in patch_set:
            for hunk in patched_file:
                context_before = []
                context_after = []
                change_lines = []

                for line in hunk:
                    if line.is_context:
                        if len(change_lines) == 0:
                            if len(context_before) < 5:
                                context_before.append((line.target_line_no, ' ' + line.value.rstrip()))
                            else:
                                context_before = context_before[1:] + [(line.target_line_no, ' ' + line.value.rstrip())]
                        else:
                            if len(context_after) < 5:
                                context_after.append((line.target_line_no, ' ' + line.value.rstrip()))
                            else:
                                changes.extend(context_before + change_lines + context_after)
                                context_before = context_after[1:] + [(line.target_line_no, ' ' + line.value.rstrip())]
                                context_after = []
                                change_lines = []
                    elif line.is_added:
                        change_lines.append((line.target_line_no, '+' + line.value.rstrip()))
                    elif line.is_removed:
                        change_lines.append((line.source_line_no, '-' + line.value.rstrip()))

                if change_lines:
                    changes.extend(context_before + change_lines + context_after)

        return changes

    def _format_changes(self, changes):
        return '\n'.join(f"{line_no}: {content}" for line_no, content in changes)

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