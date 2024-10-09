import ollama
from prompts import CODE_REVIEW_PROMPT, FEEDBACK_IMPROVEMENT_PROMPT, EXAMPLES

class Agent:
    def __init__(self, model_name="llama3.1", role="code_reviewer"):
        self.model_name = model_name
        self.role = role

    def analyze(self, data, model_name=None):
        prompt = self._prepare_prompt(data)
        model = model_name or self.model_name
        response = ollama.generate(model=model, prompt=prompt)['response']
        return prompt, response

    def _prepare_prompt(self, data):
        if self.role == "code_reviewer":
            return self._prepare_code_review_prompt(data)
        elif self.role == "feedback_improver":
            prompt = self._prepare_feedback_improvement_prompt(data)
            print(f"IMPROVERPROMPT:\n{prompt}\nENDOFIMPROVERPROMPT")
            return prompt
        else:
            raise ValueError(f"Unknown role: {self.role}")

    def _prepare_code_review_prompt(self, pr_data):
        context = f"Additional Context:\n{pr_data['context']}" if pr_data.get('context') else ""
        return CODE_REVIEW_PROMPT.format(
            title=pr_data['title'],
            description=pr_data['description'],
            changes=pr_data['changes'],
            context=context,
            examples=EXAMPLES
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
        return FEEDBACK_IMPROVEMENT_PROMPT.format(
            title=review_data['pr_data']['title'],
            description=review_data['pr_data']['description'],
            changes=review_data['pr_data']['changes'],
            reviews=reviews,
            context=context,
            examples=EXAMPLES
        )
