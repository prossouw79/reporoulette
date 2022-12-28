import json
import time
from datetime import datetime
from typing import Tuple, List
from urllib import parse

import requests
from requests import Response
from requests.auth import HTTPBasicAuth

from lib.Models import Repo


class RepoSource:
    @classmethod
    def get_repos(cls, bitbucket_username: str, bitbucket_app_password: str) -> List[Repo]:
        result: List[Repo] = []
        auth = HTTPBasicAuth(bitbucket_username, bitbucket_app_password)

        starting_repo_page_url = 'https://api.bitbucket.org/2.0/repositories'
        next_page_url = starting_repo_page_url
        repo_page_number = 1

        date_range: Tuple[datetime,datetime]

        repo_has_more_pages = True
        repo_params = {
            "role": "member",
            "pagelen": "100",
            "sort": "-updated_on",
            "after": datetime(1970,1,1,0,0,0,0).isoformat()
        }
        while repo_has_more_pages:
            print(f"Fetching page {repo_page_number}: Repositories after {repo_params.get('after')} ")

            response: Response = requests.get(next_page_url, auth=auth, params=repo_params)

            backoff_s = 60
            while response.status_code == 429:
                print(f"Waiting {backoff_s}s before retrying")
                time.sleep(backoff_s)
                response = requests.get(next_page_url, auth=auth, params=repo_params)

                if response.status_code == 429:
                    backoff_s *= 2

            page_data = json.loads(response.text)
            if page_data.get('next') is not None:
                next_page_url = page_data.get('next')
                parsed_url = parse.parse_qs(next_page_url)
                repo_params['after'] = parsed_url['after'][0]
                repo_has_more_pages = True
                repo_page_number += 1
            else:
                repo_has_more_pages = False

            for repo_values in page_data['values']:
                workspace = repo_values.get('workspace', {}).get('slug')
                name = repo_values.get('name', {})
                if ' ' in name:
                    name = name.replace(' ', '-')
                repo_url = repo_values.get('links', {}).get('html', {}).get('href')

                repo = Repo(
                    name=name,
                    workspace=workspace,
                    url=repo_url,
                    update_ts=datetime.now().isoformat()
                )
                result.append(repo)
        print(f"Fetched {len(result)} repositories")
        return result
