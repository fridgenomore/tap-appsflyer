#!/usr/bin/env python3

import csv
import datetime
import itertools
import os
import re
import sys

import attr
import backoff
import requests
import singer
import singer.stats
from singer import transform
from singer import utils


LOGGER = singer.get_logger()
SESSION = requests.Session()


CONFIG = {
    "app_id": None,
    "api_token": None
}


STATE = {}


ENDPOINTS = {
    "installs": "/export/{app_id}/installs_report/v5",
    "organic_installs": "/export/{app_id}/organic_installs_report/v5",
    "in_app_events": "/export/{app_id}/in_app_events_report/v5",
    "postbacks_installs": "/export/{app_id}/postbacks/v5",
    "postbacks_in_app_events": "/export/{app_id}/in-app-events-postbacks/v5"
}

# This order matters
RAW_DATA_FIELDS_DEFAULT = (
    "attributed_touch_type",
    "attributed_touch_time",
    "install_time",
    "event_time",
    "event_name",
    "event_value",
    "event_revenue",
    "event_revenue_currency",
    "event_revenue_usd",
    "event_source",
    "is_receipt_validated",
    "af_prt",
    "media_source",
    "af_channel",
    "af_keywords",
    "campaign",
    "af_c_id",
    "af_adset",
    "af_adset_id",
    "af_ad",
    "af_ad_id",
    "af_ad_type",
    "af_siteid",
    "af_sub_siteid",
    "af_sub1",
    "af_sub2",
    "af_sub3",
    "af_sub4",
    "af_sub5",
    "af_cost_model",
    "af_cost_value",
    "af_cost_currency",
    "contributor1_af_prt",
    "contributor1_media_source",
    "contributor1_campaign",
    "contributor1_touch_type",
    "contributor1_touch_time",
    "contributor2_af_prt",
    "contributor2_media_source",
    "contributor2_campaign",
    "contributor2_touch_type",
    "contributor2_touch_time",
    "contributor3_af_prt",
    "contributor3_media_source",
    "contributor3_campaign",
    "contributor3_touch_type",
    "contributor3_touch_time",
    "region",
    "country_code",
    "state",
    "city",
    "postal_code",
    "dma",
    "ip",
    "wifi",
    "operator",
    "carrier",
    "language",
    "appsflyer_id",
    "advertising_id",
    "idfa",
    "android_id",
    "customer_user_id",
    "imei",
    "idfv",
    "platform",
    "device_type",
    "os_version",
    "app_version",
    "sdk_version",
    "app_id",
    "app_name",
    "bundle_id",
    "is_retargeting",
    "retargeting_conversion_type",
    "af_attribution_lookback",
    "af_reengagement_window",
    "is_primary_attribution",
    "user_agent",
    "http_referrer",
    "original_url",
)


POSTBACKS_DATA_FIELDS_DEFAULT = (
    "attributed_touch_type",
    "attributed_touch_time",
    "install_time",
    "event_time",
    "event_name",
    "event_value",
    "event_revenue",
    "event_revenue_currency",
    "event_revenue_usd",
    "event_source",
    "is_receipt_validated",
    "af_prt",
    "media_source",
    "af_channel",
    "af_keywords",
    "campaign",
    "af_c_id",
    "af_adset",
    "af_adset_id",
    "af_ad",
    "af_ad_id",
    "af_ad_type",
    "af_siteid",
    "af_sub_siteid",
    "af_sub1",
    "af_sub2",
    "af_sub3",
    "af_sub4",
    "af_sub5",
    "af_cost_model",
    "af_cost_value",
    "af_cost_currency",
    "contributor1_af_prt",
    "contributor1_media_source",
    "contributor1_campaign",
    "contributor1_touch_type",
    "contributor1_touch_time",
    "contributor2_af_prt",
    "contributor2_media_source",
    "contributor2_campaign",
    "contributor2_touch_type",
    "contributor2_touch_time",
    "contributor3_af_prt",
    "contributor3_media_source",
    "contributor3_campaign",
    "contributor3_touch_type",
    "contributor3_touch_time",
    "region",
    "country_code",
    "state",
    "city",
    "postal_code",
    "dma",
    "ip",
    "wifi",
    "operator",
    "carrier",
    "language",
    "appsflyer_id",
    "advertising_id",
    "idfa",
    "android_id",
    "customer_user_id",
    "imei",
    "idfv",
    "platform",
    "device_type",
    "os_version",
    "app_version",
    "sdk_version",
    "app_id",
    "app_name",
    "bundle_id",
    "is_retargeting",
    "retargeting_conversion_type",
    "af_attribution_lookback",
    "af_reengagement_window",
    "is_primary_attribution",
    "user_agent",
    "http_referrer",
    "original_url",
    "postback_url",
    "postback_method",
    "postback_http_response_code",
    "postback_error_message"
)

