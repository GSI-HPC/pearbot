import json
import sys
import traceback
from flask import Flask, request, abort
from dotenv import load_dotenv
from github import Github, GithubException

load_dotenv()

NUM_INITIAL_REVIEWS = 3

try:
    from auth import verify_webhook_signature, get_installation_access_token
    from storage import get_or_create_session
    from agents import Agent
except EnvironmentError as e:
    print(f"Error: {e}")
    print("Please ensure all required environment variables are set in your .env file.")
    sys.exit(1)

app = Flask(__name__)
code_review_agent = Agent(role="code_reviewer")
feedback_improver_agent = Agent(role="feedback_improver")

@app.route('/webhook', methods=['POST'])
def webhook():
    separator = "\n--------\n########\n--------"
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
        print(f"\nReview requested for Pull Request #{issue['number']}")
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
        "changes": changes
    }

    initial_reviews = []

    for i in range(NUM_INITIAL_REVIEWS):
        initial_review = code_review_agent.analyze(pr_data)
        initial_reviews.append(initial_review)
        print(f"\n\nInitial review {i+1}:\n{initial_review}\n\n")

    initial_review = code_review_agent.analyze(pr_data)

    improvement_data = {
        "pr_data": pr_data,
        "initial_reviews": initial_reviews
    }
    improved_feedback = feedback_improver_agent.analyze(improvement_data)

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
        "initial_review": initial_review,
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

if __name__ == "__main__":
    app.run(host="localhost", port=3000)
