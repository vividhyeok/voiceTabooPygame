#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
korcen.py의 모든 비속어 패턴을 banned_keywords.txt로 변환하는 스크립트
"""

import korcen

def convert_to_txt():
    """korcen.py의 모든 비속어 패턴을 텍스트 파일로 변환"""
    try:
        # korcen.py의 모든 비속어 패턴 리스트들을 모음
        all_patterns = []
        
        # 각 카테고리의 패턴들을 추가
        if hasattr(korcen, 'GENERAL_PROFANITY_PATTERNS'):
            all_patterns.extend(korcen.GENERAL_PROFANITY_PATTERNS)
        if hasattr(korcen, 'MINOR_PROFANITY_PATTERNS'):
            all_patterns.extend(korcen.MINOR_PROFANITY_PATTERNS)
        if hasattr(korcen, 'SEXUAL_PROFANITY_PATTERNS'):
            all_patterns.extend(korcen.SEXUAL_PROFANITY_PATTERNS)
        if hasattr(korcen, 'BELITTLE_PROFANITY_PATTERNS'):
            all_patterns.extend(korcen.BELITTLE_PROFANITY_PATTERNS)
        if hasattr(korcen, 'RACE_PROFANITY_PATTERNS'):
            all_patterns.extend(korcen.RACE_PROFANITY_PATTERNS)
        if hasattr(korcen, 'PARENT_PROFANITY_PATTERNS'):
            all_patterns.extend(korcen.PARENT_PROFANITY_PATTERNS)
        if hasattr(korcen, 'JAPANESE_PROFANITY_PATTERNS'):
            all_patterns.extend(korcen.JAPANESE_PROFANITY_PATTERNS)
        if hasattr(korcen, 'CHINESE_PROFANITY_PATTERNS'):
            all_patterns.extend(korcen.CHINESE_PROFANITY_PATTERNS)
        if hasattr(korcen, 'SPECIAL_PROFANITY_PATTERNS'):
            all_patterns.extend(korcen.SPECIAL_PROFANITY_PATTERNS)
        if hasattr(korcen, 'POLITICS_PROFANITY_PATTERNS'):
            all_patterns.extend(korcen.POLITICS_PROFANITY_PATTERNS)
        if hasattr(korcen, 'EXACT_MATCH_PROFANITY'):
            all_patterns.extend(korcen.EXACT_MATCH_PROFANITY)
        
        # 중복 제거
        unique_patterns = list(set(all_patterns))
        
        with open('banned_keywords.txt', 'w', encoding='utf-8') as f:
            for word in unique_patterns:
                if word.strip():  # 빈 문자열 제외
                    f.write(word.strip() + '\n')
        
        print(f"성공: {len(unique_patterns)}개의 비속어 패턴을 banned_keywords.txt로 변환했습니다.")
        
    except Exception as e:
        print(f"오류 발생: {e}")

if __name__ == "__main__":
    convert_to_txt()