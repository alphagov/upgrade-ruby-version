import base64
import os

from github import Github, GithubException


repos = [
    'alphagov/asset-manager',
    'alphagov/authenticating-proxy',
    'alphagov/bouncer',
    'alphagov/calculators',
    'alphagov/calendars',
    'alphagov/collections',
    'alphagov/collections-publisher',
    'alphagov/contacts-admin',
    'alphagov/content-audit-tool',
    'alphagov/content-performance-manager',
    'alphagov/content-store',
    'alphagov/content-tagger',
    'alphagov/email-alert-api',
    'alphagov/email-alert-frontend',
    'alphagov/email-alert-service',
    'alphagov/feedback',
    'alphagov/finder-frontend',
    'alphagov/frontend',
    'alphagov/government-frontend',
    'alphagov/hmrc-manuals-api',
    'alphagov/imminence',
    'alphagov/info-frontend',
    'alphagov/kibana-gds',
    'alphagov/licence-finder',
    'alphagov/link-checker-api',
    'alphagov/local-links-manager',
    'alphagov/manuals-frontend',
    'alphagov/manuals-publisher',
    'alphagov/maslow',
    'alphagov/policy-publisher',
    'alphagov/pre-transition-stats',
    'alphagov/publisher',
    'alphagov/publishing-api',
    'alphagov/release',
    'alphagov/router-api',
    'alphagov/rummager',
    'alphagov/search-admin',
    'alphagov/service-manual-frontend',
    'alphagov/service-manual-publisher',
    'alphagov/short-url-manager',
    'alphagov/sidekiq-monitoring',
    'alphagov/signon',
    'alphagov/smart-answers',
    'alphagov/smokey',
    'alphagov/specialist-publisher',
    'alphagov/static',
    'alphagov/support',
    'alphagov/support-api',
    'alphagov/transition',
    'alphagov/travel-advice-publisher',
    'alphagov/whitehall',
    'alphagov/govuk-cdn-logs-monitor',
]


class VersionUpgrader:

    def __init__(self, old_version, new_version):
        self.old_version = old_version
        self.new_version = new_version
        self.github = Github(os.environ['GITHUB_ACCESS_TOKEN'])
        self.branch_name = 'ruby-{v}'.format(v=self.new_version.replace('.', '-'))

    def can_repo_be_upgraded(self, repo):
        try:
            branch = repo.get_branch(self.branch_name)
        except GithubException:
            pass
        else:
            print('Already upgraded!')
            return False # already upgraded

        current_version_file = repo.get_contents('.ruby-version')
        current_version = base64.b64decode(current_version_file.content).decode('UTF-8').strip()
        if not current_version.startswith(self.old_version):
            print(f'Not running {self.old_version}!')
            return False

        return True

    def create_branch(self, repo):
        print('Creating branch')

        master = repo.get_branch('master')

        try:
            repo.create_git_ref(ref=f'refs/heads/{self.branch_name}', sha=master.commit.sha)
        except GithubException:
            pass

    def upgrade_ruby_version(self, repo):
        print('Updating .ruby-version file')

        filename = '/.ruby-version'
        message = f'Update .ruby-version to {self.new_version}'
        content = f'{self.new_version}\n'
        sha = repo.get_contents(filename).sha

        repo.update_file(filename, message, content, sha, self.branch_name)

    def upgrade_dockerfile(self, repo):
        print('Updating Dockerfile')

        filename = '/Dockerfile'

        try:
            existing_file = repo.get_contents(filename)
        except GithubException:
            return  # doesn't have a Dockerfile

        sha = existing_file.sha
        existing_content = base64.b64decode(existing_file.content).decode('UTF-8').strip()

        content = existing_content.split('\n')
        content[0] = f'FROM ruby:{self.new_version}'
        content = '\n'.join(content) + '\n'

        message = f'Update Dockerfile to {self.new_version}'

        repo.update_file(filename, message, content, sha, self.branch_name)

    def raise_upgrade_pr(self, repo):
        print('Raising PR')

        title = f'Upgrade Ruby to {self.new_version}'
        body = 'https://trello.com/c/Sck93ByH/37-ruby-security-vulnerability-244'
        repo.create_pull(title, body, base='master', head=self.branch_name)

    def upgrade(self, repo_name):
        print('Upgrading', repo_name, 'to', self.new_version)

        repo = self.github.get_repo(repo_name)

        if not self.can_repo_be_upgraded(repo):
            return

        self.create_branch(repo)
        self.upgrade_ruby_version(repo)
        self.upgrade_dockerfile(repo)
        self.raise_upgrade_pr(repo)


if __name__ == '__main__':
    upgrader = VersionUpgrader('2.4', '2.4.4')
    for repo in repos:
        upgrader.upgrade(repo)
