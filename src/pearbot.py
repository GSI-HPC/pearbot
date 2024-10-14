import argparse
import json
import re
import sys

from colorama import Fore, Style
from dotenv import load_dotenv

load_dotenv()

from storage import get_or_create_session
from agents import Agent
from review_github import GitHubReviewer
from ollama_utils import is_model_available, get_available_models

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

def analyze_diff(diff_content, initial_review_models, final_review_model):
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

    code_review_agent = Agent(role="code_reviewer", use_post_request=True)
    feedback_improver_agent = Agent(role="feedback_improver", use_post_request=True)

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

def validate_models(initial_review_models, final_review_model):
    all_models = initial_review_models + [final_review_model]
    unavailable_models = [model for model in all_models if not is_model_available(model)]

    if unavailable_models:
        print(f"Error: The following models are not available: {', '.join(unavailable_models)}")
        print("Available models:")
        print(", ".join(get_available_models()))
        return False
    return True

def main():
    parser = argparse.ArgumentParser(description="Pearbot Code Review")
    parser.add_argument("--server", action="store_true", help="Run as a server")
    parser.add_argument("--diff", type=str, nargs='?', const='-', help="Path to the diff file or '-' for stdin")
    parser.add_argument("--model", type=str, default="llama3.1", help="Model for the final review step")
    parser.add_argument("--initial-review-models", type=str, default="llama3.1,llama3.1,llama3.1", help="Comma-separated list of model names for the initial review (default: llama3.1,llama3.1,llama3.1)")

    args = parser.parse_args()

    initial_review_models = args.initial_review_models.split(',')
    final_review_model = args.model

    print(f"Available models: {', '.join(get_available_models())}")

    if not validate_models(initial_review_models, final_review_model):
        sys.exit(1)

    if args.server:
        print("Running as a server...")
        code_review_agent = Agent(role="code_reviewer", use_post_request=True)
        feedback_improver_agent = Agent(role="feedback_improver", use_post_request=True)
        github_reviewer = GitHubReviewer(code_review_agent, feedback_improver_agent)
        github_reviewer.app.config['INITIAL_REVIEW_MODELS'] = initial_review_models
        github_reviewer.app.config['FINAL_REVIEW_MODEL'] = final_review_model
        github_reviewer.run_server()
    elif args.diff or not sys.stdin.isatty():
        if args.diff == '-' or not sys.stdin.isatty():
            print("Reading diff from stdin...")
            diff_content = sys.stdin.read()
        elif args.diff:
            print(f"Reading diff from file: {args.diff}")
            with open(args.diff, 'r') as file:
                diff_content = file.read()
        else:
            parser.print_help()
            return

        analyze_diff(diff_content, initial_review_models, final_review_model)
    else:
        parser.print_help()

if __name__ == "__main__":
    main()