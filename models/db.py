import telemetry

#TODO: transfer defaults to a config file
MODE = "elastic"
ELASTIC_SERVER="192.168.10.1"
INDEX='boot_tests'
USERNAME=''
PASSWORD=''

class DB:  
    def __init__(
        self, 
        elastic_server=ELASTIC_SERVER,
        username=USERNAME,
        password=PASSWORD,
        index_name=INDEX
    ):
        self.db = telemetry.elastic(
            server=elastic_server,
            username=username,
            password=password,
            index_name=index_name
        )

    def search(self, size=10000, order="desc", agg_field=None, **kwargs):
        result = {
            "hits": [],
            "aggregates": []
        }
        if kwargs:
            fields = []
            for field in kwargs:
                if kwargs[field]:
                    fields.append({"match": {field: kwargs[field]}})
            query = {
                "bool": {
                    "must": fields
                }
            }
        else:
            query = {
                "match_all": {}
            }

        request_body = {
            "sort": [{"jenkins_job_date": {"order": order}}],
            "query": query
        }

        if agg_field:
            request_body.update({
                "aggs": {
                    agg_field: {
                        "terms": {
                            "field": agg_field,
                            "size": 100
                        }
                    }
                }
            })

        res = self.db.es.search(index=self.db.index_name, size=size, body=request_body)
        for row in res['hits']['hits']:
            result['hits'].append(row['_source'])

        if agg_field:
            for row in res['aggregations'][agg_field]["buckets"]:
                result['aggregates'].append(row['key'])

        return result