POSTBACKS_EXTRA_FIELDS_SCHEMA = {
    "ad_unit": {
      "type": ["null", "string"]
    },
    "impressions": {
      "type": ["null", "string"]
    },
    "mediation_network": {
      "type": ["null", "string"]
    },
    "monetization_network": {
      "type": ["null", "string"]
    },
    "placement": {
      "type": ["null", "string"]
    },
    "segment": {
      "type": ["null", "string"]
    },
    "blocked_reason": {
      "type": ["null", "string"]
    },
    "blocked_reason_rule": {
      "type": ["null", "string"]
    },
    "blocked_reason_value": {
      "type": ["null", "string"]
    },
    "blocked_sub_reason": {
      "type": ["null", "string"]
    },
    "contributor1_match_type": {
      "type": ["null", "string"]
    },
    "contributor2_match_type": {
      "type": ["null", "string"]
    },
    "contributor3_match_type": {
      "type": ["null", "string"]
    },
    "keyword_match_type": {
      "type": ["null", "string"]
    },
    "match_type": {
      "type": ["null", "string"]
    },
    "rejected_reason": {
      "type": ["null", "string"]
    },
    "rejected_reason_value": {
      "type": ["null", "string"]
    },
    "store_product_page": {
      "type": ["null", "string"]
    },
    "gp_broadcast_referrer": {
      "type": ["null", "string"]
    },
    "gp_referrer": {
      "type": ["null", "string"]
    },
    "keyword_id": {
      "type": ["null", "string"]
    },
    "network_account_id": {
      "type": ["null", "string"]
    },
    "attributed_touch_hour": {
      "type": ["null", "string"]
    },
    "event_hour": {
      "type": ["null", "string"]
    },
    "install_hour": {
      "type": ["null", "string"]
    },
    "amazon_aid": {
      "type": ["null", "string"]
    },
    "att": {
      "type": ["null", "string"]
    },
    "custom_data": {
      "type": ["null", "string"]
    },
    "deeplink_url": {
      "type": ["null", "string"]
    },
    "device_category": {
      "type": ["null", "string"]
    },
    "postback_retry": {
      "type": ["null", "string"]
    },
    "install_app_store": {
      "type": ["null", "string"]
    },
    "device_model": {
      "type": ["null", "string"]
    },
    "oaid": {
      "type": ["null", "string"]
    },
    "is_lat": {
      "type": ["null", "boolean"]
    },
    "store_reinstall": {
      "type": ["null", "boolean"]
    },
    "gp_click_time": {
      "type": ["null", "string"],
      "format": "date-time"
    },
    "gp_install_begin": {
      "type": ["null", "string"],
      "format": "date-time"
    },
    "device_download_time": {
      "type": ["null", "string"],
      "format": "date-time"
    }
}


def contains_duplicate(fields: list) -> bool:
    if len(fields) == len(set(fields)):
        return False
    return True


def clean_config(config: dict) -> dict:
    """Strips whitespace from any values in the config."""
    for key in config.keys():
        value = config[key]
        if isinstance(value, str):
            config[key] = value.strip()
        if key == "postbacks_additional_fields" and value is not None:
            fields = list(map(lambda f: f.strip(), value.split(",")))
            if contains_duplicate(fields):
                LOGGER.error("Configuration parameter [%s] contains duplicate elements.", key)
                sys.exit(1)
            for field in fields:
                if POSTBACKS_EXTRA_FIELDS_SCHEMA.get(field) is None:
                    LOGGER.error("Configuration parameter [%s] contains wrong value. "
                                 "The field [%s] is missing in the schema definition for additional fields.", key, field)
                    sys.exit(1)
            config[key] = ','.join(fields)
    return config


def af_datetime_str_to_datetime(s):
    return datetime.datetime.strptime(s.strip(), "%Y-%m-%d %H:%M:%S")


def get_restricted_start_date(date: str) -> datetime.datetime:
    # https://support.appsflyer.com/hc/en-us/articles/207034366-API-Policy
    restriction_date = datetime.datetime.now() - datetime.timedelta(days=90)
    start_date = utils.strptime(date)

    return max(start_date, restriction_date)


