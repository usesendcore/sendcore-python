# SendCore Python SDK

Python SDK for the [SendCore](https://usesendcore.com) email API.

## Installation

```bash
pip install sendcore
```

No external dependencies required — uses only the Python standard library.

## Quick Start

```python
from sendcore import SendCore

# Initialize with your API key
client = SendCore('sk_live_xxxxxxxxxxxx')

# Send an email
response = client.emails.send({
    'from': 'sender@example.com',
    'to': 'recipient@example.com',
    'subject': 'Hello from SendCore',
    'html': '<h1>Hello!</h1><p>This is a test email.</p>',
})

print(f'Sent: {response.id} ({response.status})')
```

## Configuration

```python
from sendcore import SendCore

client = SendCore({
    'apiKey': 'sk_live_xxxxxxxxxxxx',
    'baseUrl': 'https://api.usesendcore.com',
    'timeout': 30,   # seconds
    'retries': 2,    # automatic retries with exponential backoff
})
```

## Usage

### Email

```python
# Send with all options
client.emails.send({
    'from': 'sender@example.com',
    'to': ['user1@example.com', 'user2@example.com'],
    'subject': 'Hello',
    'html': '<h1>Hello!</h1>',
    'text': 'Hello!',
    'cc': 'cc@example.com',
    'bcc': 'bcc@example.com',
    'replyTo': 'support@example.com',
    'tags': {'campaign': 'welcome'},
    'attachments': [{'filename': 'report.pdf', 'content': '...', 'contentType': 'application/pdf'}],
})

# Email logs
client.emails.logs(page=1, limit=50)

# Email stats
client.emails.stats()

# Email analytics
client.emails.analytics(days=30)
```

### Domains

```python
# List domains
client.domains.list()

# Add domain
client.domains.add({'name': 'example.com'})

# Verify domain
client.domains.verify('domain_id')

# Get DNS records
client.domains.get_dns_records('domain_id')

# Check domain health
client.domains.health('domain_id')

# Remove domain
client.domains.remove('domain_id')
```

### Broadcasts (Campaigns)

```python
# List
client.broadcasts.list()

# Create
client.broadcasts.create({
    'name': 'My Campaign',
    'subject': 'Hello',
    'content': '<h1>Email content</h1>',
    'listIds': ['list_id_1'],
})

# Send
client.broadcasts.send('broadcast_id')

# Schedule
client.broadcasts.schedule('broadcast_id', {'scheduledAt': '2025-01-01T00:00:00Z'})
```

### Audience Lists

```python
# Create list
client.audience_lists.create({'name': 'Newsletter', 'description': 'Newsletter subscribers'})

# Add contact
client.audience_lists.add_contact({
    'email': 'user@example.com',
    'firstName': 'John',
    'lastName': 'Doe',
    'listIds': ['list_id'],
})

# List contacts
client.audience_lists.list_contacts(list_id='list_id')
```

### Templates

```python
client.templates.list()
client.templates.get('template_id')
client.templates.create({'name': 'Welcome', 'subject': 'Welcome!', 'html': '<p>Hi {{name}}</p>'})
client.templates.update('template_id', {'subject': 'Updated subject'})
client.templates.delete('template_id')
```

### Suppressions

```python
client.suppressions.list(page=1, limit=20, search='spam@example.com')
client.suppressions.add({'email': 'spam@example.com', 'reason': 'Spam'})
client.suppressions.remove('suppression_id')
```

### API Keys

```python
client.api_keys.list()
client.api_keys.create({'name': 'My Key', 'scopes': ['email:send'], 'expiresInDays': 30})
client.api_keys.create_mcp('MCP Key')
client.api_keys.revoke('key_id')
```

### Email Verification

```python
client.verify.verify({'email': 'user@example.com'})
client.verify.batch({'emails': ['a@example.com', 'b@example.com']})
```

### Workflows

```python
client.workflows.list()
client.workflows.create({
    'name': 'Welcome Flow',
    'triggerType': 'contact.created',
})
client.workflows.activate('workflow_id')
client.workflows.pause('workflow_id')
client.workflows.add_step('workflow_id', {'type': 'send_email', 'config': {'subject': 'Welcome'}})
client.workflows.test('workflow_id', contact_id='contact_id')
```

### Webhook Signature Verification

```python
from sendcore import SendCore

client = SendCore('sk_live_xxxxxxxxxxxx')
is_valid = client.webhooks.verify_signature(payload_body, signature_header, webhook_secret)
```

## Error Handling

```python
from sendcore import SendCore, SendCoreError, is_sendcore_error

try:
    client.emails.send({'from': '...', 'to': '...'})
except SendCoreError as e:
    print(e.status_code)       # HTTP status code
    print(e.message)           # Error message
    print(e.detail)            # Full error detail dict
    print(e.is_rate_limited)   # True if 429
    print(e.is_unauthorized)   # True if 401
    print(e.is_server_error)   # True if 500+
```

## License

MIT
