import sys
import traceback
from datetime import datetime
from pathlib import Path
from typing import List
from typing import Tuple

import attrs
from sqlite_integrated import *

from lib.BranchSource import BranchSource
from lib.CommitSource import CommitSource
from lib.storage.dto import *
from lib.RepoSource import RepoSource

environment_variables = os.environ.copy()

# REQUIRED CONFIGURATION
BITBUCKET_USERNAME = environment_variables.get("BITBUCKET_USERNAME", None)
BITBUCKET_PASSWORD = environment_variables.get("BITBUCKET_PASSWORD", None)
DATABASE_DIR = environment_variables.get("DATABASE_DIR", None)

# OPTIONAL CONFIGURATION
REQUEST_PAGE_SIZE = int(environment_variables.get('REQUEST_PAGE_SIZE', '10'))
IGNORED_REPOS = environment_variables.get("IGNORED_REPOS", '').split(',')
BRANCH_PAGE_LIMIT = int(environment_variables.get('BRANCH_PAGE_LIMIT', '1'))
COMMIT_PAGE_LIMIT = int(environment_variables.get('COMMIT_PAGE_LIMIT', '1'))
MAIN_BRANCH_ONLY = True if environment_variables.get('MAIN_BRANCH_ONLY', 'true').lower() == 'true' else False
DB_SILENT = bool(environment_variables.get('DB_SILENT', 'true'))

if BITBUCKET_USERNAME is None or BITBUCKET_PASSWORD is None or DATABASE_DIR is None:
    print("Set required environment variables: BITBUCKET_USERNAME, BITBUCKET_PASSWORD, DATABASE_DIR")
    sys.exit(1)

REPO_TABLE = "repos"
BRANCH_TABLE = "branches"
COMMIT_TABLE = "commits"

REPO_BRANCH_LINKING_TABLE = "link_repo_branches"
BRANCH_COMMIT_LINKING_TABLE = "link_branch_commits"

db: Database


def create_database() -> None:
    global db

    DATABASE_PATH = Path(os.getcwd()).joinpath(DATABASE_DIR)
    DATABASE_FILE = os.path.join(DATABASE_PATH, "database.db")

    if not DATABASE_PATH.exists():
        os.makedirs(DATABASE_PATH, exist_ok=True)

    create_new = False if os.path.exists(DATABASE_FILE) else True
    if create_new:
        print(f"Creating new database {DATABASE_FILE}")
    else:
        print(f"Using existing database {DATABASE_FILE}")

    db = Database(DATABASE_FILE, new=create_new, silent=DB_SILENT)

    if not db.is_table(REPO_TABLE):
        print("Creating Repo table")
        db.create_table(
            REPO_TABLE,
            [
                Column("id", "integer", primary_key=True),
                Column("name", "string"),
                Column("workspace", "string"),
                Column("main_branch", "string"),
                Column("main_branch_url", "string"),
                Column("repo_url", "string"),
                Column("update_ts", "string"),
            ],
        )

    if not db.is_table(BRANCH_TABLE):
        print("Creating branch table")
        db.create_table(
            BRANCH_TABLE,
            [
                Column("id", "integer", primary_key=True),
                Column("name", "string"),
                Column("repo", "string"),
                Column("url", "string"),
                Column("update_ts", "string"),
            ],
        )

    if not db.is_table(COMMIT_TABLE):
        print("Creating commit table")
        db.create_table(
            COMMIT_TABLE,
            [
                Column("id", "integer", primary_key=True),
                Column("hash", "string"),
                Column("message", "string"),
                Column("summary", "string"),
                Column("date", "string"),
                Column("author", "string"),
                Column("email", "string"),
                Column("diff_link", "string"),
                Column("repo_url", "string"),
            ],
        )

    if not db.is_table(REPO_BRANCH_LINKING_TABLE):
        print("Creating repo-branch linking table")
        db.create_table(
            REPO_BRANCH_LINKING_TABLE,
            [
                Column("id", "integer", primary_key=True),
                Column("repo_name", "string"),
                Column("branch_name", "string"),
            ],
        )

    if not db.is_table(BRANCH_COMMIT_LINKING_TABLE):
        print("Creating branch-commit linking table")
        db.create_table(
            BRANCH_COMMIT_LINKING_TABLE,
            [
                Column("id", "integer", primary_key=True),
                Column("branch_name", "string"),
                Column("commit_hash", "string"),
            ],
        )


def fetch_repos() -> None:
    global db

    repo: Repo
    repos = RepoSource.get_repos(BITBUCKET_USERNAME, BITBUCKET_PASSWORD, IGNORED_REPOS)
    for i, repo in enumerate(repos):
        repo_d = attrs.asdict(repo)
        query = db.SELECT("name").FROM(REPO_TABLE).WHERE("repo_url").LIKE(repo.repo_url)
        result: List[DatabaseEntry] = query.run()

        if result is None or len(result) == 0:
            # print(f"Inserting repo: {repo.name}")
            db.add_entry(repo_d, REPO_TABLE)
            db.save()
        else:
            print("Already added repo:", repo.name)