def get_start(key):
    if key in STATE:
        return  get_restricted_start_date(STATE[key])

    if "start_date" in CONFIG:
        return  get_restricted_start_date(CONFIG["start_date"])

    return datetime.datetime.now() - datetime.timedelta(days=30)


def get_stop(start_datetime, stop_time, days=30):
    return min(start_datetime + datetime.timedelta(days=days), stop_time)


def get_base_url():
    if "base_url" in CONFIG:
        return CONFIG["base_url"]
    else:
        return "https://hq.appsflyer.com"


def get_url(endpoint, **kwargs):
    if endpoint not in ENDPOINTS:
        raise ValueError("Invalid endpoint {}".format(endpoint))
    else:
        return get_base_url() + ENDPOINTS[endpoint].format(**kwargs)


def xform_datetime_field(record, field_name):
    record[field_name] = af_datetime_str_to_datetime(record[field_name]).isoformat()


def xform_boolean_field(record, field_name):
    value = record[field_name]
    if value is None:
        return

    if value.lower() == "TRUE".lower():
        record[field_name] = True
    else:
        record[field_name] = False


def xform_empty_strings_to_none(record):
    for key, value in record.items():
        if value == "":
            record[key] = None


def xform(record, schema):
    xform_empty_strings_to_none(record)
    xform_boolean_field(record, "wifi")
    xform_boolean_field(record, "is_retargeting")
    xform_boolean_field(record, "is_receipt_validated")
    xform_boolean_field(record, "is_primary_attribution")

    optional_fields = ["store_reinstall", "is_lat"]
    for field in optional_fields:
        if field in record:
            xform_boolean_field(record, field)

    return transform.transform(record, schema)


@attr.s
class Stream(object):
    name = attr.ib()
    sync = attr.ib()


def get_abs_path(path):
    return os.path.join(os.path.dirname(os.path.realpath(__file__)), path)


def load_schema(entity_name):
    schema = utils.load_json(get_abs_path('schemas/{}.json'.format(entity_name)))
    return schema


def giveup(exc):
    return exc.response is not None and 400 <= exc.response.status_code < 500


def parse_source_from_url(url):
    url_regex = re.compile(get_base_url() + r'.*/(\w+)_report/v5')
    match = url_regex.match(url)
    if match:
        return match.group(1)
    return None


@backoff.on_exception(backoff.expo,
                      (requests.exceptions.RequestException),
                      max_tries=5,
                      giveup=giveup,
                      factor=2)
@utils.ratelimit(10, 1)
def request(url, params=None):

    params = params or {}
    headers = {}

    if "user_agent" in CONFIG:
        headers["User-Agent"] = CONFIG["user_agent"]

    req = requests.Request("GET", url, params=params, headers=headers).prepare()
    LOGGER.info("GET %s", req.url)

    with singer.stats.Timer(source=parse_source_from_url(url)) as stats:
        resp = SESSION.send(req)
        stats.http_status_code = resp.status_code

    if resp.status_code >= 400:
        LOGGER.error("GET %s [%s - %s]", req.url, resp.status_code, resp.content)
        sys.exit(1)

    return resp


class RequestToCsvAdapter:
    def __init__(self, request_data):
        self.request_data_iter = request_data.iter_lines();

    def __iter__(self):
        return self

    def __next__(self):
        return next(self.request_data_iter).decode("utf-8")


def sync_installs():

    schema = load_schema("raw_data/installations")
    singer.write_schema("installs", schema, [
        "event_time",
        "event_name",
        "appsflyer_id"
    ])

    # This order matters
    fieldnames = RAW_DATA_FIELDS_DEFAULT

    from_datetime = get_start("installs")
    to_datetime = get_stop(from_datetime, datetime.datetime.now())

    if to_datetime < from_datetime:
        LOGGER.error("to_datetime (%s) is less than from_endtime (%s).", to_datetime, from_datetime)
        return

    params = dict()
    params["from"] = from_datetime.strftime("%Y-%m-%d %H:%M")
    params["to"] = to_datetime.strftime("%Y-%m-%d %H:%M")
    params["api_token"] = CONFIG["api_token"]

    url = get_url("installs", app_id=CONFIG["app_id"])
    request_data = request(url, params)

    csv_data = RequestToCsvAdapter(request_data)
    reader = csv.DictReader(csv_data, fieldnames)

    next(reader) # Skip the heading row

    bookmark = from_datetime
    for i, row in enumerate(reader):
        record = xform(row, schema)
        singer.write_record("installs", record)
        # AppsFlyer returns records in order of most recent first.
        try:
            if utils.strptime(record["attributed_touch_time"]) > bookmark:
                bookmark = utils.strptime(record["attributed_touch_time"])
        except:
            LOGGER.error("failed to get attributed_touch_time")

    # Write out state
    utils.update_state(STATE, "installs", bookmark)
    singer.write_state(STATE)

