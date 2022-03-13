import os
import pprint

import requests


class GitHub:
    def __init__(self) -> None:
        self.github_url = "https://api.github.com"
        self.token = os.getenv('GH_TOKEN')
        self.s = requests.Session()

    def get_header(self):
        return {
            "Accept": "application/json",
            "Authorization": f"token {self.token}",
        }

    def get(self, url):
        if self.token:
            response = requests.get(url, headers=self.get_header())
        else:
            response = requests.get(url)
        return response.json()

    def get_repo_status(self, repo, branch="master"):
        url = f"{self.github_url}/repos/analogdevicesinc/{repo}/commits/{branch}/status"
        response = self.get(url)
        return response["state"]

    def get_repo_checks(self, repo, branch="master"):
        url = f"{self.github_url}/repos/analogdevicesinc/{repo}/commits/{branch}/check-runs"
        response = self.get(url)
        checks = []
        for check in response["check_runs"]:
            checks.append({"name": check["name"], "status": check["conclusion"]})

        return checks

    def get_commit_author(self, repo, commit_id):
        url = f"{self.github_url}/repos/analogdevicesinc/{repo}/commits/{commit_id}"
        response = self.get(url)
        if "commit" not in response:
            print(response)
        return [
            response["commit"]["author"]["name"],
            response["commit"]["committer"]["date"],
        ]

    def get_commit_date(self, repo, commit_id):
        url = f"{self.github_url}/repos/analogdevicesinc/{repo}/commits/{commit_id}"
        response = self.get(url)
        if "commit" not in response:
            print(response)
        return response["commit"]["committer"]["date"]

    # def get_lastest_committed_branch(self, repo):
    #     page = 1
    #     import time
    #     branches = []
    #     while True:
    #         url = f"{self.github_url}/repos/analogdevicesinc/{repo}/branches?page={page}?per_page=100"
    #         page += 1
    #         new = 0
    #         response = self.get(url)
    #         for branch in response:
    #             if branch['name'] not in branches:
    #                 new += 1
    #                 branches.append(branch['name'])
    #         print(response)
    #         time.sleep(1)
    #         print(f"HERE {page}")
    #         # for branch in response:
    #         #     date = self.get_commit_date(repo,branch['commit']['sha'])
    #         #     print(branch['name'],date)
    #         #     # if branch['name'] == 'master':
    #         #     #     return branch['commit']['sha']
