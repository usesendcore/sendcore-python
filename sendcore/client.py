import json
import time
import hmac
import hashlib
from typing import Any, Optional
from urllib.request import Request, urlopen
from urllib.error import HTTPError
from urllib.parse import urlencode

from .types import (
    SendCoreConfig, SendEmailParams, SendEmailResponse,
    SubscribeParams,
    Domain, DnsRecord,
    VerifyEmailParams, VerifyBatchParams, VerificationResult,
    AnalyticsParams, AnalyticsData,
    WebhookPayload,
    Broadcast, CreateBroadcastParams, ScheduleBroadcastParams,
    AudienceList, CreateAudienceListParams, AddContactParams,
    EmailTemplate, CreateTemplateParams,
    Suppression, AddSuppressionParams,
    ApiKey, CreateApiKeyParams, CreateApiKeyResponse,
    AgentInbox, CreateAgentInboxParams, InboundEmail, SendAsAgentParams, PaginatedEmails,
)
from .errors import SendCoreError

DEFAULT_BASE_URL = 'https://api.usesendcore.com'
API_PREFIX = '/api/v1'
DEFAULT_TIMEOUT = 30
DEFAULT_RETRIES = 2
RETRYABLE_STATUS_CODES = {408, 429, 500, 502, 503, 504}


class SendCore:
    def __init__(
        self, api_key_or_config: str | SendCoreConfig | dict[str, Any]
    ) -> None:
        if isinstance(api_key_or_config, str):
            config = SendCoreConfig(apiKey=api_key_or_config)
        elif isinstance(api_key_or_config, dict):
            config = SendCoreConfig(**api_key_or_config)
        else:
            config = api_key_or_config

        if not config.apiKey:
            raise SendCoreError(401, {
                'message': 'SendCore: An API key is required. Get one at https://usesendcore.com/dashboard/api-keys',
            })

        self._api_key = config.apiKey
        self._base_url = (config.baseUrl or DEFAULT_BASE_URL).rstrip('/')
        self._timeout = config.timeout or DEFAULT_TIMEOUT
        self._retries = config.retries or DEFAULT_RETRIES

        self.emails = EmailsResource(self)
        self.domains = DomainsResource(self)
        self.contacts = ContactsResource(self)
        self.broadcasts = BroadcastsResource(self)
        self.audience_lists = AudienceListsResource(self)
        self.templates = TemplatesResource(self)
        self.suppressions = SuppressionsResource(self)
        self.api_keys = ApiKeysResource(self)
        self.verify = EmailVerificationResource(self)
        self.analytics = AnalyticsResource(self)
        self.webhooks = WebhooksResource()
        self.workflows = WorkflowsResource(self)
        self.agent_inboxes = AgentInboxesResource(self)

    def _request(
        self,
        method: str,
        path: str,
        body: Optional[dict[str, Any]] = None,
        params: Optional[dict[str, Any]] = None,
    ) -> Any:
        url = f'{self._base_url}{API_PREFIX}{path}'
        if params:
            qs = urlencode(
                {k: v for k, v in params.items() if v is not None}
            )
            if qs:
                url = f'{url}?{qs}'

        headers: dict[str, str] = {
            'x-api-key': self._api_key,
            'Content-Type': 'application/json',
            'User-Agent': 'sendcore-python/1.0.0',
        }

        data_bytes: Optional[bytes] = None
        if body is not None:
            data_bytes = json.dumps(body, default=_default_json).encode('utf-8')

        last_error: Optional[Exception] = None

        for attempt in range(self._retries + 1):
            try:
                req = Request(url, data=data_bytes, headers=headers, method=method)
                resp = urlopen(req, timeout=self._timeout)
                resp_body = json.loads(resp.read().decode('utf-8'))
                return resp_body
            except HTTPError as e:
                try:
                    resp_body = json.loads(e.read().decode('utf-8'))
                except Exception:
                    resp_body = {}

                status = e.code
                if status not in RETRYABLE_STATUS_CODES:
                    raise SendCoreError(status, {
                        'statusCode': status,
                        'message': resp_body.get('message', str(e.reason)),
                        'error': resp_body.get('error'),
                        **resp_body,
                    })

                last_error = SendCoreError(status, {
                    'statusCode': status,
                    'message': resp_body.get('message', str(e.reason)),
                    'error': resp_body.get('error'),
                    **resp_body,
                })
            except Exception as e:
                last_error = e

            if attempt < self._retries:
                delay = min(1.0 * (2 ** attempt), 10.0)
                time.sleep(delay)

        raise last_error or SendCoreError(0, {
            'message': 'SendCore: Request failed after all retries',
        })