def sync_organic_installs():
    
    schema = load_schema("raw_data/organic_installs")
    singer.write_schema("organic_installs", schema, [
        "event_time",
        "event_name",
        "appsflyer_id"
    ])

    # This order matters
    fieldnames = RAW_DATA_FIELDS_DEFAULT

    from_datetime = get_start("organic_installs")
    to_datetime = get_stop(from_datetime, datetime.datetime.now())

    if to_datetime < from_datetime:
        LOGGER.error("to_datetime (%s) is less than from_endtime (%s).", to_datetime, from_datetime)
        return

    params = dict()
    params["from"] = from_datetime.strftime("%Y-%m-%d %H:%M")
    params["to"] = to_datetime.strftime("%Y-%m-%d %H:%M")
    params["api_token"] = CONFIG["api_token"]

    url = get_url("organic_installs", app_id=CONFIG["app_id"])
    request_data = request(url, params)

    csv_data = RequestToCsvAdapter(request_data)
    reader = csv.DictReader(csv_data, fieldnames)

    next(reader) # Skip the heading row

    bookmark = from_datetime
    for i, row in enumerate(reader):
        record = xform(row, schema)
        singer.write_record("organic_installs", record)
        # AppsFlyer returns records in order of most recent first.
        if utils.strptime(record["event_time"]) > bookmark:
            bookmark = utils.strptime(record["event_time"])

    # Write out state
    utils.update_state(STATE, "organic_installs", bookmark)
    singer.write_state(STATE)


def sync_in_app_events():

    schema = load_schema("raw_data/in_app_events")
    singer.write_schema("in_app_events", schema, [
        "event_time",
        "event_name",
        "appsflyer_id"
    ])

    # This order matters
    fieldnames = RAW_DATA_FIELDS_DEFAULT

    stop_time = datetime.datetime.now()
    from_datetime = get_start("in_app_events")
    to_datetime = get_stop(from_datetime, stop_time, 10)

    while from_datetime < stop_time:
        LOGGER.info("Syncing data from %s to %s", from_datetime, to_datetime)
        params = dict()
        params["from"] = from_datetime.strftime("%Y-%m-%d %H:%M")
        params["to"] = to_datetime.strftime("%Y-%m-%d %H:%M")
        params["api_token"] = CONFIG["api_token"]

        url = get_url("in_app_events", app_id=CONFIG["app_id"])
        request_data = request(url, params)

        csv_data = RequestToCsvAdapter(request_data)
        reader = csv.DictReader(csv_data, fieldnames)

        next(reader) # Skip the heading row

        bookmark = from_datetime
        for i, row in enumerate(reader):
            record = xform(row, schema)
            singer.write_record("in_app_events", record)
            # AppsFlyer returns records in order of most recent first.
            if utils.strptime(record["event_time"]) > bookmark:
                bookmark = utils.strptime(record["event_time"])

        # Write out state
        utils.update_state(STATE, "in_app_events", bookmark)
        singer.write_state(STATE)

        # Move the timings forward
        from_datetime = to_datetime
        to_datetime = get_stop(from_datetime, stop_time, 10)


def sync_postbacks_installs():
    schema = load_schema("raw_data/postbacks_installs")

    # This order matters
    fieldnames = POSTBACKS_DATA_FIELDS_DEFAULT

    from_datetime = get_start("postbacks_installs")
    to_datetime = get_stop(from_datetime, datetime.datetime.now())

    if to_datetime < from_datetime:
        LOGGER.error("to_datetime (%s) is less than from_endtime (%s).", to_datetime, from_datetime)
        return

    params = dict()
    params["from"] = from_datetime.strftime("%Y-%m-%d %H:%M")
    params["to"] = to_datetime.strftime("%Y-%m-%d %H:%M")
    params["api_token"] = CONFIG["api_token"]

    if "postbacks_additional_fields" in CONFIG:
        if CONFIG["postbacks_additional_fields"]:
            extra_fields = CONFIG["postbacks_additional_fields"]
            params["additional_fields"] = extra_fields
            fields_list = extra_fields.split(",")
            fieldnames = fieldnames + tuple(fields_list)
            schema_extension = {key: POSTBACKS_EXTRA_FIELDS_SCHEMA[key] for key in fields_list}
            schema['properties'].update(schema_extension)

    url = get_url("postbacks_installs", app_id=CONFIG["app_id"])
    request_data = request(url, params)

    csv_data = RequestToCsvAdapter(request_data)
    reader = csv.DictReader(csv_data, fieldnames)

    next(reader)  # Skip the heading row

    singer.write_schema("postbacks_installs", schema, [
        "event_time",
        "event_name",
        "appsflyer_id"
    ])

    bookmark = from_datetime
    for i, row in enumerate(reader):
        record = xform(row, schema)
        singer.write_record("postbacks_installs", record)
        # AppsFlyer returns records in order of most recent first.
        if utils.strptime(record["event_time"]) > bookmark:
            bookmark = utils.strptime(record["event_time"])

    # Write out state
    utils.update_state(STATE, "postbacks_installs", bookmark)
    singer.write_state(STATE)


