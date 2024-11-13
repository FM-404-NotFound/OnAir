import json
import logging
import threading

import typecast
from config import max_story_count
from instance import channel_manager, producer
from music_downloader import download_from_keyword

# Lock 객체를 사용하여 동기화
queue_lock = threading.Lock()


def extract_message_info(msg):
    """메시지에서 필요한 정보를 추출하는 헬퍼 함수"""
    try:
        value = json.loads(msg.value().decode('utf-8'))
        channel_id = msg.key().decode('utf-8')
        return channel_id, value
    except Exception as e:
        logging.error(f"Error extracting message info: {e}")
        return None, None


def handle_content(msg, content_type):
    """공통 로직 처리 함수"""
    channel_id, value = extract_message_info(msg)
    if channel_id is None:
        return

    logging.info(f"Received {content_type} reply {value}, {channel_id}")

    if channel_id not in channel_manager.channels:
        logging.info(f"Channel {channel_id} not found. Skipping playback.")
        return

    # TTS로 노래를 다운받고 경로를 반환받음
    file_path = typecast.get_tts(value, channel_id, content_type)
    if file_path is None:
        logging.info(f"No {content_type} file found. Skipping playback.")
        return

    with queue_lock:
        channel = channel_manager.channels[channel_id]
        channel.playback_queue.add_content(content_type, file_path)

    channel.playback_queue.log_queues()


def handle_weather(msg):
    handle_content(msg, "weather")


def handle_news(msg):
    handle_content(msg, "news")


def handle_story(msg):
    """Kafka 메시지를 받아 사연에 TTS와 음악을 추가하여 처리하는 콜백 함수"""
    channel_id, value = extract_message_info(msg)
    if channel_id is None:
        return

    logging.info(f"Received story reply {value}, {channel_id}")

    if channel_id not in channel_manager.channels:
        logging.info(f"Channel {channel_id} not found. Skipping playback.")
        return

    # story가 5개 이상일 경우 답변 생성 X
    if len(channel_manager.channels[channel_id].playback_queue.queues["story"]) >= max_story_count:
        logging.warning(f"Queue for story {channel_id} is full. Skipping.")
        return

    # TTS 파일 생성
    tts_file_path = process_tts(value, channel_id)
    if not tts_file_path:
        return

    # storyMusic 값 검증 후 음악 다운로드
    music_file_info = process_music(value, channel_id)
    if not music_file_info:
        return

    # TTS와 음악을 모두 처리했으므로 큐에 추가
    with queue_lock:
        channel = channel_manager.channels[channel_id]
        channel.playback_queue.add_content("story", tts_file_path)
        channel.playback_queue.add_content("story", music_file_info)

    logging.info(f"Story and music processed successfully. TTS info: {tts_file_path}, Music info: {music_file_info}")
    channel.playback_queue.log_queues()


def process_tts(value, channel_id):
    """TTS 생성 처리"""
    try:
        tts_file_info = typecast.get_tts(value, channel_id, "story")
        if not tts_file_info:
            logging.info("No TTS file found. Skipping playback.")
            return None
        return tts_file_info
    except Exception as e:
        logging.error(f"Error generating TTS: {e}")
        return None


def process_music(value, channel_id):
    """음악 다운로드 처리"""
    story_music = value.get('storyMusic', {})
    music_title = story_music.get('playListMusicTitle')
    music_artist = story_music.get('playListMusicArtist')

    if not music_title or not music_artist:
        logging.error(
            "Missing required 'playListMusicTitle' or 'playListMusicArtist' in storyMusic. Skipping music download.")
        return None

    try:
        music_file_info = download_from_keyword(music_title, music_artist, channel_id, "story")
        if not music_file_info:
            logging.info("No music file found. Skipping playback.")
            return None
        return music_file_info
    except Exception as e:
        logging.error(f"Error downloading music: {e}")
        return None


class ContentProvider:

    def __init__(self, channel, playback_queue):
        self.channel = channel
        self.playback_queue = playback_queue

    def request_contents(self, content_type):
        """contents_request_topic으로 요청 전송"""
        value = {
            "channelInfo": {
                "isDefault": self.channel.is_default,
                "ttsEngine": self.channel.tts_engine,
                "personality": self.channel.personality,
                "newsTopic": self.channel.news_topic
            },
            "contentType": content_type
        }
        message_value = json.dumps(value)
        producer.send_message('contents_request_topic',
                              key=self.channel.channel_id.encode('utf-8'),
                              value=message_value.encode('utf-8'))

    def stop(self):
        """ContentProvider 종료"""
        logging.info(f"Stopping ContentProvider for channel {self.channel.channel_id}")
