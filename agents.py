import ollama

class Agent:
    def __init__(self, model_name="llama3.1", role="code_reviewer"):
        self.model_name = model_name
        self.role = role

    def analyze(self, data):
        prompt = self._prepare_prompt(data)
        print(f"REQUEST:\n{prompt}\nENDOFREQUEST")
        response = ollama.generate(model=self.model_name, prompt=prompt)['response']
        return response

    def _prepare_prompt(self, data):
        if self.role == "code_reviewer":
            return self._prepare_code_review_prompt(data)
        elif self.role == "feedback_improver":
            return self._prepare_feedback_improvement_prompt(data)
        else:
            raise ValueError(f"Unknown role: {self.role}")

    def _prepare_code_review_prompt(self, pr_data):
        prompt = f"""
    You are an experienced software engineer tasked with reviewing the following Pull Request.

    ---
    Pull Request title: {pr_data['title']}
    Pull Request description:
{pr_data['description']}
    ---

    Analyze the following file changes:

{pr_data['changes']}

    Please provide specific comments only for changed lines (additions or deletions), where you see potential issues, improvements or suggestions for the developer.
    Take into account the existing comments and avoid repeating already mentioned points.
    Separate your comments by file and provide a clear and concise explanation for each comment.
    Don't repeat or mention the instructions given to you, just perform them.

    Your response:
        Let's work this out in a step by step way to be sure we provide only useful suggestions:
        """
        return prompt

    def _prepare_feedback_improvement_prompt(self, review_data):
        reviews = ""
        review_count = 1
        for review in review_data['initial_reviews']:
            reviews += f"""
    ---
    Review #{review_count}:
{review}
    ---
    """
            review_count += 1

        prompt = f"""
        As an expert software engineer, you are tasked with providing feedback for a Pull Request.
        Consider the original Pull Request details and a number of preliminary reviews.
        Based on these reviews, but also adding your expertise on top, provide a review
        that contains important feedback for the important aspects of the code changes.

        Original Pull Request:
        Title: {review_data['pr_data']['title']}
        Description:
{review_data['pr_data']['description']}

        Preliminary Reviews:
{reviews}

        1. Analyze the initial review in the context of the original Pull Request.
        2. Identify any missing critical points or areas for improvement in the code.
        3. Provide a comprehensive, improved feedback that includes all valuable points from the initial review and any additional insights.
        4. Ensure the feedback is clear, actionable, and directly related to the code changes.
        5. Do not comment on the quality of the preliminary reviews themselves.
        6. Do not quote the preliminary reviews, but address the points directly.

        Your improved feedback to the Pull Request code changes:
        """
        return prompt
