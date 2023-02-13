import json
import pprint

from app.models.artifacts import Artifacts
from app.models.boards import Boards
from app.models.boot_tests import BoardBootTests
from app.models.db import DB


class Score:
    """Class representing a scorecard data"""

    fields = [
        "jenkins_project",
        "size",
        "boards",
        "deprecated",
        "branch",
        "builds",
        "boot_tests_count",
        "artifacts_count",
        "summaries",
        "regressions",
    ]

    def __init__(
        self,
        jenkins_project="HW_tests/HW_test_multiconfig",
        size=2,
        branch="boot_partition_master",
        board=None,
        deprecated=[],
    ):
        self.jenkins_project = jenkins_project
        self.size = size
        self.board = board
        self.branch = branch
        self.deprecated = deprecated
        self.__initialize_fields()

    def __initialize_fields(self):

        # get domain from samples
        bts = BoardBootTests(
            jenkins_project_name=self.jenkins_project,
            source_adjacency_matrix=self.branch,
            boot_folder_name=self.board,
        )
        self.builds = bts.latest_builds(self.size)
        self.boards = bts.latest_builds_boards(self.size)
        self.boot_tests, self.boot_tests_count = self.get_boot_tests()
        self.artifacts, self.artifacts_count = self.get_artifacts()
        self.test_results = self.get_test_results()
        self.regressions = self.get_regressions()

    def display(self):
        return self.__dict__

    def get_boot_tests(self):
        """Get BoardBootTests object for the latest self.size builds"""
        boot_tests = {}
        boot_tests_count = {}
        for build_no in self.builds:
            boot_tests[build_no] = BoardBootTests(
                jenkins_project_name=self.jenkins_project,
                source_adjacency_matrix=self.branch,
                jenkins_build_number=build_no,
                boot_folder_name=self.board,
            ).boot_tests
            boot_tests_count[build_no] = len(boot_tests[build_no])
        return boot_tests, boot_tests_count

    def get_artifacts(self):
        artifacts = {}
        artifacts_count = {}
        for build_no in self.builds:
            artifacts[build_no] = Artifacts(
                job=self.jenkins_project, job_no=build_no, target_board=self.board
            ).artifacts
            artifacts_count[build_no] = len(artifacts[build_no])
        return artifacts, artifacts_count

    def get_test_results(self):  # noqa: C901
        tests = [
            "boards",
            "booted",
            "not_booted",
            "linux_prompt_not_reached",
            "uboot_not_reached",
            "drivers_enumerated",
            "drivers_missing",
            "dmesg_warnings_found",
            "dmesg_errors_found",
            "pytest_errors",
            "pytest_failures",
            "pytest_skipped",
            "pytest_tests",
            "matlab_errors",
            "matlab_failures",
            "matlab_skipped",
            "matlab_tests",
        ]
        supported_artifacts = {
            "drivers_enumerated": "enumerated_devs",
            "drivers_missing": "missing_devs",
            "dmesg_warnings_found": "dmesg_warn",
            "dmesg_errors_found": "dmesg_err",
            "pytest_errors": "pytest_error",
            "pytest_failures": "pytest_failure",
            "pytest_skipped": "pytest_skipped",
        }
        report = {}
        # for every build
        for bn, bts in self.boot_tests.items():
            # initialize report
            report[bn] = {}
            for test in tests:
                if test in [
                    "boards",
                    "booted",
                    "linux_prompt_not_reached",
                    "uboot_not_reached",
                ]:
                    report[bn].update({test: {"count": 0, "data": []}})
                else:
                    report[bn].update({test: {"count": 0, "data": {}}})

            # for boot_test within the build
            for bt in bts:
                for test in tests:
                    if test == "boards":
                        report[bn][test]["count"] += 1
                        if bt.boot_folder_name not in report[bn][test]["data"]:
                            report[bn][test]["data"].append(bt.boot_folder_name)
                    elif test == "booted":
                        if bt.linux_prompt_reached:
                            report[bn][test]["count"] += 1
                            report[bn][test]["data"].append(bt.boot_folder_name)
                    elif test == "not_booted":
                        if not bt.linux_prompt_reached:
                            report[bn][test]["count"] += 1
                            if (
                                bt.last_failing_stage_failure
                                not in report[bn][test]["data"]
                            ):
                                report[bn][test]["data"][
                                    bt.last_failing_stage_failure
                                ] = [bt.boot_folder_name]
                            else:
                                report[bn][test]["data"][
                                    bt.last_failing_stage_failure
                                ].append(bt.boot_folder_name)
                    elif test == "linux_prompt_not_reached":
                        if bt.uboot_reached:
                            if not bt.linux_prompt_reached:
                                report[bn][test]["count"] += 1
                                report[bn][test]["data"].append(bt.boot_folder_name)
                    elif test == "uboot_not_reached":
                        if not bt.uboot_reached:
                            report[bn][test]["count"] += 1
                            report[bn][test]["data"].append(bt.boot_folder_name)
                    else:
                        report[bn][test]["count"] += int(getattr(bt, test))
                        if test in supported_artifacts:
                            for ar in self.artifacts[bn]:
                                if ar.artifact_info_type == supported_artifacts[test]:
                                    if ar.target_board == bt.boot_folder_name:
                                        entry = ar.payload
                                        details = ar.target_board
                                        if test in [
                                            "pytest_errors",
                                            "pytest_failures",
                                            "pytest_skipped",
                                        ]:
                                            if not ar.payload_param == "NA":
                                                entry += "(" + ar.payload_param + ")"
                                        if entry in report[bn][test]["data"]:
                                            report[bn][test]["data"][entry].append(
                                                details
                                            )
                                        else:
                                            report[bn][test]["data"].update(
                                                {entry: [details]}
                                            )

            # test data credibility
            for test in [
                "booted",
                "linux_prompt_not_reached",
                "uboot_not_reached",
                "drivers_enumerated",
                "drivers_missing",
                "dmesg_warnings_found",
                "dmesg_errors_found",
                "pytest_errors",
                "pytest_failures",
                "pytest_skipped",
            ]:
                if isinstance(report[bn][test]["data"], list):
                    assert report[bn][test]["count"] == len(report[bn][test]["data"])
                else:
                    count = 0
                    for k, boards in report[bn][test]["data"].items():
                        for board in boards:
                            count += 1
                    assert report[bn][test]["count"] == count
        return report

    def get_regressions(self):
        regressions = {}
        regression_fields = [
            "regress_missing_logs",
            "regress_boards_removed",
            "regress_boards_added",
            "regress_not_booted_added",
            "regress_not_booted_removed",
            "regress_not_booted_unresolved",
            "regress_drivers_missing_added",
            "regress_drivers_missing_removed",
            "regress_drivers_missing_unresolved",
            "regress_dmesg_errors_found_added",
            "regress_dmesg_errors_found_removed",
            "regress_dmesg_errors_found_unresolved",
            "regress_dmesg_warnings_found_added",
            "regress_dmesg_warnings_found_removed",
            "regress_dmesg_warnings_found_unresolved",
        ]

        sorted_builds = list(enumerate(sorted(self.builds, key=int)))

        for builds in sorted_builds:
            index = builds[0]
            build = builds[1]
            if not str(build) in regressions:
                regressions[str(build)] = {}
            for f in regression_fields:
                if f == "regress_missing_logs":
                    regressions[str(build)][f] = self.__get_removed(
                        self.boards, self.test_results[str(build)]["boards"]["data"]
                    )
                elif f in ["regress_boards_removed", "regress_boards_added"]:
                    if index == 0:
                        regressions[str(build)][f] = []
                    else:
                        r, a, u = self.__get_diff(
                            self.test_results[sorted_builds[index - 1][1]]["boards"][
                                "data"
                            ],
                            self.test_results[build]["boards"]["data"],
                        )
                        if f == "regress_boards_removed":
                            regressions[str(build)]["regress_boards_removed"] = r
                        elif f == "regress_boards_added":
                            regressions[str(build)]["regress_boards_added"] = a

                elif f in [
                    "regress_not_booted_added",
                    "regress_not_booted_removed",
                    "regress_not_booted_unresolved",
                    "regress_drivers_missing_added",
                    "regress_drivers_missing_removed",
                    "regress_drivers_missing_unresolved",
                    "regress_dmesg_errors_found_added",
                    "regress_dmesg_errors_found_removed",
                    "regress_dmesg_errors_found_unresolved",
                    "regress_dmesg_warnings_found_added",
                    "regress_dmesg_warnings_found_removed",
                    "regress_dmesg_warnings_found_unresolved",
                ]:
                    if index == 0:
                        regressions[str(build)][f] = {}
                    else:
                        info = f.split("_")[1] + "_" + f.split("_")[2]
                        r_type = f.split("_")[3]
                        if len(f.split("_")) > 4:
                            info = (
                                f.split("_")[1]
                                + "_"
                                + f.split("_")[2]
                                + "_"
                                + f.split("_")[3]
                            )
                            r_type = f.split("_")[4]

                        r, a, u = self.__get_diff(
                            self.test_results[sorted_builds[index - 1][1]][info][
                                "data"
                            ].keys(),
                            self.test_results[build][info]["data"].keys(),
                        )
                        regressions[str(build)][f] = {}
                        if r_type == "removed":
                            for removed in r:
                                failing_boards = self.test_results[
                                    sorted_builds[index - 1][1]
                                ][info]["data"][removed]
                                regressions[str(build)][f].update(
                                    {removed: failing_boards}
                                )
                        elif r_type == "added":
                            for added in a:
                                failing_boards = self.test_results[build][info]["data"][
                                    added
                                ]
                                regressions[str(build)][f].update(
                                    {added: failing_boards}
                                )
                        elif r_type == "unresolved":
                            for unresolved in u:
                                failing_boards = self.test_results[build][info]["data"][
                                    unresolved
                                ]
                                regressions[str(build)][f].update(
                                    {unresolved: failing_boards}
                                )

        return regressions

    def __get_removed(self, list_a, list_b):
        return list(set(list_a) - set(list_b))

    def __get_added(self, list_a, list_b):
        return list(set(list_b) - set(list_a))

    def __get_diff(self, list_a, list_b):
        removed = list(set(list_a) - set(list_b))
        added = list(set(list_b) - set(list_a))
        unchanged = list(set(list_a).intersection(set(list_b)))
        return removed, added, unchanged

    def to_json(self):
        sc_data = {}
        for field in self.fields:
            if field == "summaries":
                sc_data[field] = self.test_results
            else:
                sc_data[field] = getattr(self, field)
        # return sc_data
        return json.dumps(obj=sc_data)

    def to_dict(self):
        sc_data = {}
        for field in self.fields:
            if field == "summaries":
                sc_data[field] = self.test_results
            else:
                sc_data[field] = getattr(self, field)
        return sc_data


if __name__ == "__main__":
    sc = Score(size=7, branch="boot_partition_master")
    # print(sc.boot_tests)
    # print(sc.boards)
    # print(sc.builds)
    # print(sc.boot_tests_count)
    # print(sc.artifacts_count)
    # pprint.pprint(sc.test_results['731']['dmesg_errors_found']['data'])
    # print(json.dumps(sc.test_results['731']))
    # print(sc.to_json())
