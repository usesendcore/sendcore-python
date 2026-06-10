from dataclasses import dataclass, field
from typing import Optional, Any


@dataclass
class SendCoreConfig:
    apiKey: str
    baseUrl: Optional[str] = None
    timeout: Optional[int] = None
    retries: Optional[int] = None


@dataclass
class EmailAttachment:
    filename: str
    content: str
    contentType: Optional[str] = None


@dataclass
class SendEmailParams:
    from_: str
    to: str | list[str]
    subject: Optional[str] = None
    html: Optional[str] = None
    text: Optional[str] = None
    cc: Optional[str | list[str]] = None
    bcc: Optional[str | list[str]] = None
    replyTo: Optional[str | list[str]] = None
    templateId: Optional[str] = None
    templateData: Optional[dict[str, Any]] = None
    attachments: Optional[list[EmailAttachment]] = None
    tags: Optional[dict[str, str]] = None

    def __post_init__(self):
        if hasattr(self, 'from_'):
            object.__setattr__(self, 'from', self.from_)

    def to_dict(self) -> dict[str, Any]:
        d: dict[str, Any] = {}
        for k, v in self.__dict__.items():
            if k == 'from_':
                d['from'] = v
            elif k == 'attachments' and v:
                d['attachments'] = [
                    a.__dict__ if hasattr(a, '__dict__') else a for a in v
                ]
            elif v is not None:
                d[k] = v
        return d


@dataclass
class SendEmailResponse:
    id: str
    status: str


@dataclass
class Domain:
    id: str
    name: str
    status: str
    spfStatus: bool
    dkimStatus: bool
    dmarcStatus: bool
    verificationToken: Optional[str] = None
    createdAt: str = ''
    updatedAt: str = ''


@dataclass
class DnsRecord:
    type: str
    name: str
    value: str
    priority: Optional[int] = None


@dataclass
class VerifyEmailParams:
    email: str


@dataclass
class VerifyBatchParams:
    emails: list[str]


@dataclass
class VerificationResult:
    email: str
    isValid: bool
    score: float
    reason: str


@dataclass
class AnalyticsParams:
    days: Optional[int] = None


@dataclass
class AnalyticsData:
    data: list[Any] = field(default_factory=list)


@dataclass
class Broadcast:
    id: str
    name: str
    subject: Optional[str] = None
    status: str = 'DRAFT'
    listIds: Optional[list[str]] = None
    scheduledAt: Optional[str] = None
    sentCount: Optional[int] = 0
    openCount: Optional[int] = 0
    clickCount: Optional[int] = 0
    createdAt: str = ''
    updatedAt: str = ''


@dataclass
class CreateBroadcastParams:
    name: str
    subject: Optional[str] = None
    content: Optional[str] = None
    listIds: Optional[list[str]] = None


@dataclass
class ScheduleBroadcastParams:
    scheduledAt: str


@dataclass
class AudienceList:
    id: str
    name: str
    description: Optional[str] = None
    contactCount: Optional[int] = 0
    createdAt: str = ''
    updatedAt: str = ''


@dataclass
class CreateAudienceListParams:
    name: str
    description: Optional[str] = None


@dataclass
class AddContactParams:
    email: str
    firstName: Optional[str] = None
    lastName: Optional[str] = None
    listIds: Optional[list[str]] = None
    customData: Optional[dict[str, Any]] = None


@dataclass
class EmailTemplate:
    id: str
    name: str
    subject: Optional[str] = None
    html: Optional[str] = None
    text: Optional[str] = None
    design: Optional[dict[str, Any]] = None
    createdAt: str = ''
    updatedAt: str = ''


@dataclass
class CreateTemplateParams:
    name: str
    subject: Optional[str] = None
    html: Optional[str] = None
    text: Optional[str] = None
    design: Optional[dict[str, Any]] = None


@dataclass
class Suppression:
    id: str
    email: str
    reason: Optional[str] = None
    createdAt: str = ''


@dataclass
class AddSuppressionParams:
    email: str
    reason: Optional[str] = None


@dataclass
class ApiKey:
    id: str
    name: str
    prefix: str
    scopes: list[str]
    createdAt: str = ''
    expiresAt: Optional[str] = None


@dataclass
class CreateApiKeyParams:
    name: str
    scopes: Optional[list[str]] = None
    expiresInDays: Optional[int] = None


