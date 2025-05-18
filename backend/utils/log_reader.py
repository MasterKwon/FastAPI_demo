"""
로그 파일을 읽고 파싱하는 유틸리티
"""
import os
from datetime import datetime
from typing import List, Dict, Any
from backend.core.config import settings

class LogReader:
    def __init__(self, log_dir: str = None):
        self.log_dir = log_dir or settings.LOG_DIR

    def get_log_files(self) -> List[str]:
        """로그 파일 목록 조회"""
        log_files = []
        for file in os.listdir(self.log_dir):
            if file.endswith('.log') and file.startswith(f"{settings.SERVICE_NAME}_"):
                log_files.append(os.path.join(self.log_dir, file))
        return sorted(log_files, reverse=True)

    def parse_log_line(self, line: str) -> Dict[str, Any]:
        """로그 라인 파싱"""
        try:
            # 로그 형식: [2024-03-14 10:30:45] INFO [name:123] [module] - message
            parts = line.strip().split('] ')
            if len(parts) < 4:
                return None

            timestamp = parts[0].strip('[')
            level = parts[1]
            location = parts[2].strip('[').strip(']')
            module = parts[3].strip('[').strip(']')
            message = '] '.join(parts[4:]).strip('- ').strip()

            return {
                "timestamp": timestamp,
                "level": level,
                "location": location,
                "module": module,
                "message": message
            }
        except Exception:
            return None

    def read_logs(
        self,
        level: str = "INFO",
        limit: int = 100,
        skip: int = 0
    ) -> List[Dict[str, Any]]:
        """로그 조회"""
        logs = []
        log_files = self.get_log_files()

        for log_file in log_files:
            if len(logs) >= limit:
                break

            try:
                with open(log_file, 'r', encoding='utf-8') as f:
                    for line in f:
                        log_entry = self.parse_log_line(line)
                        if log_entry and (level == "ALL" or log_entry["level"] == level):
                            if skip > 0:
                                skip -= 1
                                continue
                            logs.append(log_entry)
                            if len(logs) >= limit:
                                break
            except Exception as e:
                print(f"Error reading log file {log_file}: {str(e)}")

        return logs 