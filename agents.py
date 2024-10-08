import ollama

class Agent:
    def __init__(self, model_name="llama3.1", role="code_reviewer"):
        self.model_name = model_name
        self.role = role
        self.examples = """
    Example #1:
    Change:
    ```diff
+ fi

+if [[ $2 =~ ^[0-9]+$ ]]; then
+    msgSize=$1
    ```
    Suggestion:
    The assignment of msgSize is incorrect; it should be assigned the value of $2 instead of $1:
    ```diff
-    msgSize=$1
+    msgSize=$2
    ```

    Example #2:
    Change:
    ```diff
+ xterm -geometry 90x40+550+40 -hold -e @EX_BIN_DIR@/$PROCESSOR1 &
+
+ PROCESSOR2="fairmq-ex-region-processor"
+ PROCESSOR2+=" --id processor1"
    ```
    Suggestion:
    There seems to be a copy-paste error. The `PROCESSOR2` should have a unique identifier, but it is currently set to `processor1`, which is the same as `PROCESSOR1`. This should be corrected to ensure that each processor has a unique ID.
    ```diff
-    msgSize=$1
+    msgSize=$2
    ```
        """


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
    Reference the relevant diff lines and keep your suggestions short and consice as in these examples:

    {self.examples}

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

        Original Pull Request:
        Title: {review_data['pr_data']['title']}
        Description:
{review_data['pr_data']['description']}

        With the following file changes:

{review_data['pr_data']['changes']}

        Preliminary Reviews:
{reviews}

        Based on these reviews, but also adding your expertise on top, provide a review that contains feedback for the important aspects of the code changes.
        Include only points that could potentialy fix error or lead to improvements.
        DO NOT comment on the quality of the preliminary reviews themselves and DO NOT quote the preliminary reviews, but address the points directly.

        Reference the relevant diff lines and keep your suggestions short and consice as in these examples:

        {self.examples}

        Your feedback to the Pull Request code changes:
        """
        return prompt
