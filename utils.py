"""
Voice Taboo 게임 유틸리티 함수들
"""
import json
import os
import re
import time
import wave
from typing import List, Optional, Tuple

import numpy as np
import sounddevice as sd

from config import (
    SAMPLE_RATE, CHANNELS, RECORD_SECONDS, 
    TABOO_JSON_PATH, FALLBACK_TABOO_BANK
)


def load_taboo_bank(path: str) -> List[dict]:
    """JSON 파일에서 taboo 단어 목록을 로드"""
    try:
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
        cleaned: List[dict] = []
        for item in data:
            if not isinstance(item, dict):
                continue
            t = item.get("target")
            forb = item.get("forbidden")
            if not isinstance(t, str) or not isinstance(forb, list):
                continue
            forb2 = [str(x).strip() for x in forb if str(x).strip()]
            cleaned.append({"target": t.strip(), "forbidden": forb2})
        if not cleaned:
            return FALLBACK_TABOO_BANK
        return cleaned
    except Exception:
        return FALLBACK_TABOO_BANK


def save_wav_from_array(filename: str, audio: np.ndarray, samplerate: int = SAMPLE_RATE):
    """numpy 배열을 WAV 파일로 저장"""
    if audio.dtype != np.int16:
        if audio.dtype not in (np.float32, np.float64):
            audio = audio.astype(np.float32)
        audio = np.clip(audio, -1.0, 1.0)
        audio = (audio * 32767.0).astype(np.int16)
    with wave.open(filename, 'wb') as wf:
        wf.setnchannels(CHANNELS)
        wf.setsampwidth(2)
        wf.setframerate(samplerate)
        wf.writeframes(audio.tobytes())


def audio_array_to_wav_bytes(audio: np.ndarray, samplerate: int = SAMPLE_RATE) -> bytes:
    """numpy 배열을 WAV 바이너리 데이터로 변환 (파일 저장 없이)"""
    import io
    
    print(f"오디오 변환 시작: {len(audio)} 샘플, {samplerate}Hz")
    
    # 오디오 데이터 정규화 및 증폭
    if audio.dtype != np.int16:
        if audio.dtype not in (np.float32, np.float64):
            audio = audio.astype(np.float32)
        
        # 정규화 범위 확인
        audio_max = np.max(np.abs(audio))
        audio_rms = np.sqrt(np.mean(audio**2))
        print(f"정규화 전 최대값: {audio_max:.6f}, RMS: {audio_rms:.6f}")
        
        if audio_max > 0:
            # 매우 적극적인 증폭 (낮은 품질 오디오 문제 해결)
            target_level = 0.8  # 더 높은 목표 레벨
            if audio_max < target_level:
                amplification = min(50.0, target_level / audio_max)  # 최대 50배 증폭
                audio = audio * amplification
                print(f"오디오 증폭: {amplification:.2f}배")
            
            # 하드 클리핑
            audio = np.clip(audio, -1.0, 1.0)
            
            # 노이즈 게이트 완전 제거 (모든 신호 보존)
            # threshold = 0.0005
            # audio = np.where(np.abs(audio) < threshold, 0, audio)
            
            # 16비트로 변환
            audio = (audio * 32767.0).astype(np.int16)
            
            # 최종 상태 확인
            final_max = np.max(np.abs(audio))
            print(f"변환 후 16비트 최대값: {final_max}")
        else:
            print("경고: 오디오 데이터가 무음입니다.")
            # 완전 무음이면 짧은 더미 신호 생성 (Whisper 오류 방지)
            dummy_tone = np.sin(2 * np.pi * 440 * np.linspace(0, 0.1, int(0.1 * samplerate)))
            audio = (dummy_tone * 0.1 * 32767.0).astype(np.int16)
    
    # 메모리에서 WAV 파일 생성
    wav_buffer = io.BytesIO()
    with wave.open(wav_buffer, 'wb') as wf:
        wf.setnchannels(CHANNELS)
        wf.setsampwidth(2)
        wf.setframerate(samplerate)
        wf.writeframes(audio.tobytes())
    
    wav_buffer.seek(0)
    wav_data = wav_buffer.read()
    print(f"WAV 변환 완료: {len(wav_data)} bytes")
    
    return wav_data


def record_block(seconds: float = RECORD_SECONDS, samplerate: int = SAMPLE_RATE) -> np.ndarray:
    """지정된 시간 동안 오디오를 녹음"""
    audio = sd.rec(int(seconds * samplerate), samplerate=samplerate, channels=CHANNELS, dtype='float32')
    sd.wait()
    return audio.reshape(-1)


