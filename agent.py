import ollama

class Agent:
    def __init__(self, model_name="codellama"):
        self.model_name = model_name

    def analyze_pr(self, pr_data):
        # Prepare the prompt
        prompt = self._prepare_prompt(pr_data)

        # Call the LLM
        response = ollama.generate(model=self.model_name, prompt=prompt)

        return response['response']

    def _prepare_prompt(self, pr_data):
        prompt = f"""
        Analyze the following Pull Request and provide feedback:

        Title: {pr_data['title']}
        Description: {pr_data['description']}

        Changes:
        {pr_data['changes']}

        Please provide:
        1. A summary of the changes
        2. Any potential issues or improvements
        3. Suggestions for the developer

        Your response:
        """
        return prompt

class CodeReviewAgent(Agent):
    def __init__(self):
        super().__init__(model_name="llama3.1")

# You can add more specialized agents here in the future
