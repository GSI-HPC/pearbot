class PRSession:
    def __init__(self, pr_number, repo_full_name):
        self.pr_number = pr_number
        self.repo_full_name = repo_full_name
        self.conversation_history = []

    def add_message(self, role, content):
        self.conversation_history.append({"role": role, "content": content})

    def get_conversation_history(self):
        return self.conversation_history

pr_sessions = {}

def get_or_create_session(pr_number, repo_full_name):
    if pr_number not in pr_sessions:
        pr_sessions[pr_number] = PRSession(pr_number, repo_full_name)
    return pr_sessions[pr_number]