def start_recording(samplerate: int = SAMPLE_RATE) -> sd.InputStream:
    """실시간 녹음 시작 (키를 누르는 동안)"""
    # 마이크 테스트에서 잘 작동한 디바이스 22번 사용
    try:
        devices = sd.query_devices()
        # 마이크 테스트에서 성공한 디바이스 22 (Realtek HD Audio Mic input) 시도
        input_device = 22
        print(f"마이크 디바이스 {input_device} 사용 시도")
        
        device_info = sd.query_devices(input_device)
        print(f"디바이스 정보: {device_info}")  # 전체 정보 출력
        
    except Exception as e:
        print(f"디바이스 조회 오류: {e}")
        input_device = None
    
    stream = sd.InputStream(
        device=input_device,  # 테스트에서 성공한 디바이스 사용
        samplerate=samplerate,
        channels=CHANNELS,
        dtype='float32',
        blocksize=1024
    )
    stream.start()
    return stream


def stop_recording_and_get_audio(stream: sd.InputStream, duration: float) -> np.ndarray:
    """녹음 중단하고 오디오 데이터 반환"""
    try:
        print(f"녹음 중단 시작, 지속시간: {duration:.2f}초")
        
        # 녹음된 데이터 수집
        frames = []
        samples_per_frame = 1024
        expected_frames = max(1, int(duration * stream.samplerate / samples_per_frame))
        
        print(f"예상 프레임 수: {expected_frames}")
        
        # 실제 녹음된 데이터 읽기
        for i in range(expected_frames):
            try:
                data, overflowed = stream.read(samples_per_frame)
                if overflowed:
                    print(f"프레임 {i}: 오디오 버퍼 오버플로우")
                frames.append(data)
            except Exception as read_error:
                print(f"프레임 {i} 읽기 오류: {read_error}")
                break
        
        stream.stop()
        stream.close()
        
        if frames:
            audio = np.concatenate(frames, axis=0)
            print(f"수집된 오디오 샘플 수: {len(audio)}")
            
            # 오디오 레벨 확인 - 임계치 강화
            audio_level = np.max(np.abs(audio))
            audio_rms = np.sqrt(np.mean(audio**2))
            print(f"오디오 최대 레벨: {audio_level:.4f}, RMS: {audio_rms:.4f}")
            
            # 너무 조용하면 정적으로 판단하고 처리 거부
            if audio_level < 0.005 or audio_rms < 0.001:  # 임계치 강화
                print("경고: 오디오 레벨이 너무 낮습니다 (정적으로 판단). 더 크게 말해주세요.")
                return np.zeros(int(0.1 * SAMPLE_RATE))  # 매우 짧은 더미 데이터
            
            return audio.reshape(-1)
        else:
            print("경고: 녹음된 데이터가 없습니다.")
            return np.zeros(int(0.5 * SAMPLE_RATE))  # 0.5초 더미 데이터
            
    except Exception as e:
        print(f"녹음 중단 오류: {e}")
        try:
            stream.stop()
            stream.close()
        except:
            pass
        return np.zeros(int(0.5 * SAMPLE_RATE))


def check_violations(text: str, target: str, forbidden: List[str]) -> Tuple[Optional[str], bool]:
    """
    텍스트에서 금지어 및 목표어 위반을 검사
    
    Returns:
        Tuple[금지어_위반, 목표어_위반]
        - 금지어_위반: 위반된 금지어 문자열 또는 None
        - 목표어_위반: 목표어를 말했는지 여부 (bool)
    """
    text_l = text.lower()
    target_l = target.lower()
    tokens = text_l.split()
    token_set = set(tokens)
    
    # 1. 목표어 검사 (우선순위 높음)
    target_violation = False
    if target_l in token_set or target_l in text_l:
        target_violation = True
    
    # 2. 금지어 검사
    forbidden_violation = None
    for w in forbidden:
        w_l = w.lower().strip()
        if not w_l:
            continue
        if w_l in token_set:
            forbidden_violation = w
            break
        # 한글/붙임표 등 토큰 경계가 모호할 수 있으니 보조 검사
        if w_l in text_l:
            forbidden_violation = w
            break
    
    return forbidden_violation, target_violation


def extract_guess_token(text: str) -> str:
    """AI 응답에서 [[word]] 토큰 추출 (한글 지원 강화)"""
    # 1) [[단어]] 형태의 토큰 찾기
    m = re.search(r"\[\[\s*([가-힣\w]+)\s*\]\]", text)
    if m:
        return m.group(1).strip()
    
    # 2) 한글만 있는 [[한글]] 형태도 확인
    m2 = re.search(r"\[\[\s*([가-힣]+)\s*\]\]", text)
    if m2:
        return m2.group(1).strip()
    
    return ""
