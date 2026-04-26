import asyncio
import os
import threading
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from typing import Optional

import discord

from server.discord_classifier import classify_discord_message
from server.discord_live_hub import broadcast_event


@dataclass
class ModerationRecord:
    message_id: int
    channel_id: int
    guild_id: int
    author_id: int
    author_name: str
    content: str
    created_at: str
    decision: str
    reason_code: str
    severity: str
    confidence: float
    explanation: str
    model: str
    status: str
    action_taken: str
    escalated: bool = False
    bot_actions: list[str] = field(default_factory=list)
    classifier_source: str = ""


class DiscordModerationService:
    def __init__(self) -> None:
        intents = discord.Intents.default()
        intents.message_content = True
        intents.guilds = True
        intents.messages = True

        self.client = discord.Client(intents=intents)
        self._records: dict[int, ModerationRecord] = {}
        self._lock = threading.Lock()
        self._loop: Optional[asyncio.AbstractEventLoop] = None
        self._runner: Optional[threading.Thread] = None
        self._mod_log_channel_id = self._parse_optional_int(os.getenv("DISCORD_MOD_LOG_CHANNEL_ID"))
        self._register_handlers()

    @staticmethod
    def _parse_optional_int(value: Optional[str]) -> Optional[int]:
        if not value:
            return None
        try:
            return int(value.strip())
        except (TypeError, ValueError):
            return None

    def _register_handlers(self) -> None:
        @self.client.event
        async def on_ready():
            print(f"[discord] logged in as {self.client.user}")
            self._loop = asyncio.get_running_loop()

        @self.client.event
        async def on_message(message: discord.Message):
            if message.author.bot or message.guild is None:
                return
            await self._handle_message(message)

    async def _safe_add_reaction(self, message: discord.Message, emoji: str) -> bool:
        try:
            await message.add_reaction(emoji)
            return True
        except Exception:
            return False

    async def _safe_clear_reactions(self, message: discord.Message, emojis: tuple[str, ...]) -> None:
        for e in emojis:
            try:
                await message.remove_reaction(e, self.client.user)
            except Exception:
                pass

    async def _handle_message(self, message: discord.Message) -> None:
        author_display = str(message.author)
        try:
            moderation, classifier_source = classify_discord_message(message.content, author_display)
        except Exception as exc:
            print(f"[discord] moderation failed for {message.id}: {exc}")
            err_record = ModerationRecord(
                message_id=message.id,
                channel_id=message.channel.id,
                guild_id=message.guild.id,
                author_id=message.author.id,
                author_name=author_display,
                content=message.content,
                created_at=datetime.now(timezone.utc).isoformat(),
                decision="escalate",
                reason_code="clean",
                severity="low",
                confidence=0.0,
                explanation=f"Classifier error: {exc}",
                model="none",
                status="classifier_error",
                action_taken="none",
                escalated=False,
                bot_actions=["classifier_failed"],
                classifier_source="error",
            )
            with self._lock:
                self._records[message.id] = err_record
            broadcast_event(
                {
                    "type": "discord_error",
                    "message_id": message.id,
                    "channel_id": message.channel.id,
                    "guild_id": message.guild.id,
                    "error": str(exc),
                }
            )
            broadcast_event({"type": "discord_moderation", "record": asdict(err_record)})
            return

        decision = moderation.get("decision", "escalate")
        action_taken = "none"
        escalated = False
        bot_actions: list[str] = []

        if decision == "remove":
            try:
                await message.delete()
                action_taken = "deleted"
                bot_actions.append("delete_message")
            except Exception as exc:
                action_taken = f"delete_failed:{exc}"
                bot_actions.append(f"delete_failed:{exc}")
        elif decision == "escalate":
            escalated = True
            action_taken = "reported"
            if await self._safe_add_reaction(message, "🚨"):
                bot_actions.append("reaction_report")
            await self._send_to_mod_log(message, moderation, report=True)
        else:
            action_taken = "accepted"
            if await self._safe_add_reaction(message, "👍"):
                bot_actions.append("reaction_thumbs_up")

        record = ModerationRecord(
            message_id=message.id,
            channel_id=message.channel.id,
            guild_id=message.guild.id,
            author_id=message.author.id,
            author_name=author_display,
            content=message.content,
            created_at=datetime.now(timezone.utc).isoformat(),
            decision=decision,
            reason_code=moderation.get("reason_code", "clean"),
            severity=moderation.get("severity", "low"),
            confidence=float(moderation.get("confidence", 0.0)),
            explanation=moderation.get("explanation", ""),
            model=moderation.get("model", "unknown"),
            status="pending_review" if decision == "escalate" else "auto_resolved",
            action_taken=action_taken,
            escalated=escalated,
            bot_actions=bot_actions,
            classifier_source=classifier_source,
        )

        with self._lock:
            self._records[message.id] = record

        broadcast_event(
            {
                "type": "discord_moderation",
                "record": asdict(record),
            }
        )

    async def _send_to_mod_log(
        self, message: discord.Message, moderation: dict, report: bool = False
    ) -> None:
        channel = None
        if self._mod_log_channel_id:
            channel = self.client.get_channel(self._mod_log_channel_id)
        if channel is None:
            return
        prefix = "🚨 REPORT" if report else "🚩 Escalated"
        try:
            await channel.send(
                f"{prefix} message `{message.id}` in <#{message.channel.id}> by `{message.author}`\n"
                f"Reason: `{moderation.get('reason_code', 'harassment')}` | "
                f"Severity: `{moderation.get('severity', 'medium')}` | "
                f"Confidence: `{moderation.get('confidence', 0.0)}`\n"
                f"Content: {message.content}"
            )
        except Exception as exc:
            print(f"[discord] failed to send mod log: {exc}")

    def start(self) -> bool:
        token = os.getenv("DISCORD_BOT_TOKEN", "").strip()
        if not token:
            print("[discord] DISCORD_BOT_TOKEN missing; bot disabled")
            return False

        if self._runner and self._runner.is_alive():
            return True

        def run():
            try:
                self.client.run(token, log_handler=None)
            except Exception as exc:
                print(f"[discord] bot stopped: {exc}")

        self._runner = threading.Thread(target=run, name="discord-bot-thread", daemon=True)
        self._runner.start()
        return True

    def status(self) -> dict:
        return {
            "enabled": bool(os.getenv("DISCORD_BOT_TOKEN", "").strip()),
            "connected": bool(self.client.is_ready()),
            "user": str(self.client.user) if self.client.user else None,
            "watched_messages": len(self._records),
            "mod_log_channel_id": self._mod_log_channel_id,
        }

    def get_records(self, pending_only: bool = False) -> list[dict]:
        with self._lock:
            records = list(self._records.values())
        if pending_only:
            records = [r for r in records if r.status == "pending_review"]
        records.sort(key=lambda r: r.created_at, reverse=True)
        return [asdict(r) for r in records]

    async def _apply_action_async(self, message_id: int, action: str) -> dict:
        with self._lock:
            record = self._records.get(message_id)
        if not record:
            raise ValueError(f"message_id {message_id} not found")

        channel = self.client.get_channel(record.channel_id)
        if channel is None:
            raise ValueError(f"channel {record.channel_id} is not cached")

        try:
            message = await channel.fetch_message(message_id)
        except Exception as exc:
            raise ValueError(f"cannot fetch message {message_id}: {exc}") from exc

        action = action.lower().strip()
        bot_actions: list[str] = []

        if action == "delete":
            try:
                await message.delete()
                bot_actions.append("delete_message")
            except Exception as exc:
                raise ValueError(f"delete failed: {exc}") from exc
            with self._lock:
                self._records[message_id].status = "deleted_by_api"
                self._records[message_id].action_taken = "deleted"
                self._records[message_id].bot_actions = bot_actions
        elif action == "accept":
            await self._safe_clear_reactions(message, ("🚩", "🚨"))
            if await self._safe_add_reaction(message, "👍"):
                bot_actions.append("reaction_thumbs_up")
            with self._lock:
                self._records[message_id].status = "accepted_by_api"
                self._records[message_id].action_taken = "accepted"
                self._records[message_id].escalated = False
                self._records[message_id].bot_actions = bot_actions
        elif action in {"escalate", "flag"}:
            await self._safe_clear_reactions(message, ("👍",))
            if await self._safe_add_reaction(message, "🚨"):
                bot_actions.append("reaction_report")
            with self._lock:
                self._records[message_id].status = "escalated_by_api"
                self._records[message_id].action_taken = "reported"
                self._records[message_id].escalated = True
                self._records[message_id].bot_actions = bot_actions
        else:
            raise ValueError("action must be one of: accept, delete, escalate, flag")

        with self._lock:
            updated = asdict(self._records[message_id])
        broadcast_event({"type": "discord_review", "record": updated})
        return updated

    def apply_action(self, message_id: int, action: str) -> dict:
        if not self._loop:
            raise RuntimeError("discord bot is not connected yet")
        future = asyncio.run_coroutine_threadsafe(self._apply_action_async(message_id, action), self._loop)
        return future.result(timeout=20)


discord_service = DiscordModerationService()
