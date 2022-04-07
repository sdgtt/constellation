import os
import telemetry
import time

# TODO: transfer defaults to a config file
MODE = "elastic"
ELASTIC_SERVER = "elasticsearch" if "ES" not in os.environ else os.environ["ES"]
INDEX = "boot_tests"
USERNAME = ""
PASSWORD = ""
MAX_CONNECTION_RETRIES=5
RETRY_WAIT=30


class DB:
    def __init__(
        self,
        elastic_server=ELASTIC_SERVER,
        username=USERNAME,
        password=PASSWORD,
        index_name=INDEX,
    ):
        retries=0
        while(True):
            try:
                self.db = telemetry.elastic(
                    server=elastic_server,
                    username=username,
                    password=password,
                    index_name=index_name,
                )
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
        result = {"hits": [], "aggregates": []}
        if kwargs:
            fields = []
            for field in kwargs:
                if kwargs[field]:
                    fields.append({"match": {field: kwargs[field]}})
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

        return result


if __name__ == "__main__":

    def test_db_boot_test():
        pass

    def test_db_artifacts():
        db = DB(index_name="artifacts")
        result = db.search(sort="archive_date")
        assert len(result) == 2
