import json
import sys
import traceback
from flask import Flask, request, abort
from dotenv import load_dotenv
from github import Github, GithubException

load_dotenv()

try:
    from auth import verify_webhook_signature, get_installation_access_token
    from storage import get_or_create_session
    from agents import CodeReviewAgent
except EnvironmentError as e:
    print(f"Error: {e}")
    print("Please ensure all required environment variables are set in your .env file.")
    sys.exit(1)

app = Flask(__name__)
code_review_agent = CodeReviewAgent()

@app.route('/webhook', methods=['POST'])
def webhook():
    separator = "\n--------\n########\n--------"
    print("Webhook received")
    # print(f"Headers: {request.headers}{separator}")
    # print(f"Raw data: {request.data}{separator}")

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

    diff_files = pull_request.get_files()

    pr_data = {
        "title": pull_request.title,
        "description": pull_request.body,
        "files": [
            {
                "filename": file.filename,
                "status": file.status,
                "additions": file.additions,
                "deletions": file.deletions,
                "changes": file.changes,
                "patch": file.patch
            }
            for file in diff_files
        ]
    }

    review_comments = code_review_agent.analyze_pr(pr_data)

    try:
        print(f"\n\nPosting review comments:\n{review_comments}\n\n")
        pull_request.create_issue_comment(review_comments)
    except GithubException as e:
        print(f"GitHub API error: {e.status} - {e.data}")
    except Exception as e:
        print(f"Error posting review: {e}")
        print(f"Full exception: {traceback.format_exc()}")

    session = get_or_create_session(pr_number, repo_full_name)
    session.add_message("assistant", json.dumps(review_comments))

if __name__ == "__main__":
    app.run(host="localhost", port=3000)