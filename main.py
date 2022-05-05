import base64
import os
import re

from github import Github, GithubException


repos = [
    'alphagov/account-api',
    'alphagov/asset-manager',
    'alphagov/authenticating-proxy',
    'alphagov/bouncer',
    'alphagov/bulk-merger',
    'alphagov/cache-clearing-service',
    'alphagov/ckan-functional-tests',
    'alphagov/ckanext-datagovuk',
    'alphagov/collections',
    'alphagov/collections-publisher',
    'alphagov/contacts-admin',
    'alphagov/content-data-admin',
    'alphagov/content-data-api',
    'alphagov/content-publisher',
    'alphagov/content-store',
    'alphagov/content-tagger',
    'alphagov/datagovuk-tech-docs',
    'alphagov/datagovuk_find',
    'alphagov/datagovuk_publish',
    'alphagov/datagovuk_publish_queue_monitor',
    'alphagov/datagovuk_reference',
    'alphagov/eligibility-viewer',
    'alphagov/email-alert-api',
    'alphagov/email-alert-frontend',
    'alphagov/email-alert-monitoring',
    'alphagov/email-alert-service',
    'alphagov/feedback',
    'alphagov/finder-frontend',
    'alphagov/frontend',
    'alphagov/gds-api-adapters',
    'alphagov/gds-sso',
    'alphagov/government-frontend',
    'alphagov/govspeak',
    'alphagov/govspeak-preview',
    'alphagov/govuk-accessibility-reports',
    'alphagov/govuk-app-deployment',
    'alphagov/govuk-aws',
    'alphagov/govuk-aws-data',
    'alphagov/govuk-browser-extension',
    'alphagov/govuk-cdn-config',
    'alphagov/govuk-content-schemas',
    'alphagov/govuk-dependencies',
    'alphagov/govuk-deploy-lag-badger',
    'alphagov/govuk-developer-docs',
    'alphagov/govuk-display-screen',
    'alphagov/govuk-dns',
    'alphagov/govuk-docker',
    'alphagov/govuk-jenkinslib',
    'alphagov/govuk-knowledge-graph',
    'alphagov/govuk-load-testing',
    'alphagov/govuk-pact-broker',
    'alphagov/govuk-puppet',
    'alphagov/govuk-related-links-recommender',
    'alphagov/govuk-saas-config',
    'alphagov/govuk-secondline-blinken',
    'alphagov/govuk-secrets',
    'alphagov/govuk-user-intent-survey-explorer',
    'alphagov/govuk-user-journey-models',
    'alphagov/govuk-user-reviewer',
    'alphagov/govuk-zendesk-display-screen',
    'alphagov/govuk_ab_testing',
    'alphagov/govuk_app_config',
    'alphagov/govuk_document_types',
    'alphagov/govuk_message_queue_consumer',
    'alphagov/govuk_publishing_components',
    'alphagov/govuk_schemas',
    'alphagov/govuk_sidekiq',
    'alphagov/govuk_taxonomy_helpers',
    'alphagov/govuk_test',
    'alphagov/hmrc-manuals-api',
    'alphagov/imminence',
    'alphagov/info-frontend',
    'alphagov/licence-finder',
    'alphagov/licensify',
    'alphagov/licensify-admin',
    'alphagov/licensify-feed',
    'alphagov/link-checker-api',
    'alphagov/local-links-manager',
    'alphagov/locations-api',
    'alphagov/manuals-frontend',
    'alphagov/manuals-publisher',
    'alphagov/mapit',
    'alphagov/maslow',
    'alphagov/omniauth-gds',
    'alphagov/optic14n',
    'alphagov/plek',
    'alphagov/publisher',
    'alphagov/publishing-api',
    'alphagov/publishing-e2e-tests',
    'alphagov/rack-logstasher',
    'alphagov/rails_translation_manager',
    'alphagov/release',
    'alphagov/router',
    'alphagov/router-api',
    'alphagov/rubocop-govuk',
    'alphagov/seal',
    'alphagov/search-admin',
    'alphagov/search-analytics',
    'alphagov/search-api',
    'alphagov/service-manual-frontend',
    'alphagov/service-manual-publisher',
    'alphagov/short-url-manager',
    'alphagov/side-by-side-browser',
    'alphagov/sidekiq-monitoring',
    'alphagov/signon',
    'alphagov/slimmer',
    'alphagov/smart-answers',
    'alphagov/smokey',
    'alphagov/special-route-publisher',
    'alphagov/specialist-publisher',
    'alphagov/static',
    'alphagov/support',
    'alphagov/support-api',
    'alphagov/transition',
    'alphagov/transition-config',
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

        try:
            current_version_file = repo.get_contents('.ruby-version')
        except GithubException:
            print('No .ruby-version file found')
            return False

        current_version = base64.b64decode(current_version_file.content) \
            .decode('UTF-8').strip()

        if not current_version.startswith(self.old_version):
            print(f'Not running {self.old_version}!')
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
            print('No Dockerfile file found')
            return  # doesn't have a Dockerfile

        sha = existing_file.sha
        existing_content = base64.b64decode(existing_file.content) \
            .decode('UTF-8').strip()

        content = existing_content.split('\n')
        old = f'ruby:{self.old_version}'
        new = f'ruby:{self.new_version}'

        for line in content:
            if re.search(old,line):
                line = re.sub(old, new, line)
                break
        else:
            return  # RUBY VERSION not in the Dockerfile

        content = '\n'.join(content) + '\n'

        message = f'Update Dockerfile to {self.new_version}'

        repo.update_file(filename, message, content, sha, self.branch_name)

    def upgrade_gemfile_lock(self, repo):
        print('Updating Gemfile.lock')

        filename = 'Gemfile.lock'

        try:
            existing_file = repo.get_contents(filename)
        except GithubException:
            print('No Gemfile file found')
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
            print(e)
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
    upgrade('2.6.0', '2.7.6')
    upgrade('2.6.1', '2.7.6')
    upgrade('2.6.5', '2.7.6')
    upgrade('2.6.6', '2.7.6')
    upgrade('2.7.2', '2.7.6')
    upgrade('2.7.3', '2.7.6')
    upgrade('2.7.5', '2.7.6')
    upgrade('3.0.3', '3.0.4')
