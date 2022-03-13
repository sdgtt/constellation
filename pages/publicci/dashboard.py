import datetime

from flask import render_template

from .github import GitHub

# from github import GitHub


class Dashboard:
    def __init__(self, gh_projects):
        self.gh = GitHub()
        self.gh_projects = gh_projects
        self.last_query = None
        self.last_query_data = None

    def get_gh_statuses(self):
        statuses = {}
        for project in self.gh_projects:
            if "branch" in project:
                b = project["branch"]
            else:
                b = "master"
            au = self.gh.get_commit_author(repo=project["repo"], commit_id=b)
            status = self.gh.get_repo_status(repo=project["repo"], branch=b)
            checks = self.gh.get_repo_checks(repo=project["repo"], branch=b)
            statuses[project["repo"]] = {
                "author": au[0],
                "status": status,
                "checks": checks,
                "date": au[1],
            }
        return statuses

    def get_statuses(self):
        statues = self.get_gh_statuses()
        # statues += self.get_jk_statuses()
        return statues

    def _do_update(self):
        """Limit GH queries to max every N seconds"""
        if not self.last_query:
            return True

        diff = datetime.datetime.now() - self.last_query
        if diff > datetime.timedelta(seconds=20):
            return True

        return False

    def get_status_html(self):
        if self._do_update():
            self.last_query = datetime.datetime.now()
            self.last_query_data = self.get_statuses()
        return render_template(
            "publicci/index.html", projects=self.last_query_data, date=self.last_query
        )


if __name__ == "__main__":
    p = Dashboard(gh_projects=[{"repo": "libiio"}, {"repo": "pyadi-iio"}])
    # import pprint
    # pprint.pprint(p.get_statuses())
    # pprint.pprint(p.gh.get_repo_checks("libiio"))
    # p.gh.get_repo_checks("libiio")
