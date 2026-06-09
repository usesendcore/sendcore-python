from typing import Any


_HINTS: dict[int, str] = {
    400: 'Check your request payload for missing or invalid fields.',
    401: 'Your API key is invalid or missing. Get one at https://usesendcore.com/dashboard/api-keys',
    403: "You don't have permission for this action. Check your plan limits or team role.",
    404: 'The requested resource was not found. Verify the ID or endpoint path.',
    413: "Payload too large. Reduce attachment sizes or email content.",
    429: "Rate limit exceeded. Slow down — you'll be retried automatically.",
    500: 'Server error. If this persists, check https://status.usesendcore.com',
    502: 'Temporary gateway error. Automatic retry has been attempted.',
    503: 'Service temporarily unavailable. Automatic retry has been attempted.',
}


class SendCoreError(Exception):
    def __init__(self, status_code: int, detail: dict[str, Any]) -> None:
        self.status_code = status_code
        self.detail = detail
        self.message = detail.get('message', '')

        hint = _HINTS.get(status_code)
        parts = [self.message]
        if hint:
            parts.append(f'\n  \U0001f4a1 {hint}')
        error_detail = detail.get('error')
        if error_detail:
            parts.append(f'\n  \U0001f50d Server detail: {error_detail}')
        super().__init__(''.join(parts))

    @property
    def is_rate_limited(self) -> bool:
        return self.status_code == 429

    @property
    def is_unauthorized(self) -> bool:
        return self.status_code == 401

    @property
    def is_server_error(self) -> bool:
        return self.status_code >= 500


def is_sendcore_error(err: object) -> bool:
    return isinstance(err, SendCoreError)
