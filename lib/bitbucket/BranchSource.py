import json
import time
from datetime import datetime
from typing import Tuple, List

import requests
from requests import Response
from requests.auth import HTTPBasicAuth

from lib.Models import Branch, RepoBranchLink


class BranchSource:
    @classmethod
    def get_branches(cls, bitbucket_username: str, bitbucket_app_password: str, repo_workspace: str, repo_name) -> List[Tuple[Branch,RepoBranchLink]]:
        results: List[Tuple[Branch,RepoBranchLink]] = []

        auth = HTTPBasicAuth(bitbucket_username, bitbucket_app_password)

        starting_branch_page_url = f"https://api.bitbucket.org/2.0/repositories/{repo_workspace}/{repo_name}/refs"
        next_page_url = starting_branch_page_url
        branches_page_number = 1

        has_more_pages = True
        branch_params = {
            "pagelen": "100",
        }

        while has_more_pages:
            print(f"Fetching page {branches_page_number}: Branches of {repo_name} ")
            response: Response = requests.get(next_page_url, auth=auth, params=branch_params)

            backoff_s = 60
            while response.status_code == 429:
                print(f"Waiting {backoff_s}s before retrying")
                time.sleep(backoff_s)
                response = requests.get(next_page_url, auth=auth, params=branch_params)

                if response.status_code == 429:
                    backoff_s *= 2

            page_data = json.loads(response.text)
            if page_data.get('next') is not None:
                next_page_url = page_data.get('next')
                has_more_pages = True
                branches_page_number += 1
            else:
                has_more_pages = False

            branches = json.loads(response.text)

            for b in branches.get('values'):
                branch = Branch(
                    name=b.get('name'),
                    repo=repo_name,
                    url=b.get("links",{}).get("html",{}).get("href"),
                    update_ts=datetime.now().isoformat()
                )

                link = RepoBranchLink(
                    repo_name=repo_name,
                    branch_name=branch.name,
                )
                results.append((branch,link))

        print(f"Fetched {len(results)} branches for {repo_name}")
        return results
