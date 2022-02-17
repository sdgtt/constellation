from models.db import DB

class Artifact:
    '''Class representing a test job artifact'''

    def __init__(self, raw_artifact_result=None):
            self.raw_artifact_result = raw_artifact_result
            self.__initialize_fields()

    def __initialize_fields(self):

        fields = [
            "archive_date",
            "url",
            "server",
            "job",
            "job_no",
            "job_date",
            "job_build_parameters",
            "file_name",
            "target_board",
            "artifact_info_type",
            "payload_raw",
            "payload_ts",
            "payload"
        ]

        if self.raw_artifact_result:
            for f in fields:
                if f in self.raw_artifact_result.keys():
                    v = self.raw_artifact_result[f]
                    setattr(self, f, v)

    def display(self):
        return self.__dict__

class Artifacts:
    def __init__(self, **filters):

        self.db = DB(index_name="artifacts")
        db_res = self.db.search(
            sort="archive_date",
            **filters
        )
        # create boards object from raw db_res
        self._artifacts = [ Artifact(row) for row in db_res['hits'] ]

    @property
    def artifacts(self):
        return self._artifacts

    @property
    def artifacts_dict(self):
        self._artifacts_dict = []
        for ar in self._artifacts:
            self._artifacts_dict.append(ar.display())
        return self._artifacts_dict

if __name__ == "__main__":

    def test_model_artifacts():
        fields = [
            "archive_date",
            "url",
            "server",
            "job",
            "job_no",
            "job_date",
            "job_build_parameters",
            "file_name",
            "target_board",
            "artifact_info_type",
            "payload_raw",
            "payload_ts",
            "payload"
        ]

        ar = Artifacts(
                job_no="714",
                artifact_info_type="enumerated_devs",
                target_board="zynq-zed-adv7511-adrv9002-vcmos"
        )
        assert len(ar.artifacts) > 1
        for f in fields:
            assert hasattr(ar.artifacts[0], f)
            print("{} is present with value {}".\
            format(f,getattr(ar.artifacts[0],f)))
        
    test_model_artifacts()