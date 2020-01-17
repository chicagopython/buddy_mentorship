# Contribution Guidelines

#### Table of Contents

<!-- TOC -->

- [How to Contribute](#how-to-contribute)
- [Workflow](#workflow)
- [Development Practices and Standards](#development-practices-and-standards)
- [Set up Git and a GitHub Account](#set-up-git-and-a-github-account)
- [Fork and Clone](#fork-and-clone)
- [Set up a Development Environment](#set-up-a-development-environment)
- [Create a Feature Branch](#create-a-feature-branch)
- [Rebase on Master and Squash](#rebase-on-master-and-squash)
- [Create a Pull Request to the master branch](#create-a-pull-request-to-the-master-branch)
- [For Maintainers](#for-maintainers)
- [Guides](#guides)
  - [Creating New Django App](#creating-new-django-app)

<!-- /TOC -->

## How to Contribute

First off, thank you for considering contributing to `Buddy Mentorship`!
It’s thanks to people like you that we continue to have a high-quality, updated and documented app.

There are a few key ways to contribute:
1. Writing new code
2. Writing tests
3. Writing documentation
4. Supporting fellow developers on StackOverflow.com.

No contribution is too small!
Please submit as many fixes for typos and grammar bloopers as you can!

Regardless of which of these options you choose,
this document is meant to make contribution more accessible by codifying tribal knowledge and expectations.
Don’t be afraid to ask questions if something is unclear!

## Workflow

1. Set up Git and a GitHub account
2. Buddy Mentorship follows a [forking workflow](https://www.atlassian.com/git/tutorials/comparing-workflows/forking-workflow), so next fork and clone the repo.
3. Set up a development environment.
4. Create a feature branch.
   Pull requests should be limited to one change only, where possible, and reference an existing issue.
   Contributing through short-lived feature branches ensures contributions can get merged quickly and easily.
5. Rebase on master and squash any unnecessary commits.
   We do not automatically squash on merge, because we trust our contributors to decide which commits within a feature are worth breaking out.
6. Always add tests and docs for your code.
7. Make sure your changes pass our CI.
   You won’t get any feedback until it’s green unless you ask for it.
8. Once you’ve addressed review feedback, make sure to bump the pull request with a short note, so we know you’re done.

Each of these abbreviated workflow steps has additional instructions in sections below.


## Development Practices and Standards

- Obey [`black`'s code formatting'](https://black.readthedocs.io/en/stable/the_black_code_style.html) and [Google's docstring format](https://sphinxcontrib-napoleon.readthedocs.io/en/latest/example_google.html).
- Use underscores to separate words in non-class names.
  E.g. `n_samples` rather than `nsamples`.
- Don't ever use wildcard imports (`from module import *`).
  It's considered to be a bad practice by the [official Python recommendations](https://docs.python.org/3/tutorial/modules.html#importing-from-a-package).
  The reasons it's undesireable are that it
  pollutes the namespace,
  makes it harder to identify the origin of code,
  and, most importantly, prevents using a static analysis tool like pyflakes to automatically find bugs.
- Any new module, class, or function requires units tests and a docstring.
  Test-Driven Development (TDD) is encouraged.
- Don’t break backward compatibility.
  In the event that an interface needs redesign to add capability,
  a deprecation warning should be raised in future minor versions,
  and the change will only be merged into the next major version release.
- [Semantic line breaks](https://sembr.org/) are encouraged.


## Set up Git and a GitHub Account

- If you don't already have a GitHub account, you can register for free.
- If you don't already have Git installed,
  you can follow these [git installation instructions](https://help.github.com/en/articles/set-up-git).


## Fork and Clone

1. You will need your own fork to work on the code. Go to the [project page](https://github.com/chicagopython/buddy_mentorship) and hit the Fork button.
2. Next, you'll want to clone your fork to your machine:

    ```bash
    git clone https://github.com/chicagopython/buddy_mentorship.git buddy_mentorship-dev
    cd buddy_mentorship-dev
    git remote add upstream https://github.com/chicagopython/buddy_mentorship.git
    ```


## Set up a Development Environment

1. Ensure you you have `pipenv` [installed](https://pipenv.kennethreitz.org/en/latest/#install-pipenv-today)
2. Install the dependencies
    ```bash
        pipenv install --dev
    ```
3. Make sure to configure your [editor to use black](https://github.com/psf/black#editor-integration)
4. Ensure you have a local instance of postgres running that matches the settings in `buddy_mentorship/settings/local.py`.
  If you have docker, you can achieve this by running
    ```bash
        docker run --name postgres -e POSTGRES_USER=buddy_mentorship  -e POSTGRES_DB='buddy_mentorship' -p 5432:5432 -d postgres
    ```
5. Run all migrations
    ```bash
        python manage.py migrate --settings=buddy_mentorship.settings.local
    ```
6. Run the local server
    ```bash
        python manage.py runserver --settings=buddy_mentorship.settings.local
    ```


## Create a Feature Branch

To add a new feature, you will create every feature branch off of the master branch:

```bash
git checkout master
git checkout -b feature/<feature_name_in_snake_case>
```


## Rebase on Master and Squash

If you are new to rebase, there are many useful tutorials online,
such as [Atlassian's](https://www.atlassian.com/git/tutorials/rewriting-history/git-rebase).
Feel free to follow your own workflow,
though if you have an default git editor set up,
interactive rebasing is an easy way to go about it:

```bash
git checkout feature/<feature_name_in_snake_case>
git rebase -i master
```


## Create a Pull Request to the master branch

[Create a pull request](https://help.github.com/en/articles/creating-a-pull-request-from-a-fork)
to the master branch of Buddy Mentorship.
Tests will be be triggered to run via xxx.
Check that your PR passes CI,
since it won't be reviewed for inclusion until it passes all steps.


## For Maintainers

Steps for maintainers are largely the same,
with a few additional steps before releasing a new version:

-   Update version in xxx.
-   Update the CHANGELOG.md and the main README.md (as appropriate).
-   Rebuild the docs in your local version to verify how they render using:

    ```bash
    xxx
    ```
-   Test the new deployment/migration:

    ```bash
    xxx
    ```
-   Releases are indicated using git tags.
    Create a tag locally for the apporiate commit in master, and push that tag to GitHub.
    Travis's CD is triggered on tags within master:

```bash
    git tag -a v<#.#.#> <SHA-goes-here> -m "buddy mentorship version <#.#.#>"
    git push origin --tags
```


## Guides

### Creating New Django App

All apps are located in the `apps/` folder. To create a new
[Django application](https://docs.djangoproject.com/en/3.0/ref/applications/)
inside this project:

1. Create an `[app_name]` folder in the `apps/` directory for your app
1. `python manage.py startapp users ./apps/[app_name]`
1. Add `[app_name]` to the `INSTALLED_APPS` in the the Django settings file,
  `buddy_mentorship/settings/local.py`
