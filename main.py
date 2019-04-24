import base64
import os

from github import Github, GithubException


repos = [
    'alphagov/asset-manager',
    'alphagov/authenticating-proxy',
    'alphagov/bouncer',
    'alphagov/bulk-merger',
    'alphagov/cache-clearing-service',
    'alphagov/calculators',
    'alphagov/calendars',
    'alphagov/collections',
    'alphagov/collections-publisher',
    'alphagov/contacts-admin',
    'alphagov/content-data-admin',
    'alphagov/content-audit-tool',
    'alphagov/content-performance-manager',
    'alphagov/content-publisher',
    'alphagov/content-store',
    'alphagov/content-tagger',
    'alphagov/email-alert-api',
    'alphagov/email-alert-frontend',
    'alphagov/email-alert-service',
    'alphagov/feedback',
    'alphagov/finder-frontend',
    'alphagov/frontend',
    'alphagov/gds-api-adapters',
    'alphagov/government-frontend',
    'alphagov/govspeak-preview',
    'alphagov/govuk-alert-tracker',
    'alphagov/govuk-app-deployment',
    'alphagov/govuk-aws',
    'alphagov/govuk-content-schemas',
    'alphagov/govuk-developer-docs',
    'alphagov/govuk-dns',
    'alphagov/govuk-lint',
    'alphagov/govuk-puppet',
    'alphagov/govuk_publishing_components',
    'alphagov/govuk-saas-config',
    'alphagov/hmrc-manuals-api',
    'alphagov/imminence',
    'alphagov/info-frontend',
    'alphagov/licence-finder',
    'alphagov/link-checker-api',
    'alphagov/local-links-manager',
    'alphagov/manuals-frontend',
    'alphagov/manuals-publisher',
    'alphagov/maslow',
    'alphagov/publisher',
    'alphagov/publishing-api',
    'alphagov/publishing-e2e-tests',
    'alphagov/release',
    'alphagov/router-api',
    'alphagov/search-admin',
    'alphagov/search-api',
    'alphagov/service-manual-frontend',
    'alphagov/service-manual-publisher',
    'alphagov/short-url-manager',
    'alphagov/sidekiq-monitoring',
    'alphagov/signon',
    'alphagov/slimmer',
    'alphagov/smart-answers',
    'alphagov/smokey',
    'alphagov/specialist-publisher',
    'alphagov/static',
    'alphagov/support',
    'alphagov/support-api',
    'alphagov/transition',
    'alphagov/travel-advice-publisher',
    'alphagov/whitehall',
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
            print('Already upgraded!')
            return False  # already upgraded

        current_version_file = repo.get_contents('.ruby-version')
        current_version = base64.b64decode(current_version_file.content) \
            .decode('UTF-8').strip()

        if not current_version.startswith(self.old_version):
            print(f'Not running {self.old_version}!')
            return False

        return True

    def create_branch(self, repo):
        print('Creating branch')

        master = repo.get_branch('master')

        try:
            ref = f'refs/heads/{self.branch_name}'
            repo.create_git_ref(ref=ref, sha=master.commit.sha)
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
        existing_content = base64.b64decode(existing_file.content) \
            .decode('UTF-8').strip()

        content = existing_content.split('\n')
        content[0] = f'FROM ruby:{self.new_version}'
        content = '\n'.join(content) + '\n'

        message = f'Update Dockerfile to {self.new_version}'

        repo.update_file(filename, message, content, sha, self.branch_name)

    def upgrade_gemfile_lock(self, repo):
        print('Updating Gemfile.lock')

        filename = '/Gemfile.lock'

        try:
            existing_file = repo.get_contents(filename)
        except GithubException:
            return  # doesn't have a Dockerfile

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
            Upgrade Ruby to {self.new_version}, see commits for more details.
        '''.strip()
        repo.create_pull(title, body, base='master', head=self.branch_name)

    def upgrade(self, repo_name):
        print('Upgrading', repo_name, 'to', self.new_version)

        repo = self.github.get_repo(repo_name)

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
    upgrade('2.5', '2.6.3p62')
    upgrade('2.6', '2.6.3p62')
