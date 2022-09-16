import base64
import os
import re
import sys

import requests
from github import Github, GithubException

repos = [
    f"alphagov/{repo['app_name']}"
    for repo in requests.get("https://docs.publishing.service.gov.uk/repos.json").json()
]


class VersionUpgrader:

    def __init__(self, old_version, new_version):
        self.old_version = old_version

        self.new_version_full = new_version
        self.new_version = new_version.split('p')[0]

        self.github = Github(os.environ['GITHUB_ACCESS_TOKEN'])
        self.branch_name = f'ruby-{self.new_version}'.replace('.', '-')

    def can_repo_be_upgraded(self, repo):
        try:
            repo.get_branch(self.branch_name)
        except GithubException:
            pass
        else:
            print('Already upgraded!', file=sys.stderr)
            return False  # already upgraded

        try:
            current_version_file = repo.get_contents('.ruby-version')
        except GithubException:
            print('No .ruby-version file found', file=sys.stderr)
            return False

        current_version = base64.b64decode(current_version_file.content) \
            .decode('UTF-8').strip()

        if not current_version.startswith(self.old_version):
            print(f'Not running {self.old_version}!', file=sys.stderr)
            return False

        return True

    def create_branch(self, repo):
        print('Creating branch')

        main_branch = repo.get_branch(repo.default_branch)

        try:
            ref = f'refs/heads/{self.branch_name}'
            repo.create_git_ref(ref=ref, sha=main_branch.commit.sha)
        except GithubException:
            pass

    def upgrade_ruby_version(self, repo):
        print('Updating .ruby-version file')

        filename = '.ruby-version'
        message = f'Update .ruby-version to {self.new_version}'
        content = f'{self.new_version}\n'
        sha = repo.get_contents(filename).sha

        repo.update_file(filename, message, content, sha, self.branch_name)

    def upgrade_dockerfile(self, repo):
        print('Updating Dockerfile')

        filename = 'Dockerfile'

        try:
            existing_file = repo.get_contents(filename)
        except GithubException:
            print('No Dockerfile file found', file=sys.stderr)
            return  # doesn't have a Dockerfile

        sha = existing_file.sha
        existing_content = base64.b64decode(existing_file.content) \
            .decode('UTF-8').strip()

        old = f'ruby:{self.old_version}'
        new = f'ruby:{self.new_version}'

        if re.search(old, existing_content):
            content = re.sub(old, new, existing_content, count=1)
        else:
            return # RUBY VERSION not in the Dockerfile

        message = f'Update Dockerfile to {self.new_version}'

        repo.update_file(filename, message, content, sha, self.branch_name)

    def upgrade_gemfile_lock(self, repo):
        print('Updating Gemfile.lock')

        filename = 'Gemfile.lock'

        try:
            existing_file = repo.get_contents(filename)
        except GithubException:
            print('No Gemfile file found', file=sys.stderr)
            return  # doesn't have a Gemfile

        sha = existing_file.sha
        existing_content = base64.b64decode(existing_file.content) \
            .decode('UTF-8').strip()

        content = existing_content.split('\n')
        version_line = None

        for i, line in enumerate(content):
            if line.strip() == 'RUBY VERSION':
                version_line = i + 1
                break
        else:
            return  # RUBY VERSION not in the Gemfile.lock

        content[version_line] = f'   ruby {self.new_version_full}'
        content = '\n'.join(content) + '\n'

        message = f'Update Gemfile.lock to {self.new_version}'

        repo.update_file(filename, message, content, sha, self.branch_name)

    def raise_upgrade_pr(self, repo):
        print('Raising PR')

        title = f'Upgrade Ruby to {self.new_version}'
        body = f'''
            Upgrades Ruby to {self.new_version}. See commits for more details.
            This PR should be tested before merge, as per https://docs.publishing.service.gov.uk/manual/ruby.html#update-ruby-version-in-the-relevant-repos.
        '''.strip()
        repo.create_pull(title, body, base=repo.default_branch, head=self.branch_name)

    def upgrade(self, repo_name):
        print('Upgrading', repo_name, 'to', self.new_version)

        try:
            repo = self.github.get_repo(repo_name)
        except GithubException as e:
            print(e, file=sys.stderr)
            return

        if not self.can_repo_be_upgraded(repo):
            return

        self.create_branch(repo)
        self.upgrade_ruby_version(repo)
        self.upgrade_dockerfile(repo)
        self.upgrade_gemfile_lock(repo)
        self.raise_upgrade_pr(repo)


def upgrade(old_version, new_version):
    upgrader = VersionUpgrader(old_version, new_version)
    for repo in repos:
        upgrader.upgrade(repo)


if __name__ == '__main__':
    upgrade('2.7.5', '2.7.6')
    upgrade('3.0.3', '3.0.4')