@dataclass
class CreateApiKeyResponse:
    id: str
    name: str
    key: str
    scopes: list[str]
    createdAt: str = ''


@dataclass
class SubscribeParams:
    email: str
    firstName: Optional[str] = None
    lastName: Optional[str] = None
    listId: Optional[str] = None
    customData: Optional[dict[str, Any]] = None


@dataclass
class WorkflowStepConfig:
    to: Optional[str] = None
    from_: Optional[str] = None
    subject: Optional[str] = None
    html: Optional[str] = None
    templateSlug: Optional[str] = None
    templateData: Optional[dict[str, Any]] = None
    duration: Optional[int] = None
    unit: Optional[str] = None
    field: Optional[str] = None
    operator: Optional[str] = None
    value: Optional[str] = None
    prompt: Optional[str] = None
    listId: Optional[str] = None
    fields: Optional[dict[str, Any]] = None
    url: Optional[str] = None
    body: Optional[dict[str, Any]] = None

    def to_dict(self) -> dict[str, Any]:
        d: dict[str, Any] = {}
        for k, v in self.__dict__.items():
            if k == 'from_':
                d['from'] = v
            elif v is not None:
                d[k] = v
        return d


@dataclass
class WorkflowStep:
    id: str
    order: int
    type: str
    config: WorkflowStepConfig | dict[str, Any]
    label: Optional[str] = None
    parentStepId: Optional[str] = None
    createdAt: str = ''
    updatedAt: str = ''


@dataclass
class Workflow:
    id: str
    name: str
    triggerType: str
    triggerConfig: dict[str, Any]
    status: str = 'DRAFT'
    description: Optional[str] = None
    aiGenerated: bool = False
    executionCount: int = 0
    steps: list[WorkflowStep] = field(default_factory=list)
    createdAt: str = ''
    updatedAt: str = ''


@dataclass
class WorkflowExecutionLog:
    id: str
    stepId: str
    stepType: str
    status: str
    input: Optional[Any] = None
    output: Optional[Any] = None
    error: Optional[str] = None
    startedAt: str = ''
    completedAt: Optional[str] = None


@dataclass
class WorkflowExecution:
    id: str
    workflowId: str
    status: str
    currentStep: int = 0
    contactId: Optional[str] = None
    triggerEntityType: Optional[str] = None
    triggerEntityId: Optional[str] = None
    context: dict[str, Any] = field(default_factory=dict)
    logs: list[WorkflowExecutionLog] = field(default_factory=list)
    createdAt: str = ''
    updatedAt: str = ''


@dataclass
class CreateWorkflowParams:
    name: str
    triggerType: str
    description: Optional[str] = None
    triggerConfig: Optional[dict[str, Any]] = None
    steps: Optional[list[dict[str, Any]]] = None


@dataclass
class WebhookPayload:
    event: str
    data: dict[str, Any]
    timestamp: int


# ─── Agent Inbox Types ──────────────────────

@dataclass
class AgentInbox:
    id: str
    emailAddress: str
    status: str = 'ACTIVE'
    displayName: Optional[str] = None
    webhookUrl: Optional[str] = None
    metadata: Optional[dict[str, Any]] = None
    createdAt: str = ''
    updatedAt: str = ''


@dataclass
class CreateAgentInboxParams:
    displayName: Optional[str] = None
    webhookUrl: Optional[str] = None
    metadata: Optional[dict[str, Any]] = None


@dataclass
class InboundEmail:
    id: str
    inboxId: str
    fromAddress: str
    toAddress: str
    subject: Optional[str] = None
    fromName: Optional[str] = None
    bodyText: Optional[str] = None
    bodyHtml: Optional[str] = None
    parsedOtp: Optional[str] = None
    messageId: Optional[str] = None
    inReplyTo: Optional[str] = None
    references: Optional[str] = None
    isRead: bool = False
    receivedAt: str = ''


@dataclass
class SendAsAgentParams:
    to: str | list[str]
    subject: str
    body: str
    inReplyTo: Optional[str] = None


@dataclass
class PaginatedEmails:
    data: list[InboundEmail] = field(default_factory=list)
    page: int = 1
    limit: int = 50
    total: int = 0
    totalPages: int = 0
