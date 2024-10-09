import ollama
import requests
import json
import sys
from prompts import CODE_REVIEW_PROMPT, FEEDBACK_IMPROVEMENT_PROMPT, EXAMPLES

class Agent:
    def __init__(self, model_name="llama3.1", role="code_reviewer", use_post_request=False):
        self.model_name = model_name
        self.role = role
        self.use_post_request = use_post_request

    def analyze(self, data, model_name=None):
        prompt = self._prepare_prompt(data)
        model = model_name or self.model_name

        if self.use_post_request:
            response = self._post_request_generate(model, prompt)
        else:
            response = ollama.generate(model=model, prompt=prompt)['response']

        return prompt, response

    def _post_request_generate(self, model, prompt):
        url = "http://localhost:11434/api/generate"
        headers = {"Content-Type": "application/json"}
        data = {"model": model, "prompt": prompt, "stream": True}

        response_content = ""
        with requests.post(url, headers=headers, json=data, stream=True) as r:
            for line in r.iter_lines():
                if line:
                    json_response = json.loads(line)
                    if not json_response.get("done", False):
                        content = json_response.get("response", "")
                        print(content, end='', flush=True)
                        response_content += content
                    else:
                        # This is the final response with metrics
                        print("\n\n---------------------")
                        eval_count = json_response.get("eval_count", 0)
                        prompt_eval_count = json_response.get('prompt_eval_count', 0)
                        eval_duration = json_response.get("eval_duration", 1)  # in nanoseconds
                        tokens_per_second = (eval_count / eval_duration) * 1e9
                        print(f"Tokens generated: {eval_count}")
                        print(f"Generation time: {eval_duration / 1e9:.2f} seconds")
                        print(f"Speed: {tokens_per_second:.2f} tokens/second")
                        print(f"Prompt tokens: {prompt_eval_count}")
                        print(f"Total tokens: {prompt_eval_count + eval_count}")
                        print(f"Total duration: {json_response.get('total_duration', 0) / 1e9:.2f} seconds")
                        print("---------------------")

        print()
        return response_content

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
