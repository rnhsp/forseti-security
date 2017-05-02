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

"""Wrapper for IAM API client."""

from google.cloud.security.common.gcp_api import _base_client
from google.cloud.security.common.util import log_util

LOGGER = log_util.get_logger(__name__)


class IamClient(_base_client.BaseClient):
    """IAM Client."""

    API_NAME = 'iam'

    def __init__(self, credentials=None):
        super(IamClient, self).__init__(
            credentials=credentials, api_name=self.API_NAME)

    def list_service_accounts(self, project_id):
        """List service accounts for a particular project.

        Args:
            project_id: The project id.

        Yields:
            An iterator of
                {'project': project_id,
                 'service_accounts': API response}
        """

        project_name = 'projects/%s' % project_id
        svc_acct_api = self.service.projects().serviceAccounts()
        request = svc_acct_api.list(name=project_name)

        # TODO: does IAM API have a quota? I can't find it.
        while request is not None:
            response = self._execute(request)
            yield {'project': project_id, 'service_accounts': response}
            request = svc_acct_api.list_next(
                previous_request=request,
                previous_response=response)

    def list_service_account_keys(self, project_id, service_account_email):
        """List the service account keys for a project's service account.

        The resulting service account keys will not contain any private key
        data as per documentation.
        https://cloud.google.com/iam/reference/rest/v1/projects.serviceAccounts.keys#ServiceAccountKey

        Args:
            project_id: The project id.
            service_account_email: The service account email.

        Yield:
            Iterator of
                {'project': project_id,
                 'service_account': service_acount_email,
                 'keys': API response}.
        """

        svc_acct_keys_api = self.service.projects().serviceAccounts().keys()
        svc_acct_name = (
            'projects/%s/serviceAccounts/%s' %
            (project_id, service_account_email))
        request = svc_acct_keys_api.list(name=svc_acct_name)

        while request is not None:
            response = self._execute(request)
            yield {
                'project': project_id,
                'service_account': service_account_email,
                'keys': response
            }
            request = svc_acct_keys_api.list_next(
                previous_request=request,
                previous_response=response)
