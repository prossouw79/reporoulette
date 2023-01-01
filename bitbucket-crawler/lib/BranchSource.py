import json
import time
from datetime import datetime
from typing import Tuple, List

import requests
from .storage.dto import *
from requests import Response
from requests.auth import HTTPBasicAuth


class BranchSource:
    @classmethod
    def get_branches(
            cls,
            bitbucket_username: str,
            bitbucket_app_password: str,
            repo_workspace: str,
            repo_name: str,
            page_length: int = 100,
            branch_page_limit: int = -1
    ) -> List[Tuple[Branch, RepoBranchLink]]:
        results: List[Tuple[Branch, RepoBranchLink]] = []

        auth = HTTPBasicAuth(bitbucket_username, bitbucket_app_password)

        starting_branch_page_url = f"https://api.bitbucket.org/2.0/repositories/{repo_workspace}/{repo_name}/refs"
        next_page_url = starting_branch_page_url
        branches_page_number = 1

        has_more_pages = True
        branch_params = {"pagelen": f"{page_length}"}

        while has_more_pages:
            if branch_page_limit == 1 and branches_page_number == 1:
                print(f"Only a single page of branches will be fetched")
            elif branch_page_limit > 0 and branches_page_number >= branch_page_limit:
                print(f"Hit branch page limit: {branch_page_limit}")
                break

            print(f"Fetching page {branches_page_number}: Branches of {repo_name} ")
            response: Response = requests.get(
                next_page_url, auth=auth, params=branch_params
            )

            backoff_s = 10
            while response.status_code == 429:
                print(f"Waiting {backoff_s}s before retrying")
                time.sleep(backoff_s)
                response = requests.get(next_page_url, auth=auth, params=branch_params)

                if response.status_code == 429:
                    backoff_s *= 2

            page_data = json.loads(response.text)
            if page_data.get("next") is not None:
                next_page_url = page_data.get("next")
                has_more_pages = True
                branches_page_number += 1
            else:
                has_more_pages = False

            branches = json.loads(response.text)
            values = branches.get("values")

            for bi, b in enumerate(values):
                branch = Branch(
                    name=b.get("name"),
                    repo=repo_name,
                    url=b.get("links", {}).get("html", {}).get("href"),
                    update_ts=datetime.now().isoformat(),
                )

                link = RepoBranchLink(
                    repo_name=repo_name,
                    branch_name=branch.name,
                )
                results.append((branch, link))

        print(f"Fetched {len(results)} branches for {repo_name}")
        return results