def sync_postbacks_in_app_events():
    schema = load_schema("raw_data/postbacks_in_app_events")

    # This order matters
    fieldnames = POSTBACKS_DATA_FIELDS_DEFAULT

    from_datetime = get_start("postbacks_in_app_events")
    to_datetime = get_stop(from_datetime, datetime.datetime.now())

    if to_datetime < from_datetime:
        LOGGER.error("to_datetime (%s) is less than from_endtime (%s).", to_datetime, from_datetime)
        return

    params = dict()
    params["from"] = from_datetime.strftime("%Y-%m-%d %H:%M")
    params["to"] = to_datetime.strftime("%Y-%m-%d %H:%M")
    params["api_token"] = CONFIG["api_token"]

    if "postbacks_additional_fields" in CONFIG:
        if CONFIG["postbacks_additional_fields"]:
            extra_fields = CONFIG["postbacks_additional_fields"]
            params["additional_fields"] = extra_fields
            fields_list = extra_fields.split(",")
            fieldnames = fieldnames + tuple(fields_list)
            schema_extension = {key: POSTBACKS_EXTRA_FIELDS_SCHEMA[key] for key in fields_list}
            schema['properties'].update(schema_extension)

    url = get_url("postbacks_in_app_events", app_id=CONFIG["app_id"])
    request_data = request(url, params)

    csv_data = RequestToCsvAdapter(request_data)
    reader = csv.DictReader(csv_data, fieldnames)

    next(reader)  # Skip the heading row

    singer.write_schema("postbacks_in_app_events", schema, [
        "event_time",
        "event_name",
        "appsflyer_id"
    ])

    bookmark = from_datetime
    for i, row in enumerate(reader):
        record = xform(row, schema)
        singer.write_record("postbacks_in_app_events", record)
        # AppsFlyer returns records in order of most recent first.
        if utils.strptime(record["event_time"]) > bookmark:
            bookmark = utils.strptime(record["event_time"])

    # Write out state
    utils.update_state(STATE, "postbacks_in_app_events", bookmark)
    singer.write_state(STATE)

STREAMS = [
    Stream("installs", sync_installs),
    Stream("in_app_events", sync_in_app_events)
]


def get_streams_to_sync(streams, state):
    target_stream = state.get("this_stream")
    result = streams
    if "organic_installs" in CONFIG:
        if CONFIG["organic_installs"]:
            result.append(Stream("organic_installs", sync_organic_installs))
    if "postbacks_installs" in CONFIG:
        if CONFIG["postbacks_installs"]:
            result.append(Stream("postbacks_installs", sync_postbacks_installs))
    if "postbacks_in_app_events" in CONFIG:
        if CONFIG["postbacks_in_app_events"]:
            result.append(Stream("postbacks_in_app_events", sync_postbacks_in_app_events))
    if target_stream:
        result = list(itertools.dropwhile(lambda x: x.name != target_stream, streams))
    if not result:
        raise Exception('Unknown stream {} in state'.format(target_stream))
    return result


def do_sync():
    LOGGER.info("do_sync()")
    streams = get_streams_to_sync(STREAMS, STATE)
    LOGGER.info('Starting sync. Will sync these streams: %s', [stream.name for stream in streams])
    for stream in streams:
        LOGGER.info('Syncing %s', stream.name)
        STATE["this_stream"] = stream.name
        stream.sync() # pylint: disable=not-callable
    STATE["this_stream"] = None
    singer.write_state(STATE)
    LOGGER.info("Sync completed")


def main():
    args = utils.parse_args(
        [
            "app_id",
            "api_token"
        ])

    config = clean_config(args.config)
    CONFIG.update(config)

    if args.state:
        STATE.update(args.state)

    do_sync()


if __name__ == '__main__':
    main()
