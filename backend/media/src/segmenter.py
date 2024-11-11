import asyncio
import itertools
import os
import subprocess
import time
from threading import Lock

import aiofiles

from logger import log
from config import STREAMING_CHANNELS
from config import SEGMENT_DURATION, SEGMENT_LIST_SIZE, SEGMENT_UPDATE_INTERVAL, SEGMENT_UPDATE_SIZE


######################  파일 -ffmpeg-> 세그먼트  ######################
def generate_segment(hls_path, file_path, last_index):
  log.info(f'세그먼트 생성 시작 [{file_path}]')
  ffmpeg_command = [
    'ffmpeg',
    '-loglevel', 'info',
    '-i', file_path,
    '-c:a', 'aac',
    '-b:a', '128k',
    '-f', 'hls',
    '-hls_time', str(SEGMENT_DURATION),
    '-hls_list_size', '0',
    '-hls_segment_type', 'mpegts',
    '-hls_segment_filename', os.path.join(hls_path, f'segment_{last_index:04d}_%5d.ts'),
    os.path.join(STREAMING_CHANNELS, "channel_1/dummy.m3u8")
  ]

  process = subprocess.Popen(
      ffmpeg_command,
      stdout=subprocess.PIPE,
      stderr=subprocess.PIPE,
      universal_newlines=True,
      encoding='utf-8'
  )

  stdout, stderr = process.communicate()
  if process.returncode == 0:
    log.info(f"세그먼트 생성 완료 [{file_path}]")
  else:
    log.error(f"세그먼트 생성 실패 [{file_path}\n{stderr}]")
  return (last_index+1)


######################  m3u8 작성  ######################
async def write_m3u8(channel, m3u8_path, segments):
  m3u8_lines = [
    "#EXTM3U\n",
    "#EXT-X-VERSION:3\n",
    f"#EXT-X-TARGETDURATION:{SEGMENT_DURATION}\n",
  ]
  # channel['queue'].dequeue(SEGMENT_LIST_SIZE)
  m3u8_lines.extend(get_m3u8_seg_list(channel, segments))

  async with aiofiles.open(m3u8_path, "w") as f:
    await f.writelines(m3u8_lines)
  wait_time = (m3u8_lines[3].strip())[8:-1]
  return float(wait_time)


###################### m3u8 작성: segment list 가져오기 ######################
def get_m3u8_seg_list(channel, segments):
  playlist_lines = []
  previous_index = segments[0][0]
  for index, number in segments:
    if previous_index != index:
      ### 다음 파일 전환, duration 수정
      duration = get_audio_duration(channel, playlist_lines[-1].strip())
      playlist_lines[-2] = playlist_lines[-2].replace(str(SEGMENT_DURATION), str(duration))
      ### discontinuity 추가
      playlist_lines.append("#EXT-X-DISCONTINUITY\n")

    # 세그먼트 리스트 작성
    playlist_lines.append(f"#EXTINF:{SEGMENT_DURATION},\n")
    playlist_lines.append(f"segment_{index:04d}_{number:05d}.ts\n")
    previous_index = index
  return playlist_lines


###################### 세그먼트 리스트 업데이트  ######################
async def update_m3u8(channel):
  channel_path = channel['channel_path']
  m3u8_path = os.path.join(channel_path, "index.m3u8")
  temp_m3u8_path = os.path.join(channel_path, "index_temp.m3u8")
  await asyncio.sleep(SEGMENT_UPDATE_INTERVAL)

  while True:
    # 루프 시작 시간 기록
    start_time = time.perf_counter()

    # 저장할 세그먼트 리스트 조회
    segments = channel['queue'].get_buffer()
    segments.extend(channel['queue'].dequeue(SEGMENT_UPDATE_SIZE))
      
    # index_temp.m3u8 작성
    first_seg_length = await write_m3u8(channel, temp_m3u8_path, segments)
    
    # 파일 교체
    try:
      os.replace(temp_m3u8_path, m3u8_path)
      log.info("index.m3u8 업데이트 완료")
    except PermissionError as e:
      await asyncio.sleep(0.2)  # 잠시 대기 후 재시도

    # 루프 종료 시간 기록
    end_time = time.perf_counter()
    execution_time = end_time - start_time

    # 남은 시간 계산하여 대기 (최소 대기 시간은 0으로 설정)
    sleep_time = first_seg_length - execution_time if first_seg_length > execution_time else 0
    print(f'함수 소요 시간 [{execution_time}]')
    print(f'세그먼트 시간 [{first_seg_length}]')
    print(f'wait to [{sleep_time}]')
    await asyncio.sleep(sleep_time)


######################  주어진 파일의 길이(초)를 가져오는 함수  ######################
def get_audio_duration(channel, segment_name):
  segment_path = os.path.join(channel['hls_path'], segment_name)
  try:
    result = subprocess.run(
      [
        'ffprobe',
        '-v', 'error',
        '-show_entries', 'format=duration',
        '-of', 'default=noprint_wrappers=1:nokey=1',
        segment_path
      ],
      stdout=subprocess.PIPE,
      stderr=subprocess.PIPE,
      universal_newlines=True,
      text=True,
      encoding='utf-8'
    )
    return float(result.stdout.strip())
  except Exception as e:
    log.error(f"파일 길이 가져오기 실패: {e}")
    return None