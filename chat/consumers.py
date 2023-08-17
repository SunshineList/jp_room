import json
import logging

from asgiref.sync import async_to_sync
from channels.generic.websocket import WebsocketConsumer

logger = logging.getLogger(__name__)


class BasicConsumer(WebsocketConsumer):

    def connect(self):
        self.room_name = self.scope['url_route']['kwargs']['room_name']
        self.room_group_name = 'chat_%s' % self.room_name

        print("channel_name", self.channel_name, "room_name", self.room_name)

        async_to_sync(self.channel_layer.group_add)(
            self.room_group_name,
            self.channel_name
        )

        self.accept()

    def disconnect(self, close_code):
        async_to_sync(self.channel_layer.group_discard)(
            self.room_group_name,
            self.channel_name
        )

        # Receive message from WebSocket

    def send_group(self, group_name, data):
        async_to_sync(self.channel_layer.group_send)(  # 发送到房间分组
            group_name, data
        )


class CommonConsumer(BasicConsumer):
    """ 一般websocket应用"""

    def connect(self):
        self.room_name = self.scope['url_route']['kwargs']['room_name']
        self.room_group_name = '%s' % self.room_name

        async_to_sync(self.channel_layer.group_add)(
            self.room_group_name,
            self.channel_name
        )
        self.accept()

    def receive(self, text_data=None, bytes_data=None):
        try:
            msg = json.loads(text_data)
        except:
            msg = text_data
        self.send_group(self.room_group_name,
                        {'type': 'message', 'msg': msg, 'sender_channel_name': self.channel_name})

    def message(self, event):
        """处理消息 handle部分"""
        message = event['msg']
        print(message)
        try:
            msg = json.dumps(message)
        except:
            msg = message
        if self.channel_name != event.get('sender_channel_name'):  # 排除掉客户端发送的信息
            self.send(text_data=msg)
