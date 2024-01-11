import os
import time

import telemetry

# TODO: transfer defaults to a config file
MODE = "elastic"
ELASTIC_SERVER = "elasticsearch" if "ES" not in os.environ else os.environ["ES"]
INDEX = "boot_tests"
USERNAME = ""
PASSWORD = ""
MAX_CONNECTION_RETRIES = 5
RETRY_WAIT = 30
KEYWORDS = [
    "boot_folder_name",
    "hdl_branch",
    "linux_branch",
    "boot_partition_branch",
    "jenkins_project_name",
    "jenkins_agent",
    "jenkins_trigger",
    "source_adjacency_matrix",
    "last_failing_stage",
]

class DB:
    def __init__(
        self,
        elastic_server=ELASTIC_SERVER,
        username=USERNAME,
        password=PASSWORD,
        index_name=INDEX,
        keywords=KEYWORDS
    ):
        retries = 0
        while True:
            try:
                self.db = telemetry.elastic(
                    server=elastic_server,
                    port=9200,
                    username=username,
                    password=password,
                    index_name=index_name,
                )
                self.keywords=keywords
                break
            except Exception as e:
                print("Server not yet ready")
                time.sleep(RETRY_WAIT)
                retries += 1
                if not retries < MAX_CONNECTION_RETRIES:
                    raise e

    def search(
        self,
        size=10000,
        sort="jenkins_job_date",
        order="desc",
        agg_field=None,
        **kwargs
    ):
        result = {"hits": [], "aggregates": [], "aggregates_top": []}
        if kwargs:
            fields = []
            for field in kwargs:
                if kwargs[field]:
                    val = kwargs[field]
                    field = f"{field}.keyword" if field in self.keywords else field
                    fields.append({"match": {field: val}})
            query = {"bool": {"must": fields}}
        else:
            query = {"match_all": {}}

        request_body = {"sort": [{sort: {"order": order}}], "query": query}

        if agg_field:
            request_body.update(
                {"aggs": {agg_field: {"terms": {"field": agg_field, "size": 100}}}}
            )

        res = self.db.es.search(index=self.db.index_name, size=size, body=request_body)
        for row in res["hits"]["hits"]:
            result["hits"].append(row["_source"])

        if agg_field:
            for row in res["aggregations"][agg_field]["buckets"]:
                result["aggregates"].append(row["key"])
                
                agg_field_data = {}
                # get top data for the aggregated field
                for row_data in result["hits"]:
                    agg_field = agg_field.split(".keyword")[0] if "keyword" in agg_field else agg_field
                    if row_data[agg_field] == row["key"]:
                        agg_field_data = row_data
                        break
                if agg_field_data:
                    result["aggregates_top"].append({row["key"]: agg_field_data})

        return result


if __name__ == "__main__":

    def test_db_boot_test():
        pass

    def test_db_artifacts():
        db = DB(index_name="artifacts")
        result = db.search(sort="archive_date")
        assert len(result) == 2

    def test_db_search():
        db = DB(
            elastic_server="primary.englab",
            username="",
            password="",
            index_name="boot_tests"
        )
        result = db.search(
            size=1,
            sort="jenkins_job_date",
            order="desc",
            agg_field="boot_folder_name.keyword",
        )