import json
import logging
import os
import time
import uuid
from datetime import datetime
from pathlib import Path

import requests

import config
from path_util import get_medias_path

# Actor 별 지원하는 emotion presets 설정
ACTOR_EMOTIONS = {
    "세나": [
        "tonemid-1", "tonemid-2", "tonemid-3", "tonemid-4",
        "normal-1", "normal-2", "normal-3", "normal-4",
        "happy-1", "happy-2", "happy-3",
        "sad-1", "sad-2", "sad-3", "sad-4",
        "angry-1", "angry-2", "angry-3"
    ],
    "제롬": ["normal-1", "normal-2", "normal-3", "normal-4"],
    "현지": ["normal-1", "normal-2", "normal-3", "normal-4"],
    "은빈": ["happy-1", "happy-2", "soft-1", "soft-2", "normal-1", "normal-2"]
}

# Actor 별로 다른 API 토큰 설정
ACTOR_TOKENS = {
    "세나": config.sena_token,
    "제롬": config.jerome_token,
    "현지": config.hyeonji_token,
    "은빈": config.eunbin_token
}

# Actor 별 actor_id 설정
ACTOR_IDS = {
    "세나": config.sena_actor_id,
    "제롬": config.jerome_actor_id,
    "현지": config.hyeonji_actor_id,
    "은빈": config.eunbin_actor_id
}


# 기본값 설정 함수
def validate_value(value):
    # typecast 내부에서 값을 추출하도록 수정
    typecast = value.get("typecast", {})

    # 필수 값 검증
    if not typecast.get("text") or not isinstance(typecast["text"], str):
        raise ValueError("Text field is required")
    if not typecast.get("actor") or typecast["actor"] not in ACTOR_EMOTIONS:
        raise ValueError("Not Valid Actor")

    # 기본값 설정
    defaults = {
        "volume": 100,
        "speed_x": 1.0,
        "tempo": 1.0,
        "pitch": 0,
        "last_pitch": 0,
        "emotion_tone_preset": "normal-1"
    }

    # 숫자 범위 및 타입 검증
    def validate_int(key, min_val, max_val):
        try:
            val = int(typecast.get(key, defaults[key]))
            if val < min_val or val > max_val or isinstance(typecast.get(key), float):
                raise ValueError
        except (ValueError, TypeError):
            return defaults[key]
        return val

    def validate_float(key, min_val, max_val):
        try:
            val = float(typecast.get(key, defaults[key]))
            if val < min_val or val > max_val or isinstance(typecast.get(key), int):
                raise ValueError
        except (ValueError, TypeError):
            return defaults[key]
        return val

    # validate_int 및 validate_float 함수를 사용하여 필드 검증
    typecast["volume"] = validate_int("volume", 50, 200)
    typecast["speed_x"] = validate_float("speed_x", 0.5, 1.5)
    typecast["tempo"] = validate_float("tempo", 0.5, 2.0)
    typecast["pitch"] = validate_int("pitch", -12, 12)
    typecast["last_pitch"] = validate_int("last_pitch", -2, 2)

    # 감정 톤 검증 및 기본값 설정
    actor = typecast["actor"]
    emotion = typecast.get("emotion_tone_preset")
    if not emotion or emotion not in ACTOR_EMOTIONS[actor]:
        typecast["emotion_tone_preset"] = defaults["emotion_tone_preset"]

    # 결과 반환
    return typecast


# TTS 요청 함수
def get_tts(value, channel_id, content_type):
    url = "https://typecast.ai/api/speak"

    validated_value = validate_value(value)
    actor = validated_value["actor"]
    token = ACTOR_TOKENS[actor]
    actor_id = ACTOR_IDS[actor]

    payload = json.dumps({
        "actor_id": actor_id,
        "text": validated_value["text"],
        "lang": "ko-kr",
        "model_version": "latest",
        "xapi_hd": False,
        "xapi_audio_format": "mp3",
        "emotion_tone_preset": validated_value["emotion_tone_preset"],
        "volume": validated_value["volume"],
        "speed-x": validated_value["speed_x"],
        "tempo": validated_value["tempo"],
        "pitch": validated_value["pitch"],
        "last_pitch": validated_value["last_pitch"],
        "max_seconds": 60
    })

    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {token}"
    }

    # ## 운영용
    # response = requests.post(url, headers=headers, data=payload)
    #
    # if response.status_code == 200:
    #     response_data = response.json()
    #     speak_v2_url = response_data.get("result", {}).get("speak_v2_url")
    #     if speak_v2_url:
    #         speak_id = speak_v2_url.split('/')[-1]
    #         audio_info = download_audio(speak_id, token, channel_id, content_type)
    #         return audio_info
    #     else:
    #         logging.error(f"Failed to get speak_v2_url: {response_data}")
    # else:
    #     logging.error(f"Failed: {response.status_code}, {response.text}")

    ## 테스트용
    speak_id = "67321dc699ff75f1fc28b89a"
    audio_info = download_audio(speak_id, token, channel_id, content_type)
    return audio_info


def download_audio(speak_id, token, channel, content_type):
    url = f"https://typecast.ai/api/speak/v2/{speak_id}"
    headers = {
        "Authorization": f"Bearer {token}"
    }

    retries = 3
    for _ in range(retries):
        response = requests.get(url, headers=headers)
        logging.info(f"Typecast Response : {response.text}")

        if response.status_code == 200:
            data = response.json()
            result = data.get("result", {})
            status = result.get("status")

            if status == "done":
                audio_url = result.get("audio_download_url")
                if audio_url:
                    logging.info(f"Download URL: {audio_url}")
                    file_path = save_audio_file(audio_url, channel, content_type)
                    length = result.get("duration")
                    return {"file_path": file_path, "length": length}

            elif status == "progress":
                logging.info("Synthesis in progress. Waiting 5 seconds...")
                time.sleep(5)
            elif status == "failed":
                logging.error("Synthesis request failed.")
                return
            elif status == "started":
                logging.info("Synthesis has started but is not yet complete. Waiting 5 seconds...")
                time.sleep(5)
        else:
            logging.error(f"Failed to fetch the status, retrying... (Status Code: {response.status_code})")
            time.sleep(5)

    logging.error("Max retries reached. Could not download the audio.")


def save_audio_file(audio_url, channel_id, content_type):
    # medias 경로 설정
    current_dir = os.getcwd()
    medias_path = get_medias_path(current_dir)

    output_filepath = medias_path / channel_id / content_type

    # 디렉토리 생성 (존재하지 않으면)
    output_filepath.mkdir(parents=True, exist_ok=True)

    # 고유한 파일 이름 설정
    current_time = datetime.now().strftime("%Y%m%d_%H%M%S")
    # UUID 생성
    unique_id = uuid.uuid4()
    # 파일 이름 생성 (날짜 시간 + UUID)
    file_name = f"{current_time}_{unique_id}.mp3"
    output_file = output_filepath / file_name

    # 오디오 파일 저장
    response = requests.get(audio_url)
    if response.status_code == 200:
        with open(output_file, 'wb') as f:
            f.write(response.content)
        logging.info(f"Audio downloaded successfully as {str(output_file)}")
        return str(output_file)
    else:
        logging.error(f"Failed to download audio: {response.status_code}, {response.text}")
        return
