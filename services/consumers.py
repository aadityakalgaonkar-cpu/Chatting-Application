import json

from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async
from django.utils import timezone

from .models import (
    Conversation,
    ConversationParticipant,
    Message,
    UserProfile,
)


class ChatConsumer(AsyncWebsocketConsumer):

    async def connect(self):
        self.user = self.scope["user"]
        self.connection_accepted = False

        if self.user.is_anonymous:
            await self.close(code=4001)
            return

        self.conversation_id = self.scope["url_route"]["kwargs"][
            "conversation_id"
        ]

        if not await self.conversation_exists():
            await self.close(code=4004)
            return

        if not await self.is_participant():
            await self.close(code=4003)
            return

        self.room_group_name = f"chat_{self.conversation_id}"

        await self.channel_layer.group_add(
            self.room_group_name,
            self.channel_name,
        )

        await self.accept()
        self.connection_accepted = True

        await self.set_online()

        # Notify the other user that this user is online.
        await self.channel_layer.group_send(
            self.room_group_name,
            {
                "type": "status_message",
                "username": self.user.username,
                "status": "online",
                "sender_channel": self.channel_name,
            },
        )

        print(
            f"{self.user.username} connected to "
            f"conversation {self.conversation_id}"
        )

    async def disconnect(self, close_code):
        room_group_name = getattr(self, "room_group_name", None)

        if room_group_name:
            await self.channel_layer.group_discard(
                room_group_name,
                self.channel_name,
            )

        if (
            self.connection_accepted
            and not self.user.is_anonymous
        ):
            await self.set_offline()

            if room_group_name:
                await self.channel_layer.group_send(
                    room_group_name,
                    {
                        "type": "status_message",
                        "username": self.user.username,
                        "status": "offline",
                        "sender_channel": self.channel_name,
                    },
                )

        print(
            f"{self.user.username} disconnected"
        )

    async def receive(self, text_data):
        try:
            data = json.loads(text_data)
        except json.JSONDecodeError:
            await self.send_json({
                "type": "error",
                "message": "Invalid JSON data.",
            })
            return

        message_type = data.get("type")

        # ==========================================
        # CHAT MESSAGE
        # ==========================================

        if message_type in ["chat", "message"]:
            message_text = data.get("message", "").strip()

            if not message_text:
                await self.send_json({
                    "type": "error",
                    "message": "Message cannot be empty.",
                })
                return

            if len(message_text) > 5000:
                await self.send_json({
                    "type": "error",
                    "message": "Message is too long.",
                })
                return

            await self.save_message(message_text)

            await self.channel_layer.group_send(
                self.room_group_name,
                {
                    "type": "chat_message",
                    "message": message_text,
                    "username": self.user.username,
                    "time": timezone.localtime().strftime("%H:%M"),
                },
            )

        # ==========================================
        # WEBRTC OFFER
        # ==========================================

        elif message_type == "offer":
            offer = data.get("offer")

            if not offer:
                return

            await self.channel_layer.group_send(
                self.room_group_name,
                {
                    "type": "webrtc_offer",
                    "offer": offer,
                    "username": self.user.username,
                    "sender_channel": self.channel_name,
                },
            )

        # ==========================================
        # WEBRTC ANSWER
        # ==========================================

        elif message_type == "answer":
            answer = data.get("answer")

            if not answer:
                return

            await self.channel_layer.group_send(
                self.room_group_name,
                {
                    "type": "webrtc_answer",
                    "answer": answer,
                    "username": self.user.username,
                    "sender_channel": self.channel_name,
                },
            )

        # ==========================================
        # ICE CANDIDATE
        # ==========================================

        elif message_type in ["ice", "ice_candidate"]:
            candidate = data.get("candidate")

            if not candidate:
                return

            await self.channel_layer.group_send(
                self.room_group_name,
                {
                    "type": "webrtc_ice",
                    "candidate": candidate,
                    "username": self.user.username,
                    "sender_channel": self.channel_name,
                },
            )

        # ==========================================
        # END VIDEO CALL
        # ==========================================

        elif message_type == "end_call":
            await self.channel_layer.group_send(
                self.room_group_name,
                {
                    "type": "call_ended",
                    "username": self.user.username,
                    "sender_channel": self.channel_name,
                },
            )

        else:
            await self.send_json({
                "type": "error",
                "message": f"Unknown message type: {message_type}",
            })

    # ==========================================
    # CHAT MESSAGE HANDLER
    # ==========================================

    async def chat_message(self, event):
        await self.send_json({
            "type": "chat",
            "message": event["message"],
            "username": event["username"],
            "time": event.get("time"),
        })

    # ==========================================
    # ONLINE/OFFLINE STATUS HANDLER
    # ==========================================

    async def status_message(self, event):
        # Do not send the current user's own status back to them.
        if event.get("sender_channel") == self.channel_name:
            return

        is_online = event["status"] == "online"

        await self.send_json({
            "type": "status",
            "username": event["username"],
            "status": event["status"],
            "is_online": is_online,
        })

    # ==========================================
    # WEBRTC OFFER HANDLER
    # ==========================================

    async def webrtc_offer(self, event):
        if event.get("sender_channel") == self.channel_name:
            return

        await self.send_json({
            "type": "offer",
            "offer": event["offer"],
            "username": event["username"],
        })

    # ==========================================
    # WEBRTC ANSWER HANDLER
    # ==========================================

    async def webrtc_answer(self, event):
        if event.get("sender_channel") == self.channel_name:
            return

        await self.send_json({
            "type": "answer",
            "answer": event["answer"],
            "username": event["username"],
        })

    # ==========================================
    # WEBRTC ICE HANDLER
    # ==========================================

    async def webrtc_ice(self, event):
        if event.get("sender_channel") == self.channel_name:
            return

        await self.send_json({
            "type": "ice",
            "candidate": event["candidate"],
            "username": event["username"],
        })

    # ==========================================
    # END-CALL HANDLER
    # ==========================================

    async def call_ended(self, event):
        if event.get("sender_channel") == self.channel_name:
            return

        await self.send_json({
            "type": "end_call",
            "username": event["username"],
        })

    # ==========================================
    # JSON HELPER
    # ==========================================

    async def send_json(self, data):
        await self.send(
            text_data=json.dumps(data)
        )

    # ==========================================
    # CHECK CONVERSATION
    # ==========================================

    @database_sync_to_async
    def conversation_exists(self):
        return Conversation.objects.filter(
            id=self.conversation_id
        ).exists()

    # ==========================================
    # CHECK PARTICIPANT
    # ==========================================

    @database_sync_to_async
    def is_participant(self):
        return ConversationParticipant.objects.filter(
            conversation_id=self.conversation_id,
            user=self.user,
        ).exists()

    # ==========================================
    # SAVE CHAT MESSAGE
    # ==========================================

    @database_sync_to_async
    def save_message(self, message_text):
        conversation = Conversation.objects.get(
            id=self.conversation_id
        )

        Message.objects.create(
            conversation=conversation,
            sender=self.user,
            message=message_text,
        )

    # ==========================================
    # SET USER ONLINE
    # ==========================================

    @database_sync_to_async
    def set_online(self):
        profile, created = UserProfile.objects.get_or_create(
            user=self.user
        )

        profile.is_online = True
        profile.save(update_fields=["is_online"])

    # ==========================================
    # SET USER OFFLINE
    # ==========================================

    @database_sync_to_async
    def set_offline(self):
        profile, created = UserProfile.objects.get_or_create(
            user=self.user
        )

        profile.is_online = False
        profile.save(update_fields=["is_online"])