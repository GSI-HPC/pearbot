import argparse
import sys

from dotenv import load_dotenv

load_dotenv()

from storage import get_or_create_session
from agents import Agent
from review_github import GitHubReviewer
from review_local import analyze_diff
from ollama_utils import get_available_models

def main():
    parser = argparse.ArgumentParser(description="Pearbot Code Review")
    parser.add_argument("--server", action="store_true", help="Run as a server")
    parser.add_argument("--diff", type=str, nargs='?', const='-', help="Path to the diff file or '-' for stdin")
    parser.add_argument("--model", type=str, default="llama3.1", help="Model for the final review step")
    parser.add_argument("--prompt-style", type=str, default="default", help="Prompt style (from prompts.yaml)")
    parser.add_argument("--initial-review-models", type=str, default="llama3.1,llama3.1,llama3.1", help="Comma-separated list of model names for the initial review (default: llama3.1,llama3.1,llama3.1)")

    args = parser.parse_args()

    initial_review_models = args.initial_review_models.split(',')
    final_review_model = args.model

    print(f"Available models: {', '.join(get_available_models()) or 'NONE'}")

    code_review_agent = Agent(role="code_reviewer", use_post_request=True, prompt_style=args.prompt_style)
    feedback_improver_agent = Agent(role="feedback_improver", use_post_request=True, prompt_style=args.prompt_style)

    if args.server:
        print("Running as a server...")
        github_reviewer = GitHubReviewer(code_review_agent, feedback_improver_agent, initial_review_models, final_review_model)
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

        analyze_diff(diff_content, code_review_agent, feedback_improver_agent, initial_review_models, final_review_model)
    else:
        parser.print_help()

if __name__ == "__main__":
    main()