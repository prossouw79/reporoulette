from typing import List, Tuple
import json
import time
from datetime import datetime, timezone
from json import JSONDecodeError

import requests as requests
from dateutil.relativedelta import relativedelta
from requests import Response
from requests.auth import HTTPBasicAuth

from lib.Models import Branch, BranchCommitLink, Repo, Commit


class CommitSource:
    @classmethod
    def get_commits(cls, bitbucket_username: str, bitbucket_app_password: str, repo: Repo, branch: Branch, month_delta: int = 12) -> List[Tuple[Commit,BranchCommitLink]]:
        auth = HTTPBasicAuth(bitbucket_username, bitbucket_app_password)
        results: List[Tuple[Commit,BranchCommitLink]] = []

        commit_url = f"https://api.bitbucket.org/2.0/repositories/{repo.workspace}/{repo.name}/commits/{branch.name}"

        commit_has_next = True
        current_month_delta = 1
        commit_page_number = 1

        while commit_has_next and current_month_delta <= month_delta:
            dt = datetime.now(timezone.utc) - relativedelta(months=current_month_delta)
            print(f"Looking for commits after {dt}, page #{commit_page_number}")
            commit_current_page_params = {
                "pagelen": "100",
                "filter": f"updated_on <= {dt.year}-{dt.month}-{dt.day}",
                "page": f"{commit_page_number}"
            }

            response: Response = requests.get(commit_url, auth=auth, params=commit_current_page_params)

            backoff_s = 60
            while response.status_code == 429:
                print(f"Waiting {backoff_s}s before retrying")
                time.sleep(backoff_s)
                response = requests.get(commit_url, auth=auth, params=commit_current_page_params)

                if response.status_code == 429:
                    backoff_s *= 2

            try:
                commit_page_data = json.loads(response.text)
                print(f"{repo.workspace}/{repo.name} parsing {len(commit_page_data['values'])} commits on branch {branch.name}")

                if commit_page_data.get('next') is not None:
                    commit_has_next = True
                    commit_page_number += 1
                else:
                    commit_has_next = False
                    current_month_delta += 1

                for values in commit_page_data.get('values'):
                    repo_d: dict = values.get('repository')
                    author: str = values.get('author', {}).get('raw')
                    email: str = author[author.find("<") + 1:author.find(">")].lower()
                    commit = Commit(
                        hash=values.get('hash'),
                        date=values.get('date'),
                        author=author.replace(email, '').replace('<>', '').strip(),
                        email=email,
                        diff_link=values.get('links', {}).get('html', {}).get('href'),
                        repo_url=repo_d.get('links', {}).get('html', {}).get('href', {})
                    )

                    link = BranchCommitLink(branch.name,commit.hash)

                    results.append((commit,link))

            except JSONDecodeError as e:
                print("Invalid JSON for", response)
                commit_has_next = False

        print(f"Fetched {len(results)} commits for {repo.name} branch {branch.name}")
        return results
