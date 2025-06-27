import ollama
import yaml

from .model import post_request_generate

class Agent:
    def __init__(self, role="code_reviewer", use_post_request=False, prompt_style="default"):
        self.role = role
        self.use_post_request = use_post_request
        self.prompt_style = prompt_style
        self.prompts = self._load_prompts()
        print(f"Initialized agent with role: {role}, use_post_request: {use_post_request}, prompt_style: {prompt_style}")

    def _load_prompts(self):
        with open('src/prompts.yaml', 'r') as file:
            return yaml.safe_load(file)['prompts']

    def analyze(self, data, model: str):
        prompt = self._prepare_prompt(data)

        # print(f"Prompt:\n{prompt}\nENDOFPROMPT")

        if self.use_post_request:
            response = post_request_generate(model, prompt)
        else:
            response = ollama.generate(model=model, prompt=prompt)['response']

        return prompt, response

    def _prepare_prompt(self, data):
        if self.role == "code_reviewer":
            return self._prepare_code_review_prompt(data)
        elif self.role == "feedback_improver":
            prompt = self._prepare_feedback_improvement_prompt(data)
            # print(f"IMPROVERPROMPT:\n{prompt}\nENDOFIMPROVERPROMPT")
            return prompt
        else:
            raise ValueError(f"Unknown role: {self.role}")

    def _prepare_code_review_prompt(self, pr_data):
        context = f"Additional Context:\n{pr_data['context']}" if pr_data.get('context') else ""
        return self.prompts['instructions'][self.prompt_style]['review'].format(
            title=pr_data['title'],
            description=pr_data['description'],
            changes=pr_data['changes'],
            context=context,
            examples=self.prompts['examples']
        )

    def _prepare_feedback_improvement_prompt(self, review_data):
        context = f"Additional Context:\n{review_data['pr_data']['context']}" if review_data['pr_data'].get('context') else ""
        reviews = ""
        for i, review in enumerate(review_data['initial_reviews'], 1):
            reviews += f"""
---
Review #{i}:
{review}
---
"""
        return self.prompts['instructions'][self.prompt_style]['feedback'].format(
            title=review_data['pr_data']['title'],
            description=review_data['pr_data']['description'],
            changes=review_data['pr_data']['changes'],
            reviews=reviews,
            context=context,
            examples=self.prompts['examples']
        )