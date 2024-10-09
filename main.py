import argparse
import json
import re
import subprocess
import sys
import traceback

from flask import Flask, request, abort
from dotenv import load_dotenv
from github import Github, GithubException

load_dotenv()

NUM_INITIAL_REVIEWS = 3
REVIEW_MODELS = ["llama3.1", "codellama", "codestral"]

try:
    from auth import verify_webhook_signature, get_installation_access_token
    from storage import get_or_create_session
    from agents import Agent
except EnvironmentError as e:
    print(f"Error: {e}")
    print("Please ensure all required environment variables are set in your .env file.")
    sys.exit(1)

app = Flask(__name__)
code_review_agent = Agent(role="code_reviewer", use_post_request=True)
feedback_improver_agent = Agent(role="feedback_improver", use_post_request=True)

@app.route('/webhook', methods=['POST'])
def webhook():
    print("Webhook received")

    if not verify_webhook_signature(request):
        print("Webhook signature verification failed")
        abort(401)

    event = request.headers.get("X-GitHub-Event")
    payload = request.json

    print(f"Received event: {event}")

    if event == "issue_comment":
        handle_issue_comment(payload)
    else:
        print(f"Event {event} is not supported")

    return 'Webhook received', 200

def handle_issue_comment(payload):
    action = payload["action"]
    comment = payload["comment"]
    issue = payload["issue"]
    repo = payload["repository"]

    print(f"\n\nReceived comment:\n   action: {action},\n   comment body: {comment["body"]}")

    if "pull_request" in issue and action == "created" and "@pearbot review" in comment["body"].lower():
        print(f"\nReview requested with `@pearbot review` for Pull Request #{issue['number']}")
        perform_review(issue["number"], repo["full_name"], payload["installation"]["id"])
    else:
        print(f"Review condition not found")

def perform_review(pr_number, repo_full_name, installation_id):
    access_token = get_installation_access_token(installation_id)
    g = Github(access_token)
    repo_obj = g.get_repo(repo_full_name)
    pull_request = repo_obj.get_pull(pr_number)

    changes = file_changes_as_string(pull_request.get_files())
    pr_data = {
        "title": pull_request.title,
        "description": pull_request.body,
        "changes": changes,
        "context": ""
    }

    initial_reviews = []

    for i in range(NUM_INITIAL_REVIEWS):
        print(f"\n\n >>> Requesting initial review {i+1} (with {REVIEW_MODELS[i]})...")
        _, initial_review = code_review_agent.analyze(pr_data, REVIEW_MODELS[i])
        initial_reviews.append(initial_review)

    improvement_data = {
        "pr_data": pr_data,
        "initial_reviews": initial_reviews
    }
    print(f"\n\n >>> Requesting improved review (with llama3.1)...\n\n")
    improver_prompt, improved_feedback = feedback_improver_agent.analyze(improvement_data, "llama3.1")

    try:
        print(f"\n\nPosting improved feedback:\n{improved_feedback}\n\n")
        # pull_request.create_issue_comment(f"Code Review Feedback:\n\n{improved_feedback}")
    except GithubException as e:
        print(f"GitHub API error: {e.status} - {e.data}")
    except Exception as e:
        print(f"Error posting review: {e}")
        print(f"Full exception: {traceback.format_exc()}")

    session = get_or_create_session(pr_number, repo_full_name)
    session.add_message("assistant", json.dumps({
        "initial_reviews": initial_reviews,
        "improved_feedback": improved_feedback
    }))

def file_changes_as_string(files):
    file_changes = []
    for file in files:
        file_changes.append(f"""
    Filename: {file.filename}
    Status: {file.status}
    Additions: {file.additions}
    Deletions: {file.deletions}
    Changes: {file.changes}
    Patch:
{file.patch}
""")
    return "\n---\n".join(file_changes)

def extract_commit_info(diff_content):
    commit_range = None
    commit_messages = []

    # Updated regex to match both full and shortened commit hashes
    commit_hashes = re.findall(r'index ([0-9a-f]{7,40})\.\.([0-9a-f]{7,40})', diff_content)
    if commit_hashes:
        first_commit, last_commit = commit_hashes[0][0], commit_hashes[-1][1]
        commit_range = f"{first_commit}..{last_commit}"
        print(f"Extracted commit range: {commit_range}")
    else:
        print("No commit range found in the diff content.")

    # Try to find commit messages in git format-patch style diffs
    message_blocks = re.findall(r'From [0-9a-f]+ .*\nFrom: .*\nDate: .*\nSubject: \[PATCH\] (.*)', diff_content)
    commit_messages.extend(message_blocks)

    if commit_messages:
        print(f"Extracted {len(commit_messages)} commit message(s) from the diff content.")
    else:
        print("No commit messages found in the diff content.")

    return commit_range, commit_messages

def get_commit_comments(commit_range):
    try:
        result = subprocess.run(['git', 'log', '--pretty=format:%s', commit_range],
                                capture_output=True, text=True, check=True)
        comments = result.stdout.strip().split('\n')
        print(f"Retrieved {len(comments)} commit comment(s) from git log.")
        return comments
    except subprocess.CalledProcessError:
        print("Warning: Unable to retrieve commit comments using git log. This may not be a git repository or the specified range is invalid.")
        return []

def analyze_diff(diff_content, provided_commit_range=None):
    extracted_range, extracted_messages = extract_commit_info(diff_content)

    if provided_commit_range:
        commit_comments = get_commit_comments(provided_commit_range)
    elif extracted_range:
        commit_comments = get_commit_comments(extracted_range)
    else:
        commit_comments = extracted_messages

    if not commit_comments:
        if extracted_range:
            comments_str = f"Commit range {extracted_range} found, but unable to retrieve commit messages."
        else:
            comments_str = "No commit information available."
    else:
        comments_str = "\n".join(commit_comments)

    pr_data = {
        "title": "Local Diff Analysis",
        "description": f"Analyzing a local diff with the following commit information:\n\n{comments_str}",
        "changes": diff_content,
        "context": ""
    }

    # print(json.dumps(pr_data, indent=4))

    initial_reviews = []
    for i in range(NUM_INITIAL_REVIEWS):
        print(f"\n\n >>> Requesting initial review {i+1} (with {REVIEW_MODELS[i]})...")
        _, initial_review = code_review_agent.analyze(pr_data, REVIEW_MODELS[i])
        initial_reviews.append(initial_review)

    improvement_data = {
        "pr_data": pr_data,
        "initial_reviews": initial_reviews
    }

    print(f"\n\n >>> Requesting improved review (with llama3.1)...\n\n")
    _, improved_feedback = feedback_improver_agent.analyze(improvement_data, "llama3.1")

    print(f"\n\nImproved feedback:\n{improved_feedback}\n\n")

def main():
    parser = argparse.ArgumentParser(description="Code Review Script")
    parser.add_argument("--server", action="store_true", help="Run as a server")
    parser.add_argument("--diff", type=str, nargs='?', const='-', help="Path to the diff file or '-' for stdin")
    parser.add_argument("--additional-arg", type=str, help="An example of an additional argument")

    args = parser.parse_args()

    if args.server:
        print("Running as a server...")
        app.run(host="localhost", port=3000)
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

        if args.additional_arg:
            print(f"Additional argument provided: {args.additional_arg}")

        analyze_diff(diff_content)
    else:
        parser.print_help()

if __name__ == "__main__":
    main()