class EmailsResource:
    def __init__(self, client: SendCore) -> None:
        self._client = client

    def send(self, params: SendEmailParams | dict[str, Any]) -> SendEmailResponse:
        if isinstance(params, SendEmailParams):
            payload = params.to_dict()
        else:
            payload = dict(params)

        if 'from' not in payload:
            raise SendCoreError(400, {'message': "SendCore: 'from' is required"})
        if 'to' not in payload:
            raise SendCoreError(400, {'message': "SendCore: 'to' is required"})

        to = payload['to']
        if isinstance(to, str):
            payload['to'] = [to]
        for key in ('cc', 'bcc', 'replyTo'):
            val = payload.get(key)
            if isinstance(val, str):
                payload[key] = [val]

        result = self._client._request('POST', '/emails/send', payload)
        return SendEmailResponse(**result)

    def logs(self, page: Optional[int] = None, limit: Optional[int] = None) -> Any:
        params: dict[str, Any] = {}
        if page is not None:
            params['page'] = page
        if limit is not None:
            params['limit'] = limit
        return self._client._request('GET', '/emails/logs', params=params or None)

    def get_log(self, id: str) -> Any:
        return self._client._request('GET', f'/emails/logs/{id}')

    def stats(self) -> Any:
        return self._client._request('GET', '/emails/stats')

    def analytics(self, days: Optional[int] = None) -> Any:
        params = {'days': days} if days is not None else None
        return self._client._request('GET', '/emails/analytics', params=params)


class DomainsResource:
    def __init__(self, client: SendCore) -> None:
        self._client = client

    def list(self) -> list[Domain]:
        result = self._client._request('GET', '/domains')
        return [Domain(**d) for d in result]

    def add(self, params: dict[str, Any]) -> Domain:
        result = self._client._request('POST', '/domains', params)
        return Domain(**result)

    def remove(self, id: str) -> None:
        self._client._request('DELETE', f'/domains/{id}')

    def verify(self, id: str) -> Domain:
        result = self._client._request('POST', f'/domains/{id}/verify')
        return Domain(**result)

    def get_dns_records(self, id: str) -> list[DnsRecord]:
        result = self._client._request('GET', f'/domains/{id}/dns')
        return [DnsRecord(**r) for r in result]

    def health(self, id: str) -> dict[str, Any]:
        return self._client._request('GET', f'/domains/{id}/health')


class ContactsResource:
    def __init__(self, client: SendCore) -> None:
        self._client = client

    def subscribe(self, params: SubscribeParams | dict[str, Any]) -> Any:
        if isinstance(params, SubscribeParams):
            payload = params.__dict__
        else:
            payload = dict(params)
        if 'email' not in payload:
            raise SendCoreError(400, {'message': "SendCore: 'email' is required"})
        return self._client._request('POST', '/organizations/audience/subscribe', payload)

    def unsubscribe(self, params: dict[str, Any]) -> Any:
        if 'email' not in params:
            raise SendCoreError(400, {'message': "SendCore: 'email' is required"})
        return self._client._request('POST', '/organizations/audience/unsubscribe', params)


