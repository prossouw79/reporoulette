from typing import Tuple
import os
from pathlib import Path
import sys
from typing import List

import attrs
from sqlite_integrated import * # type: ignore
import sqlite3

from lib.Models import Branch, BranchCommitLink, Repo, Commit, RepoBranchLink
from lib.bitbucket.BranchSource import BranchSource
from lib.bitbucket.CommitSource import CommitSource
from lib.bitbucket.RepoSource import RepoSource

environment_variables = os.environ.copy()

BITBUCKET_USERNAME = environment_variables.get('BITBUCKET_USERNAME', None) # username, not email
BITBUCKET_PASSWORD = environment_variables.get('BITBUCKET_PASSWORD', None) # app password
DATABASE_DIR = environment_variables.get('DATABASE_DIR', None)

if BITBUCKET_USERNAME is None or BITBUCKET_PASSWORD is None or DATABASE_DIR is None:
    print("Set required environment variables: BITBUCKET_USERNAME, BITBUCKET_PASSWORD, DATABASE_DIR")
    sys.exit(1)

REPO_TABLE = "repos"
BRANCH_TABLE = "branches"
COMMIT_TABLE = "commits"

REPO_BRANCH_LINKING_TABLE = "link_repo_branches"
BRANCH_COMMIT_LINKING_TABLE = "link_branch_commits"

