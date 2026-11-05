"""
Real Hedera Consensus Service (HCS) integration using the official
`hedera-sdk-py` package. This is genuine, runnable code against the classes
that package actually exposes (Client, AccountId, PrivateKey,
TopicCreateTransaction, TopicMessageSubmitTransaction) — but it is DISABLED
by default and returns a clear "not configured" status until you provide
real testnet credentials.

Why it's gated: this sandbox has no Hedera testnet account, no HBAR, and no
network route to Hedera's nodes. Faking a "connected" response would be
dishonest. Set the environment variables below and this module will submit
every ledger block as a real HCS topic message.

Required env vars:
    HEDERA_ACCOUNT_ID     e.g. "0.0.123456"
    HEDERA_PRIVATE_KEY    your ED25519/ECDSA private key string
    HEDERA_NETWORK        "testnet" (default) or "mainnet"
    HEDERA_TOPIC_ID       an existing topic id, e.g. "0.0.789012"
                          (or leave unset and call create_topic() once)
"""
import os
from typing import Optional

_HEDERA_SDK_ERROR: str | None = None
try:
    from hedera import (
        Client, AccountId, PrivateKey,
        TopicCreateTransaction, TopicMessageSubmitTransaction,
    )
    _HEDERA_SDK_AVAILABLE = True
except Exception as e:
    # Catch any import-time errors (including jnius / Java errors) so the
    # whole application can start even when Hedera native dependencies
    # (JNI / javac / JDK) are missing in the runtime environment.
    _HEDERA_SDK_AVAILABLE = False
    _HEDERA_SDK_ERROR = str(e)


def _load_credentials():
    account_id = os.getenv("HEDERA_ACCOUNT_ID")
    private_key = os.getenv("HEDERA_PRIVATE_KEY")
    network = os.getenv("HEDERA_NETWORK", "testnet")
    topic_id = os.getenv("HEDERA_TOPIC_ID")
    return account_id, private_key, network, topic_id


def status() -> dict:
    """Report whether real Hedera connectivity is configured, without
    attempting a network call unless credentials are actually present."""
    if not _HEDERA_SDK_AVAILABLE:
        return {
            "configured": False,
            "reason": _HEDERA_SDK_ERROR or "hedera-sdk-py not available or failed to initialize",
        }
    account_id, private_key, network, topic_id = _load_credentials()
    if not (account_id and private_key):
        return {
            "configured": False,
            "reason": "HEDERA_ACCOUNT_ID / HEDERA_PRIVATE_KEY not set — "
                      "running in local-ledger-only mode (see ledger_service.py).",
        }
    return {
        "configured": True,
        "network": network,
        "topic_id": topic_id,
        "account_id": account_id,
    }


def _get_client(account_id: str, private_key: str, network: str) -> "Client":
    client = Client.forTestnet() if network == "testnet" else Client.forMainnet()
    client.setOperator(AccountId.fromString(account_id), PrivateKey.fromString(private_key))
    return client


def create_topic(memo: str = "CRISPR-X audit ledger") -> dict:
    """Create a new HCS topic to anchor ledger blocks to. Requires real
    credentials; raises RuntimeError otherwise rather than pretending."""
    account_id, private_key, network, _ = _load_credentials()
    if not (_HEDERA_SDK_AVAILABLE and account_id and private_key):
        raise RuntimeError("Hedera not configured — set HEDERA_ACCOUNT_ID and HEDERA_PRIVATE_KEY")
    client = _get_client(account_id, private_key, network)
    receipt = (
        TopicCreateTransaction()
        .setTopicMemo(memo)
        .execute(client)
        .getReceipt(client)
    )
    return {"topic_id": str(receipt.topicId)}


def submit_ledger_block(block: dict) -> dict:
    """Submit one audit-ledger block's hash (not the raw data) as an HCS
    message, anchoring it to Hedera's public consensus timestamp. Requires
    real credentials and an existing topic; raises RuntimeError otherwise."""
    account_id, private_key, network, topic_id = _load_credentials()
    if not (_HEDERA_SDK_AVAILABLE and account_id and private_key and topic_id):
        raise RuntimeError(
            "Hedera not configured — set HEDERA_ACCOUNT_ID, HEDERA_PRIVATE_KEY, "
            "and HEDERA_TOPIC_ID to submit real HCS messages"
        )
    client = _get_client(account_id, private_key, network)
    message = f"block#{block['index']} hash={block['hash']}"
    receipt = (
        TopicMessageSubmitTransaction()
        .setTopicId(topic_id)
        .setMessage(message)
        .execute(client)
        .getReceipt(client)
    )
    return {"status": str(receipt.status), "topic_id": topic_id, "message": message}