class BroadcastsResource:
    def __init__(self, client: SendCore) -> None:
        self._client = client

    def list(self) -> list[Broadcast]:
        result = self._client._request('GET', '/organizations/broadcasts')
        return [Broadcast(**b) for b in result]

    def get(self, id: str) -> Broadcast:
        result = self._client._request('GET', f'/organizations/broadcasts/{id}')
        return Broadcast(**result)

    def create(self, params: CreateBroadcastParams | dict[str, Any]) -> Broadcast:
        payload = params.__dict__ if isinstance(params, CreateBroadcastParams) else dict(params)
        result = self._client._request('POST', '/organizations/broadcasts', payload)
        return Broadcast(**result)

    def update(self, id: str, params: dict[str, Any]) -> Broadcast:
        result = self._client._request('PUT', f'/organizations/broadcasts/{id}', params)
        return Broadcast(**result)

    def delete(self, id: str) -> None:
        self._client._request('DELETE', f'/organizations/broadcasts/{id}')

    def send(self, id: str) -> Broadcast:
        result = self._client._request('POST', f'/organizations/broadcasts/{id}/send')
        return Broadcast(**result)

    def schedule(self, id: str, params: ScheduleBroadcastParams | dict[str, Any]) -> Broadcast:
        payload = params.__dict__ if isinstance(params, ScheduleBroadcastParams) else dict(params)
        result = self._client._request('POST', f'/organizations/broadcasts/{id}/schedule', payload)
        return Broadcast(**result)


class AudienceListsResource:
    def __init__(self, client: SendCore) -> None:
        self._client = client

    def list(self) -> list[AudienceList]:
        result = self._client._request('GET', '/organizations/audience/lists')
        return [AudienceList(**a) for a in result]

    def create(self, params: CreateAudienceListParams | dict[str, Any]) -> AudienceList:
        payload = params.__dict__ if isinstance(params, CreateAudienceListParams) else dict(params)
        result = self._client._request('POST', '/organizations/audience/lists', payload)
        return AudienceList(**result)

    def update(self, id: str, params: dict[str, Any]) -> AudienceList:
        result = self._client._request('PUT', f'/organizations/audience/lists/{id}', params)
        return AudienceList(**result)

    def delete(self, id: str) -> None:
        self._client._request('DELETE', f'/organizations/audience/lists/{id}')

    def add_contact(self, params: AddContactParams | dict[str, Any]) -> Any:
        payload = params.__dict__ if isinstance(params, AddContactParams) else dict(params)
        return self._client._request('POST', '/organizations/audience/contacts', payload)

    def list_contacts(self, list_id: Optional[str] = None) -> Any:
        params = {'listId': list_id} if list_id else None
        return self._client._request('GET', '/organizations/audience/contacts', params=params)


class TemplatesResource:
    def __init__(self, client: SendCore) -> None:
        self._client = client

    def list(self) -> list[EmailTemplate]:
        result = self._client._request('GET', '/organizations/templates')
        return [EmailTemplate(**t) for t in result]

    def get(self, id: str) -> EmailTemplate:
        result = self._client._request('GET', f'/organizations/templates/{id}')
        return EmailTemplate(**result)

    def create(self, params: CreateTemplateParams | dict[str, Any]) -> EmailTemplate:
        payload = params.__dict__ if isinstance(params, CreateTemplateParams) else dict(params)
        result = self._client._request('POST', '/organizations/templates', payload)
        return EmailTemplate(**result)

    def update(self, id: str, params: dict[str, Any]) -> EmailTemplate:
        result = self._client._request('PUT', f'/organizations/templates/{id}', params)
        return EmailTemplate(**result)

    def delete(self, id: str) -> None:
        self._client._request('DELETE', f'/organizations/templates/{id}')


class SuppressionsResource:
    def __init__(self, client: SendCore) -> None:
        self._client = client

    def list(
        self,
        page: Optional[int] = None,
        limit: Optional[int] = None,
        search: Optional[str] = None,
    ) -> list[Suppression]:
        params: dict[str, Any] = {}
        if page is not None:
            params['page'] = page
        if limit is not None:
            params['limit'] = limit
        if search is not None:
            params['search'] = search
        result = self._client._request(
            'GET', '/organizations/suppressions',
            params=params or None,
        )
        return [Suppression(**s) for s in result]

    def add(self, params: AddSuppressionParams | dict[str, Any]) -> Suppression:
        payload = params.__dict__ if isinstance(params, AddSuppressionParams) else dict(params)
        result = self._client._request('POST', '/organizations/suppressions', payload)
        return Suppression(**result)

    def remove(self, id: str) -> None:
        self._client._request('DELETE', f'/organizations/suppressions/{id}')