def main():
    DATABASE_PATH = Path(os.getcwd()).joinpath(DATABASE_DIR)
    DATABASE_FILE = os.path.join(DATABASE_PATH, "database.db")

    if not DATABASE_PATH.exists():
        os.makedirs(DATABASE_PATH,exist_ok=True)

    create_new = False if os.path.exists(DATABASE_FILE) else True
    if create_new:
        print(f"Creating new database {DATABASE_FILE}")
    else:
        print(f"Using existing database {DATABASE_FILE}")

    db = Database(DATABASE_FILE, new=create_new, silent=True)
    db_raw = sqlite3.connect(DATABASE_FILE)

    if not db.is_table(REPO_TABLE):
        print("Creating repo table")
        db.create_table(REPO_TABLE, [
            Column("id", "integer", primary_key=True),
            Column("name", "string"),
            Column("workspace", "string"),
            Column("url", "string"),
            Column("update_ts", "string")
        ])
    
    if not db.is_table(BRANCH_TABLE):
        print("Creating branch table")
        db.create_table(BRANCH_TABLE, [
            Column("id", "integer", primary_key=True),
            Column("name", "string"),
            Column("repo", "string"),
            Column("url", "string"),
            Column("update_ts", "string")            
        ])

    if not db.is_table(COMMIT_TABLE):
        print("Creating commit table")
        db.create_table(COMMIT_TABLE, [
            Column("id", "integer", primary_key=True),
            Column("hash", "string"),
            Column("date", "string"),
            Column("author", "string"),
            Column("email", "string"),
            Column("diff_link", "string"),
            Column("repo_url", "string")
        ])

    if not db.is_table(REPO_BRANCH_LINKING_TABLE):
        print("Creating repo-branch linking table")
        db.create_table(REPO_BRANCH_LINKING_TABLE, [
            Column("id", "integer", primary_key=True),
            Column("repo_name", "string"),
            Column("branch_name", "string")
        ])

    if not db.is_table(BRANCH_COMMIT_LINKING_TABLE):
        print("Creating branch-commit linking table")
        db.create_table(BRANCH_COMMIT_LINKING_TABLE, [
            Column("id", "integer", primary_key=True),
            Column("branch_name", "string"),
            Column("commit_hash", "string")
        ])

    repo: Repo
    for repo in RepoSource.get_repos(BITBUCKET_USERNAME, BITBUCKET_PASSWORD):
        try:
            repo_d = attrs.asdict(repo)
            query = db.SELECT("name").FROM(REPO_TABLE).WHERE("url").LIKE(repo.url)
            result: List[DatabaseEntry] = query.run()

            if result is None or len(result) == 0:
                print(f"Inserting repo: {repo.name}")
                db.add_entry(repo_d, REPO_TABLE)
                db.save()

        except Exception as e:
            print("Exception occurred:",e)
            print("Continuing")
            pass

    repo_query = db.SELECT("*").FROM(REPO_TABLE)
    repo_query_results: List[DatabaseEntry] = repo_query.run()

    repo_query_result: DatabaseEntry
    for repo_query_result in repo_query_results:
        repo = Repo(
            name=repo_query_result.get("name"),
            workspace=repo_query_result.get("workspace"),
            url=repo_query_result.get("url"),
            update_ts=repo_query_result.get("update_ts")
        )

        branch_and_link: Tuple[List[Branch], List[RepoBranchLink]]
        for branch_and_link in BranchSource.get_branches(BITBUCKET_USERNAME,BITBUCKET_PASSWORD,repo.workspace,repo.name):
            branch: Branch
            link: RepoBranchLink
            branch, link = branch_and_link

            branch_d = attrs.asdict(branch)

            branch_query = db.SELECT("url").FROM(BRANCH_TABLE).WHERE("url").LIKE(branch.url)
            branch_result: List[DatabaseEntry] = branch_query.run()
            if branch_result is None or len(branch_result) == 0:
                print(f"Inserting branch: {branch.name}")
                db.add_entry(branch_d,BRANCH_TABLE)
                db.save()

            link_d = attrs.asdict(link)
            existing_link_sql=f'SELECT * FROM {REPO_BRANCH_LINKING_TABLE} WHERE repo_name == "{repo.name}" AND branch_name == "{branch.name}"'
            existing_links = db.cursor.execute(existing_link_sql).fetchall()

            if existing_links is None or len(existing_links) == 0:
                print(f"Inserting repo branch link: {repo.name} -> {branch.name}")
                db.add_entry(link_d, REPO_BRANCH_LINKING_TABLE)
                db.save()

    branch_query = db.SELECT("*").FROM(BRANCH_TABLE)
    branch_query_results: List[DatabaseEntry] = branch_query.run()

    branch_query_result: DatabaseEntry
    for branch_query_result in branch_query_results:

        branch = Branch(
            name=branch_query_result.get('name'),
            repo=branch_query_result.get('repo'),
            url=branch_query_result.get('url'),
            update_ts=branch_query_result.get('update_ts')
        )
        repo_q: DatabaseEntry = list(filter(lambda r: r.get('name') == branch.repo , repo_query_results))[0]
        repo = Repo(
            name=repo_q.get("name"),
            workspace=repo_q.get("workspace"),
            url=repo_q.get("url"),
            update_ts=repo_q.get("update_ts")
        )

        commit_and_link: Tuple[List[Commit], List[BranchCommitLink]]
        for commit_and_link in CommitSource.get_commits(BITBUCKET_USERNAME,BITBUCKET_PASSWORD, repo,branch):
            commit: Commit
            link: BranchCommitLink
            commit, link = commit_and_link

            commit_d = attrs.asdict(commit)
            link_d = attrs.asdict(link)
            query = db.SELECT("diff_link").FROM(COMMIT_TABLE).WHERE("diff_link").LIKE(commit.diff_link)
            result: List[DatabaseEntry] = query.run()

            if result is None or len(result) == 0:
                print(f"Inserting commit: {commit.diff_link}")
                db.add_entry(commit_d, COMMIT_TABLE)
                db.save()
            
            existing_link_sql = f'SELECT * FROM {BRANCH_COMMIT_LINKING_TABLE} WHERE branch_name == "{branch.name}" AND commit_hash == "{commit.hash}"'
            existing_links = db.cursor.execute(existing_link_sql).fetchall()

            if existing_links is None or len(existing_links) == 0:
                print(f"Inserting branch commit link: {repo.name} -> {branch.name}")
                db.add_entry(link_d, BRANCH_COMMIT_LINKING_TABLE)
                db.save()   

    print("Done")
    db.close()


if __name__ == '__main__':
    main()
