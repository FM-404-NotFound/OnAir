# 외부 패키지
import os
import shutil

# 내부 패키지
from config import STREAMING_CHANNELS, PLAYLIST_DIR, HLS_DIR
from logger import log


######################  채널 추가시 폴더 구성  ######################
def dir_setup(channel_name):
  channel_path = os.path.join(STREAMING_CHANNELS, channel_name)
  playlist_path = os.path.join(channel_path, PLAYLIST_DIR)
  hls_path = os.path.join(channel_path, HLS_DIR)

  os.makedirs(channel_path, exist_ok=True)
  os.makedirs(playlist_path, exist_ok=True)
  create_or_clear_directory(hls_path)

  if os.path.exists(os.path.join(channel_path, 'dummy.m3u8')):
    os.remove(os.path.join(channel_path, 'dummy.m3u8'))
  return channel_path, playlist_path, hls_path

######################  기존 디렉토리가 존재하면 초기화  ######################
def create_or_clear_directory(path):
  if os.path.exists(path):
    shutil.rmtree(path)
  os.makedirs(path, exist_ok=True)

######################  서버 종료시 디렉토리 정리  ######################
def clear_hls_path(channel):
  if os.path.exists(channel['hls_path']):
    log.info(f"HLS path 정리 [{channel['hls_path']}]")
    shutil.rmtree(channel['hls_path'])
  if os.path.exists(os.path.join(channel['channel_path'], 'index.m3u8')):
    os.remove(os.path.join(channel["channel_path"], "index.m3u8"))


######################  파일 유효성 검사  ######################
def validate_file(file_path, valid_extension=".mp3"):
  if not os.path.exists(file_path):
    log.error(f"파일이 존재하지 않습니다. [{file_path}]")
    return False

  if not os.path.isfile(file_path):
    log.error(f"파일이 아닙니다. [{file_path}]")
    return False

  if not file_path.lower().endswith(valid_extension):
    log.error(f"잘못된 파일 형식입니다 [{file_path}]")
    return False

  return True