class ApiKeysResource:
    def __init__(self, client: SendCore) -> None:
        self._client = client

    def list(self) -> list[ApiKey]:
        result = self._client._request('GET', '/organizations/api-keys')
        return [ApiKey(**k) for k in result]

    def create(self, params: CreateApiKeyParams | dict[str, Any]) -> CreateApiKeyResponse:
        payload = params.__dict__ if isinstance(params, CreateApiKeyParams) else dict(params)
        result = self._client._request('POST', '/organizations/api-keys', payload)
        return CreateApiKeyResponse(**result)

    def create_mcp(self, name: str) -> CreateApiKeyResponse:
        result = self._client._request('POST', '/organizations/api-keys/mcp', {'name': name})
        return CreateApiKeyResponse(**result)

    def revoke(self, id: str) -> None:
        self._client._request('DELETE', f'/organizations/api-keys/{id}')


class EmailVerificationResource:
    def __init__(self, client: SendCore) -> None:
        self._client = client

    def verify(self, params: VerifyEmailParams | dict[str, Any]) -> VerificationResult:
        payload = params.__dict__ if isinstance(params, VerifyEmailParams) else dict(params)
        result = self._client._request('POST', '/email-verification/verify', payload)
        return VerificationResult(**result)

    def batch(self, params: VerifyBatchParams | dict[str, Any]) -> list[VerificationResult]:
        payload = params.__dict__ if isinstance(params, VerifyBatchParams) else dict(params)
        result = self._client._request('POST', '/email-verification/batch-verify', payload)
        return [VerificationResult(**r) for r in result]


class AnalyticsResource:
    def __init__(self, client: SendCore) -> None:
        self._client = client

    def get(self, days: Optional[int] = None) -> AnalyticsData:
        params = {'days': days} if days is not None else None
        result = self._client._request('GET', '/emails/analytics', params=params)
        return AnalyticsData(**result)

    def stats(self) -> Any:
        return self._client._request('GET', '/emails/stats')


class WebhooksResource:
    @staticmethod
    def verify_signature(payload: str, signature: str, secret: str) -> bool:
        expected = hmac.new(
            secret.encode('utf-8'),
            payload.encode('utf-8'),
            hashlib.sha256,
        ).hexdigest()
        return hmac.compare_digest(expected, signature)

    @staticmethod
    def verify(payload: WebhookPayload, signature: str, secret: str) -> bool:
        return WebhooksResource.verify_signature(
            json.dumps(payload.__dict__), signature, secret
        )


class WorkflowsResource:
    def __init__(self, client: SendCore) -> None:
        self._client = client

    def list(self) -> Any:
        return self._client._request('GET', '/organizations/workflows')

    def get(self, id: str) -> Any:
        return self._client._request('GET', f'/organizations/workflows/{id}')

    def create(self, params: dict[str, Any]) -> Any:
        return self._client._request('POST', '/organizations/workflows', params)

    def update(self, id: str, params: dict[str, Any]) -> Any:
        return self._client._request('PUT', f'/organizations/workflows/{id}', params)

    def delete(self, id: str) -> None:
        self._client._request('DELETE', f'/organizations/workflows/{id}')

    def activate(self, id: str) -> Any:
        return self._client._request('POST', f'/organizations/workflows/{id}/activate')

    def pause(self, id: str) -> Any:
        return self._client._request('POST', f'/organizations/workflows/{id}/pause')

    def add_step(self, workflow_id: str, params: dict[str, Any]) -> Any:
        return self._client._request(
            'POST', f'/organizations/workflows/{workflow_id}/steps', params
        )

    def update_step(self, step_id: str, params: dict[str, Any]) -> Any:
        return self._client._request(
            'PUT', f'/organizations/workflows/steps/{step_id}', params
        )

    def delete_step(self, step_id: str) -> None:
        self._client._request('DELETE', f'/organizations/workflows/steps/{step_id}')

    def get_executions(self, workflow_id: str) -> Any:
        return self._client._request(
            'GET', f'/organizations/workflows/{workflow_id}/executions'
        )

    def get_execution(self, execution_id: str) -> Any:
        return self._client._request(
            'GET', f'/organizations/workflows/executions/{execution_id}'
        )

    def test(self, workflow_id: str, contact_id: Optional[str] = None) -> Any:
        body: dict[str, Any] = {}
        if contact_id is not None:
            body['contactId'] = contact_id
        return self._client._request(
            'POST', f'/organizations/workflows/{workflow_id}/test', body
        )


