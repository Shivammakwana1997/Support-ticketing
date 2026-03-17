from abc import ABC, abstractmethod


class ChannelProvider(ABC):
    """Abstract base class for all channel providers.

    Each channel provider must implement methods for sending messages,
    receiving and normalizing inbound messages, and validating webhook
    signatures to ensure request authenticity.
    """

    @abstractmethod
    async def send_message(
        self,
        recipient: str,
        content: str,
        metadata: dict | None = None,
    ) -> dict:
        """Send a message through the channel.

        Args:
            recipient: The recipient identifier (phone number, email, channel ID, etc.).
            content: The message body to send.
            metadata: Optional provider-specific metadata (e.g. subject, attachments).

        Returns:
            A dict containing at minimum ``{"message_id": str, "status": str}``.
        """

    @abstractmethod
    async def receive_message(self, raw_payload: dict) -> dict:
        """Parse an inbound webhook payload into a normalized message dict.

        Args:
            raw_payload: The raw request body received from the channel's webhook.

        Returns:
            A normalized dict with the shape::

                {
                    "sender": str,
                    "content": str,
                    "channel": str,
                    "metadata": dict,
                }
        """

    @abstractmethod
    async def validate_webhook(
        self,
        request_data: dict,
        signature: str,
    ) -> bool:
        """Validate that an incoming webhook request is authentic.

        Args:
            request_data: The request data to verify.
            signature: The signature header provided by the channel.

        Returns:
            ``True`` if the request is valid, ``False`` otherwise.
        """
