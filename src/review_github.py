import os
import jwt
import time
import requests
import hmac
import hashlib
import sys
import traceback

from github import Github, GithubException
from flask import Flask, request, abort

class GitHubReviewer:
    def __init__(self, code_review_agent, feedback_improver_agent):
        try:
            self.GITHUB_APP_ID = os.getenv("GITHUB_APP_ID")
            self.GITHUB_PRIVATE_KEY = os.getenv("GITHUB_PRIVATE_KEY")
            self.GITHUB_APP_WEBHOOK_SECRET = os.getenv("GITHUB_APP_WEBHOOK_SECRET")

            if not all([self.GITHUB_APP_ID, self.GITHUB_PRIVATE_KEY, self.GITHUB_APP_WEBHOOK_SECRET]):
                raise EnvironmentError("Missing required environment variables. Please check your .env file.")
        except EnvironmentError as e:
            print(f"Error: {e}")
            print("Please ensure all required environment variables are set in your .env file.")
            sys.exit(1)

        self.GITHUB_PRIVATE_KEY = self.GITHUB_PRIVATE_KEY.replace('\\n', '\n') if self.GITHUB_PRIVATE_KEY else None

        self.code_review_agent = code_review_agent
        self.feedback_improver_agent = feedback_improver_agent

        self.app = Flask(__name__)
        self.setup_routes()

    def setup_routes(self):
        @self.app.route('/webhook', methods=['POST'])
        def webhook():
            print("Webhook received")

            if not self.verify_webhook_signature(request):
                print("Webhook signature verification failed")
                abort(401)

            event = request.headers.get("X-GitHub-Event")
            payload = request.json

            print(f"Received event: {event}")

            if event == "issue_comment":
                self.handle_issue_comment(payload)
            else:
                print(f"Event {event} is not supported")

            return 'Webhook received', 200

    def run_server(self, host="localhost", port=3000):
        self.app.run(host=host, port=port)

    def verify_webhook_signature(self, request):
        signature = request.headers.get('X-Hub-Signature-256')
        if signature is None:
            return False

        sha_name, signature = signature.split('=')
        if sha_name != 'sha256':
            return False

        secret = self.GITHUB_APP_WEBHOOK_SECRET.encode()
        mac = hmac.new(secret, msg=request.data, digestmod=hashlib.sha256)

        return hmac.compare_digest(mac.hexdigest(), signature)

    def create_jwt(self):
        now = int(time.time())
        payload = {
            "iat": now,
            "exp": now + (10 * 60),  # JWT expires in 10 minutes
            "iss": self.GITHUB_APP_ID
        }
        return jwt.encode(payload, self.GITHUB_PRIVATE_KEY, algorithm="RS256")

    def get_installation_access_token(self, installation_id):
        jwt_token = self.create_jwt()
        headers = {
            "Authorization": f"Bearer {jwt_token}",
            "Accept": "application/vnd.github.v3+json"
        }
        response = requests.post(
            f"https://api.github.com/app/installations/{installation_id}/access_tokens",
            headers=headers
        )
        return response.json()["token"]

    def handle_issue_comment(self, payload):
        action = payload["action"]
        comment = payload["comment"]
        issue = payload["issue"]
        repo = payload["repository"]

        print(f"\n\nReceived comment:\n   action: {action},\n   comment body: {comment['body']}")

        if "pull_request" in issue and action == "created" and "@pearbot review" in comment["body"].lower():
            print(f"\nReview requested with `@pearbot review` for Pull Request #{issue['number']}")
            self.perform_review(issue["number"], repo["full_name"], payload["installation"]["id"])
        else:
            print(f"Review condition not found")

    def perform_review(self, pr_number, repo_full_name, installation_id):
        access_token = self.get_installation_access_token(installation_id)
        g = Github(access_token)
        repo_obj = g.get_repo(repo_full_name)
        pull_request = repo_obj.get_pull(pr_number)

        changes = self.file_changes_as_string(pull_request.get_files())
        pr_data = {
            "title": pull_request.title,
            "description": pull_request.body,
            "changes": changes,
            "context": ""
        }

        initial_reviews = []
        for model in self.app.config['INITIAL_REVIEW_MODELS']:
            print(f"\n\n >>> Requesting initial review with {model}...")
            _, initial_review = self.code_review_agent.analyze(pr_data, model)
            initial_reviews.append(initial_review)

        improvement_data = {
            "pr_data": pr_data,
            "initial_reviews": initial_reviews
        }
        print(f"\n\n >>> Requesting improved review (with {self.app.config['FINAL_REVIEW_MODEL']})...\n\n")
        _, improved_feedback = self.feedback_improver_agent.analyze(improvement_data, self.app.config['FINAL_REVIEW_MODEL'])

        try:
            print(f"\n\nPosting improved feedback:\n{improved_feedback}\n\n")
            pull_request.create_issue_comment(f"Code Review Feedback:\n\n{improved_feedback}")
        except GithubException as e:
            print(f"GitHub API error: {e.status} - {e.data}")
        except Exception as e:
            print(f"Error posting review: {e}")
            print(f"Full exception: {traceback.format_exc()}")

    @staticmethod
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