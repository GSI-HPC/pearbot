CODE_REVIEW_PROMPT = """
    You are an experienced software engineer tasked with reviewing the following Pull Request.

    ---
    Pull Request title: {title}
    Pull Request description:
{description}
    ---

    Analyze the following file changes:

{changes}

    {context}

    Please provide specific comments only for changed lines (additions or deletions), where you see potential issues, improvements or suggestions for the developer.
    Take into account the existing comments and avoid repeating already mentioned points.
    Separate your comments by file and provide a clear and concise explanation for each comment.
    Don't repeat or mention the instructions given to you, just perform them.
    Reference the relevant diff lines and keep your suggestions short and concise as in these examples:

    {examples}

    Your response:
        Let's work this out in a step by step way to be sure we provide only useful suggestions:
"""

FEEDBACK_IMPROVEMENT_PROMPT = """
    As an expert software engineer, you are tasked with providing feedback for a Pull Request.
    Consider the original Pull Request details and a number of preliminary reviews.

    Original Pull Request:
    ---
    Title: {title}
    Description:
{description}
    ---

    With the following file changes:

{changes}

    {context}

    Preliminary Reviews:
{reviews}

    Based on these reviews, but also adding your expertise on top, provide a review that contains feedback for the important aspects of the code changes.
    Include only points that could potentially fix errors or lead to improvements.
    DO NOT comment on the quality of the preliminary reviews themselves and DO NOT quote the preliminary reviews, but address the points directly.

    Reference the relevant diff lines and keep your suggestions short and concise as in these examples:

    {examples}

    Your feedback to the Pull Request code changes:
"""

EXAMPLES = """
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
