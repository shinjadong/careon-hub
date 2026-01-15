"""
CareOn Hub - Scrapy Pipelines
스크래핑한 데이터를 처리하고 ADB/Supabase와 통합
"""

import os
import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Any, Dict

from itemadapter import ItemAdapter

logger = logging.getLogger(__name__)


class CareonScraperPipeline:
    """기본 데이터 정제 및 검증 파이프라인"""

    def process_item(self, item: Dict[str, Any], spider) -> Dict[str, Any]:
        adapter = ItemAdapter(item)

        # 타임스탬프 추가
        adapter["scraped_at"] = datetime.utcnow().isoformat()
        adapter["spider_name"] = spider.name

        # 빈 필드 제거
        cleaned_item = {k: v for k, v in adapter.asdict().items() if v}

        logger.info(f"Processed item from {spider.name}: {cleaned_item.get('title', 'N/A')}")
        return cleaned_item


class ADBIntegrationPipeline:
    """
    ADB 디바이스 제어와 통합
    스크래핑한 데이터를 모바일 디바이스로 전달하거나
    디바이스 상태를 기록
    """

    def __init__(self):
        self.adb_enabled = False
        self.device_manager = None

    def open_spider(self, spider):
        """스파이더 시작 시 ADB 연결"""
        try:
            if spider.settings.get("ADB_ENABLED", False):
                # ADB 모듈 동적 임포트
                import sys
                adb_path = spider.settings.get("ADB_DEVICES_PATH")
                if adb_path and os.path.exists(adb_path):
                    sys.path.insert(0, adb_path)
                    from device_tools.adb_enhanced import ADBDeviceManager

                    self.device_manager = ADBDeviceManager()
                    self.adb_enabled = True
                    logger.info("ADB Integration enabled")
                else:
                    logger.warning(f"ADB path not found: {adb_path}")
        except Exception as e:
            logger.error(f"Failed to initialize ADB: {e}")

    def process_item(self, item: Dict[str, Any], spider) -> Dict[str, Any]:
        """ADB 디바이스로 데이터 전송 또는 처리"""
        if not self.adb_enabled:
            return item

        try:
            # 스크래핑한 URL을 디바이스에서 열기 (선택사항)
            if "url" in item and hasattr(spider, "open_on_device"):
                url = item["url"]
                # devices = self.device_manager.list_devices()
                # if devices:
                #     self.device_manager.open_url(devices[0], url)
                logger.info(f"ADB: Would open {url} on device")

            # 디바이스 메타데이터 추가
            item["adb_processed"] = True

        except Exception as e:
            logger.error(f"ADB processing error: {e}")
            item["adb_error"] = str(e)

        return item

    def close_spider(self, spider):
        """스파이더 종료 시 ADB 연결 해제"""
        if self.device_manager:
            logger.info("Closing ADB connections")
            self.device_manager = None


class SupabasePipeline:
    """
    Supabase 데이터베이스에 스크래핑한 데이터 저장
    """

    def __init__(self):
        self.supabase_enabled = False
        self.client = None
        self.table_name = "scraped_data"

    def open_spider(self, spider):
        """스파이더 시작 시 Supabase 연결"""
        try:
            if spider.settings.get("SUPABASE_ENABLED", False):
                from supabase import create_client
                import os

                # 환경변수 로드 (.env 파일)
                from dotenv import load_dotenv
                env_path = Path(__file__).parents[4] / ".env"
                load_dotenv(env_path)

                supabase_url = os.getenv("SUPABASE_URL")
                supabase_key = os.getenv("SUPABASE_ANON_KEY")

                if supabase_url and supabase_key:
                    self.client = create_client(supabase_url, supabase_key)
                    self.table_name = spider.settings.get("SUPABASE_TABLE", "scraped_data")
                    self.supabase_enabled = True
                    logger.info(f"Supabase connected: {self.table_name}")
                else:
                    logger.warning("Supabase credentials not found")
        except Exception as e:
            logger.error(f"Failed to connect to Supabase: {e}")

    def process_item(self, item: Dict[str, Any], spider) -> Dict[str, Any]:
        """Supabase에 데이터 저장"""
        if not self.supabase_enabled:
            return item

        try:
            # Supabase에 삽입
            data = dict(item)
            response = self.client.table(self.table_name).insert(data).execute()

            logger.info(f"Saved to Supabase: {item.get('title', 'N/A')}")
            item["supabase_id"] = response.data[0]["id"] if response.data else None

        except Exception as e:
            logger.error(f"Supabase insert error: {e}")
            item["supabase_error"] = str(e)

        return item


class JSONFilePipeline:
    """
    로컬 JSON 파일로 백업 저장
    """

    def __init__(self):
        self.output_dir = None
        self.files = {}

    def open_spider(self, spider):
        """출력 디렉토리 생성"""
        output_path = spider.settings.get("DATA_OUTPUT_PATH", "./data/scraped")
        self.output_dir = Path(output_path)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        logger.info(f"JSON output directory: {self.output_dir}")

    def process_item(self, item: Dict[str, Any], spider) -> Dict[str, Any]:
        """JSON 파일로 저장"""
        try:
            spider_name = spider.name
            if spider_name not in self.files:
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                filename = self.output_dir / f"{spider_name}_{timestamp}.jsonl"
                self.files[spider_name] = open(filename, "a", encoding="utf-8")
                logger.info(f"Created output file: {filename}")

            line = json.dumps(dict(item), ensure_ascii=False) + "\n"
            self.files[spider_name].write(line)

        except Exception as e:
            logger.error(f"JSON file write error: {e}")

        return item

    def close_spider(self, spider):
        """파일 닫기"""
        for file in self.files.values():
            file.close()
        logger.info("Closed all output files")
