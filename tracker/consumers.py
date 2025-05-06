import json
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async
from django.contrib.auth.models import User
from .models import UserProfile

class StatsConsumer(AsyncWebsocketConsumer):
    GROUP_NAME = "live_stats"

    async def connect(self):
        # Check if user is authenticated
        if self.scope["user"].is_authenticated:
            await self.channel_layer.group_add(
                self.GROUP_NAME,
                self.channel_name
            )
            await self.accept()
            # Send initial full list of stats upon connection
            await self.send_all_stats()
        else:
            # Reject unauthenticated connections
            await self.close()

    async def disconnect(self, close_code):
        # Leave the group
        await self.channel_layer.group_discard(
            self.GROUP_NAME,
            self.channel_name
        )

    # Receive message from WebSocket (optional, we might not need client-to-server messages for this feature)
    async def receive(self, text_data):
        # Example: text_data_json = json.loads(text_data)
        # message = text_data_json['message']
        # We likely don't need to handle incoming messages for just broadcasting stats
        pass

    # Receive message from the channel group (called when group_send is used)
    async def stats_update(self, event):
        stats_data = event['stats_data']

        # Send message to WebSocket
        await self.send(text_data=json.dumps({
            'type': 'stats_update',
            'stats': stats_data
        }))

    @database_sync_to_async
    def _get_all_user_stats(self):
        """Fetches username and total_points for all active users."""
        profiles = UserProfile.objects.select_related('user').filter(user__is_active=True).order_by('-total_points')
        stats_list = [
            {"username": profile.user.username, "points": profile.total_points}
            for profile in profiles
        ]
        return stats_list

    async def send_all_stats(self):
        """Sends the current stats of all users to this specific client."""
        all_stats = await self._get_all_user_stats()
        await self.send(text_data=json.dumps({
            'type': 'full_stats_load', # Different type for initial load
            'stats': all_stats
        }))

# Helper function to trigger broadcast from outside the consumer (e.g., from a view or signal)
async def broadcast_stats_update():
    from channels.layers import get_channel_layer
    channel_layer = get_channel_layer()

    @database_sync_to_async
    def _get_stats():
        profiles = UserProfile.objects.select_related('user').filter(user__is_active=True).order_by('-total_points')
        return [
            {"username": profile.user.username, "points": profile.total_points}
            for profile in profiles
        ]

    latest_stats = await _get_stats()

    await channel_layer.group_send(
        StatsConsumer.GROUP_NAME,
        {
            'type': 'stats_update', # This corresponds to the method name in the consumer
            'stats_data': latest_stats
        }
    ) 