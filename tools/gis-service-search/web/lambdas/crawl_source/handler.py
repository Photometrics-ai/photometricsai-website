"""Step Functions Map task: crawl one ArcGIS source."""

import arcgis_crawler


def lambda_handler(event, context):
    return arcgis_crawler.crawl_and_classify(
        event["source"],
        event["query"],
        event["matchMode"],
        event["budgetSeconds"],
    )
