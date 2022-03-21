from app.models.db import DB

class BootTest:
    def __init__(self, raw_boot_test_result=None):
        self.raw_boot_test_result = raw_boot_test_result
        self.__initialize_fields()
        
    def __initialize_fields(self):

        fields = [
            "boot_folder_name",
            "hdl_hash",
            "linux_hash",
            "boot_partition_hash",
            "hdl_branch",
            "linux_branch",
            "boot_partition_branch",
            "is_hdl_release",
            "is_linux_release",
            "is_boot_partition_release",
            "uboot_reached",
            "linux_prompt_reached",
            "drivers_enumerated",
            "drivers_missing",
            "dmesg_warnings_found",
            "dmesg_errors_found",
            "jenkins_job_date",
            "jenkins_build_number",
            "jenkins_project_name",
            "jenkins_agent",
            "jenkins_trigger",
            "source_adjacency_matrix",
            "pytest_errors",
            "pytest_failures",
            "pytest_skipped",
            "pytest_tests",
            "matlab_errors",
            "matlab_failures",
            "matlab_skipped",
            "matlab_tests",
            "last_failing_stage",
            "last_failing_stage_failure"
        ]

        if self.raw_boot_test_result:
            for f in fields:
                if f in self.raw_boot_test_result.keys():
                    v = self.raw_boot_test_result[f]
                    if f in ['hdl_hash', 'linux_hash', 'boot_partition_hash']:
                        v = v.split('(')[0].strip()
                    setattr(self, f, v)
                else:
                    if f in ["drivers_enumerated", 
                            "drivers_missing", 
                            "dmesg_warnings_found", 
                            "dmesg_errors_found",
                            "pytest_errors",
                            "pytest_failures",
                            "pytest_skipped",
                            "pytest_tests",
                            "matlab_errors",
                            "matlab_errors",
                            "matlab_failures",
                            "matlab_skipped",
                            "matlab_tests"]:
                        setattr(self, f, "0")
                    else:
                        setattr(self, f, "NA")
        else:
            for f in fields:
                setattr(self, f, None)

        self.boot_test_result, self.boot_test_failure = self.__is_pass()

    def __is_pass(self):
        # TODO: needs further detailed implementation
        # to represent correctly the actual status of the board
        if self.raw_boot_test_result:
            result = 'Pass'
            failure = []
            # if self.linux_prompt_reached and\
            #    self.dmesg_errors_found == '0' and\
            #    self.pytest_errors == '0' and\
            #    self.pytest_failures == '0':
            #     return 'Pass' 
            if not self.pytest_failures == '0':
                result = 'Fail'
                failure.append('pytest failure {}'.format(self.pytest_failures))
            if not self.pytest_errors == '0':
                result = 'Fail'
                failure.append('pytest errors {}'.format(self.pytest_errors))
            if not self.drivers_missing == '0':
                result = 'Fail'
                failure.append('linux drivers missing {}'.format(self.drivers_missing))
            if not self.dmesg_errors_found == '0':
                result = 'Fail'
                failure.append('linux dmesg errors {}'.format(self.dmesg_errors_found))
            if not self.linux_prompt_reached:
                result = 'Fail'
                failure = []
                failure.append('Linux prompt not reached')
            if not self.uboot_reached:
                result = 'Fail'
                failure = []
                failure.append('u-boot not reached')
            if not self.last_failing_stage_failure == 'NA':
                result = 'Fail'
                failure = []
                failure.append(self.last_failing_stage_failure)

            return result,failure

        return None,None

    def display(self):
        return self.__dict__

class BoardBootTests:
    def __init__(self, 
            sort="jenkins_job_date",
            order="desc",
            agg_field=None,
            boot_folder_name=None,
            jenkins_project_name=None,
            jenkins_build_number=None,
            source_adjacency_matrix=None,
            filters=None
        ):

        # if not boot_folder_name:
        #     raise ValueError('boot_folder_name must not be null or empty')
        
        self.db = DB()
        db_res = self.db.search(
            sort=sort,
            order=order,
            agg_field=agg_field,
            boot_folder_name=boot_folder_name,
            jenkins_project_name=jenkins_project_name,
            jenkins_build_number=jenkins_build_number,
            source_adjacency_matrix=source_adjacency_matrix
        )
        # create boards object from raw db_res
        self._boot_tests = [ BootTest(row) for row in db_res['hits'] ]

        if filters:
            for field, values in filters.items():
                filtered_boot_tests = []
                for _boot_test in self._boot_tests:
                    if getattr(_boot_test, field, '') in values:
                        filtered_boot_tests.append(_boot_test)
                self._boot_tests = filtered_boot_tests

    @property
    def boot_tests(self):
        return self._boot_tests
    
    def latest_builds(self, size):
        builds = {}
        element_count = 0
        for bt in self._boot_tests:
            if not bt.jenkins_build_number in builds:
                builds.update(
                    {   
                        bt.jenkins_build_number: {
                            "jenkins_job_date": bt.jenkins_job_date,
                            "jenkins_trigger": bt.jenkins_trigger
                        }
                    }
                )
                element_count += 1
                if element_count == size:
                    break
                
        return builds

    def latest_builds_boards(self, size):
        boards = []
        latest_builds  = self.latest_builds(size)
        for bt in self._boot_tests:
            if bt.jenkins_build_number in latest_builds:
                if not bt.boot_folder_name in boards:
                    boards.append(bt.boot_folder_name)
        return boards

    @property
    def boot_tests_dict(self):
        self._boot_tests_dict = []
        for bt in self._boot_tests:
            self._boot_tests_dict.append(bt.display())
        return self._boot_tests_dict

if __name__ == "__main__":
    bt = BoardBootTests(jenkins_project_name="HW_tests/HW_test_multiconfig")
    print(bt.latest_builds(size=7))
    