def fetch_repo_branches() -> None:
    global db

    repo_query = db.SELECT("*").FROM(REPO_TABLE)
    repo_query_results: List[DatabaseEntry] = repo_query.run()
    repo_query_results.sort(key=lambda x: x.get('name'), reverse=False)

    repo_query_result: DatabaseEntry
    for ir, repo_query_result in enumerate(repo_query_results):
        try:
            repo = Repo.from_db_entry(repo_query_result)

            if MAIN_BRANCH_ONLY:
                branch = Branch(repo.main_branch, repo.name, repo.main_branch_url, datetime.now().isoformat())
                link = RepoBranchLink(repo.name, repo.main_branch)

                branch_d = attrs.asdict(branch)

                branch_query = (db.SELECT("url").FROM(BRANCH_TABLE).WHERE("url").LIKE(branch.url))
                branch_result: List[DatabaseEntry] = branch_query.run()
                if branch_result is None or len(branch_result) == 0:
                    db.add_entry(branch_d, BRANCH_TABLE)
                    db.save()

                link_d = attrs.asdict(link)
                existing_link_sql = f'SELECT * FROM {REPO_BRANCH_LINKING_TABLE} ' \
                                    f'WHERE repo_name == "{repo.name}" AND ' \
                                    f'branch_name == "{branch.name}"'

                existing_links = db.cursor.execute(existing_link_sql).fetchall()

                if existing_links is None or len(existing_links) == 0:
                    # print(f"Inserting repo branch link: {repo.name} -> {branch.name}")
                    db.add_entry(link_d, REPO_BRANCH_LINKING_TABLE)
                    db.save()
            else:
                print(f"{ir + 1}/{len(repo_query_results)}: Fetching branches for {repo.name}")

                branch_and_link: Tuple[List[Branch], List[RepoBranchLink]]
                branch_links = BranchSource.get_branches(BITBUCKET_USERNAME, BITBUCKET_PASSWORD, repo.workspace,
                                                         repo.name, page_length=REQUEST_PAGE_SIZE,
                                                         branch_page_limit=BRANCH_PAGE_LIMIT)
                for ib, branch_and_link in enumerate(branch_links):
                    branch: Branch
                    link: RepoBranchLink
                    branch, link = branch_and_link

                    branch_d = attrs.asdict(branch)

                    branch_query = (
                        db.SELECT("url").FROM(BRANCH_TABLE).WHERE("url").LIKE(branch.url)
                    )
                    branch_result: List[DatabaseEntry] = branch_query.run()
                    if branch_result is None or len(branch_result) == 0:
                        # print(f"Inserting branch: {branch.name}")
                        db.add_entry(branch_d, BRANCH_TABLE)
                        db.save()

                    link_d = attrs.asdict(link)
                    existing_link_sql = f'SELECT * FROM {REPO_BRANCH_LINKING_TABLE} ' \
                                        f'WHERE repo_name == "{repo.name}" AND ' \
                                        f'branch_name == "{branch.name}"'

                    existing_links = db.cursor.execute(existing_link_sql).fetchall()

                    if existing_links is None or len(existing_links) == 0:
                        # print(f"Inserting repo branch link: {repo.name} -> {branch.name}")
                        db.add_entry(link_d, REPO_BRANCH_LINKING_TABLE)
                        db.save()

        except Exception:
            print(f"An error occurred fetching branches")
            traceback.print_exc()
            print("Continuing")
            pass


def fetch_branch_commits() -> None:
    global db
    repo_query = db.SELECT("*").FROM(REPO_TABLE)
    repo_query_results: List[DatabaseEntry] = repo_query.run()
    repo_query_results.sort(key=lambda x: x.get('name'), reverse=False)
    repo_query_result: DatabaseEntry
    for ir, repo_query_result in enumerate(repo_query_results):

        branch_query = db.SELECT("*").FROM(BRANCH_TABLE).WHERE('repo').LIKE(repo_query_result.get('name'))
        branch_query_results: List[DatabaseEntry] = branch_query.run()

        branch_query_result: DatabaseEntry
        for ib, branch_query_result in enumerate(branch_query_results):
            try:
                branch = Branch.from_db_entry(branch_query_result)
                print(
                    f"Repo [{ir + 1}/{len(repo_query_results)}] Branch [{ib + 1}/{len(branch_query_results)}]: Fetching commits for branch {branch.name} of  {branch.repo}"
                )

                repo_q: DatabaseEntry = list(
                    filter(lambda r: r.get("name") == branch.repo, repo_query_results)
                )[0]
                repo = Repo.from_db_entry(repo_q)

                commit_links = CommitSource.get_commits(
                    BITBUCKET_USERNAME, BITBUCKET_PASSWORD, repo, page_length=REQUEST_PAGE_SIZE, branch=branch,
                    commit_page_limit=COMMIT_PAGE_LIMIT
                )
                commit_and_link: Tuple[List[Commit], List[BranchCommitLink]]
                for ci, commit_and_link in enumerate(commit_links):
                    commit: Commit
                    link: BranchCommitLink
                    commit, link = commit_and_link

                    commit_d = attrs.asdict(commit)
                    link_d = attrs.asdict(link)
                    query = (
                        db.SELECT("diff_link")
                        .FROM(COMMIT_TABLE)
                        .WHERE("diff_link")
                        .LIKE(commit.diff_link)
                    )
                    result: List[DatabaseEntry] = query.run()

                    if result is None or len(result) == 0:
                        # print(f"Inserting commit: {commit.diff_link}")
                        db.add_entry(commit_d, COMMIT_TABLE)
                        db.save()

                    existing_link_sql = f'SELECT * FROM {BRANCH_COMMIT_LINKING_TABLE} WHERE branch_name == "{branch.name}" AND commit_hash == "{commit.hash}"'

                    existing_links = db.cursor.execute(existing_link_sql).fetchall()

                    if existing_links is None or len(existing_links) == 0:
                        # print(f"Inserting branch commit link: {branch.name} -> {commit.hash}")
                        db.add_entry(link_d, BRANCH_COMMIT_LINKING_TABLE)
                        db.save()

            except Exception:
                print(f"An error occurred fetching commits ")
                traceback.print_exc()
                print("Continuing")
                pass


def main():
    global db

    create_database()
    fetch_repos()
    fetch_repo_branches()
    fetch_branch_commits()

    print("Done")
    db.close()


if __name__ == "__main__":
    main()
