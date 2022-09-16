# Upgrade Ruby Version

A script to upgrade the version of Ruby used by a project.

## Prerequisites

- [pipenv](https://pipenv.pypa.io/en/latest/) (`brew install pipenv`)
- [jq](https://stedolan.github.io/jq/) (`brew install jq`)

## Setup

Create a `.env` file with the following contents:

```
GITHUB_ACCESS_TOKEN=personal_access_token
```

You'll need to [create a personal access token](https://docs.github.com/en/authentication/keeping-your-account-and-data-secure/creating-a-personal-access-token) with a `repo` [scope](https://docs.github.com/en/developers/apps/building-oauth-apps/scopes-for-oauth-apps) so that you have write access to GOV.UK repositories.

> It's advised not to use your personal GitHub account to create the access token, as another developer will need to approve the PRs. You can use [govuk-ci GitHub account](https://github.com/govuk-ci).

Install dependencies:

```
pipenv install
```

## Configure the script

[Configure which Ruby versions should be upgraded](https://github.com/alphagov/upgrade-ruby-version/blob/67c9b1285c9601bd6020206e57480d1a14c66f28/main.py#L216).

When upgrading a specific list of repos (e.g. only those owned by your team), set up [the list of repos](https://github.com/alphagov/upgrade-ruby-version/blob/cf13233184bbda51550439b3d76b7af571a10121/main.py#L8-L11) with hardcoded values:
```
repos = [
    'alphagov/authenticating-proxy',
    'alphagov/bouncer',
]
```

## Run the script

This will open pull requests in every repository you've configured it to:

```bash
pipenv run python main.py
```

You can see the created PRs by visiting <https://github.com/pulls>.
