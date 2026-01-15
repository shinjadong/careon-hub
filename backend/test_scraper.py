"""
Scrapy 통합 테스트 스크립트
"""

import sys
from pathlib import Path

# scraper 모듈 경로 추가
scraper_path = Path(__file__).parent / "app" / "core" / "scraper"
sys.path.insert(0, str(scraper_path))

from scraper_manager import ScraperManager


def test_list_spiders():
    """스파이더 목록 테스트"""
    print("=" * 60)
    print("Scrapy 스파이더 목록 테스트")
    print("=" * 60)

    manager = ScraperManager(adb_enabled=False)
    spiders = manager.list_spiders()

    print(f"\n✅ 총 {len(spiders)}개의 스파이더 발견:")
    for spider in spiders:
        info = manager.get_spider_info(spider)
        if info:
            print(f"  - {spider}: {info['description']}")
            print(f"    타입: {info['type']}")
            if info.get('requires_args'):
                print(f"    필수 인자: {info.get('args', [])}")
    print()


def test_spider_info():
    """스파이더 상세 정보 테스트"""
    print("=" * 60)
    print("스파이더 상세 정보")
    print("=" * 60)

    manager = ScraperManager(adb_enabled=False)

    test_spiders = ["naver_news", "mobile_web", "dynamic_content"]

    for spider_name in test_spiders:
        info = manager.get_spider_info(spider_name)
        if info:
            print(f"\n📋 {spider_name}:")
            print(f"   설명: {info['description']}")
            print(f"   타입: {info['type']}")
            print(f"   인자 필요: {info['requires_args']}")
            if info.get('args'):
                print(f"   인자: {', '.join(info['args'])}")


def main():
    print("\n🚀 CareOn Hub - Scrapy 통합 테스트\n")

    try:
        test_list_spiders()
        test_spider_info()

        print("=" * 60)
        print("✅ 모든 테스트 완료!")
        print("=" * 60)
        print("\n사용 예시:")
        print("  cd backend/app/core/scraper")
        print("  scrapy crawl naver_news")
        print("  scrapy crawl mobile_web -a url=https://m.naver.com")
        print()

    except Exception as e:
        print(f"❌ 테스트 실패: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
