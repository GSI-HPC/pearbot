import json
import re
import sys

from colorama import Fore, Style

from ollama_utils import validate_models

def extract_commit_info(diff_content):
    commit_range = None
    commit_messages = []

    commit_hashes = re.findall(r'index ([0-9a-f]{7,40})\.\.([0-9a-f]{7,40})', diff_content)
    if commit_hashes:
        first_commit, last_commit = commit_hashes[0][0], commit_hashes[-1][1]
        commit_range = f"{first_commit}..{last_commit}"
        print(f"Extracted commit range: {commit_range}")
    else:
        print("No commit range found in the diff content.")

    message_blocks = re.findall(r'From [0-9a-f]+ .*\nFrom: .*\nDate: .*\nSubject: \[PATCH\] (.*)', diff_content)
    commit_messages.extend(message_blocks)

    if commit_messages:
        print(f"Extracted {len(commit_messages)} commit message(s) from the diff content.")
    else:
        print("No commit messages found in the diff content.")

    return commit_messages

def analyze_diff(diff_content, code_review_agent, feedback_improver_agent, initial_review_models, final_review_model):
    if not validate_models(initial_review_models + [final_review_model]):
        sys.exit(1)

    extracted_messages = extract_commit_info(diff_content)

    if not extracted_messages:
        comments_str = "No commit information found."
    else:
        comments_str = "\n    ".join(extracted_messages)

    pr_data = {
        "title": "Local Diff Analysis",
        "description": f"    commits:\n\n{comments_str}",
        "changes": diff_content,
        "context": ""
    }

    print(json.dumps(pr_data, indent=4))

    initial_reviews = []
    for model in initial_review_models:
        print(Fore.GREEN + f"\n\n >>> Requesting initial review with {model}...")
        print(Style.RESET_ALL)
        _, initial_review = code_review_agent.analyze(pr_data, model)
        initial_reviews.append(initial_review)

    improvement_data = {
        "pr_data": pr_data,
        "initial_reviews": initial_reviews
    }

    print(Fore.GREEN + f"\n\n >>> Requesting improved review (with {final_review_model})...\n\n")
    print(Style.RESET_ALL)
    _, improved_feedback = feedback_improver_agent.analyze(improvement_data, final_review_model)

    print(f"\n\nImproved feedback:\n{improved_feedback}\n\n")