class AgentInboxesResource:
    def __init__(self, client: SendCore) -> None:
        self._client = client

    def create(self, params: CreateAgentInboxParams | dict[str, Any]) -> AgentInbox:
        payload = params.__dict__ if isinstance(params, CreateAgentInboxParams) else dict(params)
        result = self._client._request('POST', '/agent-inboxes', payload)
        return AgentInbox(**result)

    def list(self) -> list[AgentInbox]:
        result = self._client._request('GET', '/agent-inboxes')
        return [AgentInbox(**i) for i in result]

    def get(self, id: str) -> AgentInbox:
        result = self._client._request('GET', f'/agent-inboxes/{id}')
        return AgentInbox(**result)

    def delete(self, id: str) -> None:
        self._client._request('DELETE', f'/agent-inboxes/{id}')

    def set_webhook(self, id: str, url: str) -> AgentInbox:
        result = self._client._request('PUT', f'/agent-inboxes/{id}/webhook', {'url': url})
        return AgentInbox(**result)

    def get_emails(self, id: str, page: Optional[int] = None, limit: Optional[int] = None, search: Optional[str] = None) -> PaginatedEmails:
        params: dict[str, Any] = {}
        if page is not None:
            params['page'] = page
        if limit is not None:
            params['limit'] = limit
        if search is not None:
            params['search'] = search
        result = self._client._request('GET', f'/agent-inboxes/{id}/emails', params=params or None)
        return PaginatedEmails(**result)

    def get_email(self, inbox_id: str, email_id: str) -> InboundEmail:
        result = self._client._request('GET', f'/agent-inboxes/{inbox_id}/emails/{email_id}')
        return InboundEmail(**result)

    def mark_as_read(self, inbox_id: str, email_id: str) -> None:
        self._client._request('PUT', f'/agent-inboxes/{inbox_id}/emails/{email_id}/read')

    def send_email(self, id: str, params: SendAsAgentParams | dict[str, Any]) -> Any:
        payload = params.__dict__ if isinstance(params, SendAsAgentParams) else dict(params)
        to = payload.get('to')
        if isinstance(to, str):
            payload['to'] = [to]
        return self._client._request('POST', f'/agent-inboxes/{id}/send', payload)

    def list_threads(self, inbox_id: str, page: Optional[int] = None, limit: Optional[int] = None) -> PaginatedThreads:
        params: dict[str, Any] = {}
        if page is not None:
            params['page'] = page
        if limit is not None:
            params['limit'] = limit
        result = self._client._request('GET', f'/agent-inboxes/{inbox_id}/threads', params=params or None)
        return PaginatedThreads(**result)

    def get_thread(self, inbox_id: str, thread_id: str) -> Any:
        return self._client._request('GET', f'/agent-inboxes/{inbox_id}/threads/{thread_id}')

    def get_thread_by_email(self, inbox_id: str, email_id: str) -> Any:
        return self._client._request('GET', f'/agent-inboxes/{inbox_id}/emails/{email_id}/thread')

    def get_attachment(self, inbox_id: str, email_id: str, attachment_id: str) -> Any:
        return self._client._request('GET', f'/agent-inboxes/{inbox_id}/emails/{email_id}/attachments/{attachment_id}')


def _default_json(o: Any) -> Any:
    if hasattr(o, '__dict__'):
        return o.__dict__
    raise TypeError(f'Object of type {type(o).__name__} is not JSON serializable')
