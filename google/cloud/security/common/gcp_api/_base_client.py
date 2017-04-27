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

"""Base GCP client which uses the discovery API."""

from apiclient import discovery
from oauth2client.client import GoogleCredentials
from retrying import retry
from googleapiclient import errors as googleapi_errors

from google.cloud.security.common.gcp_api import _supported_apis
from google.cloud.security.common.util import retryable_exceptions
from google.cloud.security.common.util import log_util

LOGGER = log_util.get_logger(__name__)


# pylint: disable=too-few-public-methods
class BaseClient(object):
    """Base client for a specified GCP API and credentials."""

    def __init__(self, credentials=None, api_name=None, **kwargs):
        """Thin client wrapper over the Google Discovery API.

        The intent for this class is to define the Google APIs expected by
        Forseti. While other APIs and versions can be specified, it may not
        be stable and could cause unknown issues in Forseti.

        Args:
            credentials: Google credentials for auth-ing to the API.
            api_name: The API name to wrap. More details here:
                https://developers.google.com/api-client-library/python/apis/
            kwargs: Additional args such as version.

        Raise:
            googleapiclient.errors.UnknownApiNameOrVersion if API or version
            is not known in the Google Discovery API.
        """
        if not credentials:
            credentials = GoogleCredentials.get_application_default()
        self._credentials = credentials

        self.name = api_name

        # Look to see if the API is formally supported in Forseti.
        supported_api = _supported_apis.SUPPORTED_APIS.get(api_name)
        if not supported_api:
            LOGGER.warn('API "%s" is not formally supported in Forseti, '
                        'proceed at your own risk.', api_name)

        # See if the version is supported by Forseti.
        # If no version is specified, try to find the supported API's version.
        version = kwargs.get('version')
        if not version and supported_api:
            version = supported_api.get('version')
        self.version = version

        if supported_api and supported_api.get('version') != version:
            LOGGER.warn('API "%s" version %s is not formally supported '
                        'in Forseti, proceed at your own risk.',
                        api_name, version)

        should_cache_discovery = kwargs.get('cache_discovery')

        self.service = discovery.build(self.name,
                                       self.version,
                                       credentials=self._credentials,
                                       cache_discovery=should_cache_discovery)

    def __repr__(self):
        return 'API: name={}, version={}'.format(self.name, self.version)

    # The wait time is (2^X * multiplier) milliseconds, where X is the retry
    # number.
    @retry(retry_on_exception=retryable_exceptions.is_retryable_exception,
           wait_exponential_multiplier=1000, wait_exponential_max=10000,
           stop_max_attempt_number=5)
    # pylint: disable=no-self-use
    def _execute(self, request):
        """Executes requests with exponential retry.

        Args:
            request: GCP API client request object.

        Returns:
            API response object.

        Raises:
            When the retry is exceeded, exception will be thrown.  This
            exception is not wrapped by the retry library, and should be handled
            upstream.
        """
        return request.execute()
