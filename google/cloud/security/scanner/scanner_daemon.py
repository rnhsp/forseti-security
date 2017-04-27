# Copyright 2017 Google Inc.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#    http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""POC for PubSub client."""

import base64
import datetime
import time
import sys

import daemon
import gflags as flags

from google.apputils import app
from google.cloud.security.common.gcp_api import pubsub
from google.cloud.security.scanner import scanner
from google.cloud.security.common.util import log_util

FLAGS = flags.FLAGS

flags.DEFINE_string('subscription', None, 'Inventory subscription.')
flags.DEFINE_integer('poll_interval', 10, 'PubSub poll interval in seconds.')

LOGGER = log_util.get_logger(__name__)

# TODO: make this configurable by flags?
MAX_SCAN_INTERVAL = datetime.timedelta(seconds=60*60)
MAX_MESSAGES = 10


def main(_):
    """Run the scanner daemon."""

    if not FLAGS.subscription:
        LOGGER.info('No PubSub subscription to listen to. Exiting.')
        sys.exit(0)

    client = pubsub.PubSubClient()
    subscription_service = client.service.projects().subscriptions()

    prev_snapshot_timestamp = None
    next_scan = _get_next_scan_time()

    with daemon.DaemonContext():
        while True:
            # TODO: determine whether to run the scanner based on:
            # 1. If current time exceeds the "next_scan"
            # 2. If the snapshot differs
            now = datetime.datetime.utcnow()

            LOGGER.info('now: %s', now)
            LOGGER.info('next scan: %s', next_scan)

            curr_snapshot_timestamp = check_subscription(
                subscription_service, FLAGS.subscription)

            LOGGER.info('current snapshot: %s', curr_snapshot_timestamp)
            if ((now > next_scan) or
                    (curr_snapshot_timestamp is not None and
                     curr_snapshot_timestamp != prev_snapshot_timestamp)):
                scanner.run(snapshot_timestamp=curr_snapshot_timestamp)
                next_scan = _get_next_scan_time()
            prev_snapshot_timestamp = curr_snapshot_timestamp

            time.sleep(FLAGS.poll_interval)

def _get_next_scan_time():
    """Get the next scan time.

    Returns:
        The scan time, which is now + MAX_SCAN_INTERVAL, at the top of the hour.
    """
    return datetime.datetime.utcnow().replace(
        minute=0, second=0, microsecond=0) + MAX_SCAN_INTERVAL

def check_subscription(subscription_service, subscription_name):
    """Check the PubSub subscription for new snapshot notifications.

    Args:
        subscription_service: The PubSub subscription service.
        subscription_name: The full name of the PubSub subscription.

    Returns:
        The snapshot timestamp read from the subscription message, if any.
    """

    # read from topic
    request = subscription_service.pull(
        subscription=subscription_name,
        body={'returnImmediately': True, 'maxMessages': MAX_MESSAGES})
    response = request.execute()
    LOGGER.info('subscription response %s', response)
    ack_ids = []
    msg_data = None

    if response:
        messages = response.get('receivedMessages')
        for message in messages:
            ack_ids.append(message.get('ackId'))
            msg_content = message.get('message')
            _ = msg_content.get('attributes')
            msg_data = base64.b64decode(msg_content.get('data'))
            LOGGER.info('msg data: %s', msg_data)

    if ack_ids:
        request = subscription_service.acknowledge(
            subscription=subscription_name,
            body={'ackIds': ack_ids})
        response = request.execute()

    return msg_data


if __name__ == '__main__':
    app.run()
