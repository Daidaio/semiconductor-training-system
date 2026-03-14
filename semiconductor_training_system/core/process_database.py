# -*- coding: utf-8 -*-
"""
製程參數資料庫 (Process Parameter Database)
基於論文 "Digital twin driven intelligent manufacturing" 的 Key Process Database 概念

功能:
1. 儲存最佳製程參數 (Optimal Process Parameters)
2. 定義參數容許範圍 (Tolerance Range)
3. 記錄參數來源 (Expert Knowledge / Simulation / Historical Data)
4. 提供參數查詢介面
"""

import sqlite3
from pathlib import Path
from typing import Dict, List, Optional
import json


class ProcessParameterDB:
    """製程參數資料庫"""

    def __init__(self, db_path: str = None):
        """
        初始化資料庫

        Args:
            db_path: 資料庫檔案路徑,預設為 data/process_parameters.db
        """
        if db_path is None:
            base_dir = Path(__file__).parent.parent
            data_dir = base_dir / "data"
            data_dir.mkdir(exist_ok=True)
            db_path = str(data_dir / "process_parameters.db")

        self.db_path = db_path
        self.conn = sqlite3.connect(db_path, check_same_thread=False)
        self.conn.row_factory = sqlite3.Row  # 允許字典式存取
        self._create_tables()
        self._initialize_default_parameters()

    def _create_tables(self):
        """建立資料表"""

        # 最佳製程參數表
        self.conn.execute("""
            CREATE TABLE IF NOT EXISTS optimal_parameters (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                process_name TEXT NOT NULL,
                parameter_name TEXT NOT NULL,
                optimal_value REAL NOT NULL,
                tolerance_min REAL NOT NULL,
                tolerance_max REAL NOT NULL,
                unit TEXT NOT NULL,
                source TEXT NOT NULL,
                description TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(process_name, parameter_name)
            )
        """)

        # 製程設定檔表 (組合多個參數成為一個完整設定)
        self.conn.execute("""
            CREATE TABLE IF NOT EXISTS process_profiles (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                profile_name TEXT NOT NULL UNIQUE,
                process_name TEXT NOT NULL,
                description TEXT,
                parameters TEXT NOT NULL,  -- JSON 格式儲存
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)

        # 歷史調整記錄表
        self.conn.execute("""
            CREATE TABLE IF NOT EXISTS parameter_history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                process_name TEXT NOT NULL,
                parameter_name TEXT NOT NULL,
                old_value REAL,
                new_value REAL,
                reason TEXT,
                operator TEXT,
                timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)

        self.conn.commit()

    def _initialize_default_parameters(self):
        """初始化預設參數 (基於 SECOM 資料集 + 專家知識)"""

        # 檢查是否已有資料
        cursor = self.conn.execute("SELECT COUNT(*) FROM optimal_parameters")
        count = cursor.fetchone()[0]

        if count > 0:
            return  # 已有資料,不重複初始化

        default_params = [
            # Lithography (光刻) 製程參數
            {
                "process_name": "lithography",
                "parameter_name": "cooling_flow",
                "optimal_value": 5.0,
                "tolerance_min": 4.8,
                "tolerance_max": 5.2,
                "unit": "L/min",
                "source": "expert",
                "description": "冷卻水流量 - 維持光學元件溫度穩定"
            },
            {
                "process_name": "lithography",
                "parameter_name": "lens_temp",
                "optimal_value": 23.0,
                "tolerance_min": 22.9,
                "tolerance_max": 23.1,
                "unit": "°C",
                "source": "expert",
                "description": "投影鏡頭溫度 - 影響成像精度"
            },
            {
                "process_name": "lithography",
                "parameter_name": "vacuum_pressure",
                "optimal_value": 1.0e-6,
                "tolerance_min": 0.5e-6,
                "tolerance_max": 1.5e-6,
                "unit": "Torr",
                "source": "expert",
                "description": "真空腔體壓力 - 防止污染"
            },
            {
                "process_name": "lithography",
                "parameter_name": "light_intensity",
                "optimal_value": 100.0,
                "tolerance_min": 95.0,
                "tolerance_max": 105.0,
                "unit": "%",
                "source": "expert",
                "description": "曝光光源強度 - 影響曝光劑量"
            },
            {
                "process_name": "lithography",
                "parameter_name": "stage_position_x",
                "optimal_value": 0.0,
                "tolerance_min": -0.005,
                "tolerance_max": 0.005,
                "unit": "μm",
                "source": "expert",
                "description": "晶圓載台 X 軸定位精度"
            },
            {
                "process_name": "lithography",
                "parameter_name": "stage_position_y",
                "optimal_value": 0.0,
                "tolerance_min": -0.005,
                "tolerance_max": 0.005,
                "unit": "μm",
                "source": "expert",
                "description": "晶圓載台 Y 軸定位精度"
            },
            {
                "process_name": "lithography",
                "parameter_name": "filter_pressure_drop",
                "optimal_value": 50.0,
                "tolerance_min": 30.0,
                "tolerance_max": 70.0,
                "unit": "Pa",
                "source": "expert",
                "description": "空氣過濾網壓降 - 超過表示堵塞"
            },
            {
                "process_name": "lithography",
                "parameter_name": "alignment_accuracy",
                "optimal_value": 0.0,
                "tolerance_min": -2.0,
                "tolerance_max": 2.0,
                "unit": "nm",
                "source": "expert",
                "description": "對準系統精度 - 影響疊對誤差"
            },
        ]

        for param in default_params:
            try:
                self.conn.execute("""
                    INSERT INTO optimal_parameters
                    (process_name, parameter_name, optimal_value, tolerance_min,
                     tolerance_max, unit, source, description)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    param["process_name"],
                    param["parameter_name"],
                    param["optimal_value"],
                    param["tolerance_min"],
                    param["tolerance_max"],
                    param["unit"],
                    param["source"],
                    param["description"]
                ))
            except sqlite3.IntegrityError:
                pass  # 參數已存在,跳過

        self.conn.commit()
        print(f"[OK] 製程參數資料庫已初始化: {len(default_params)} 個參數")

    # ==================== 查詢方法 ====================

    def get_optimal_parameters(self, process_name: str) -> Dict[str, Dict]:
        """
        取得指定製程的所有最佳參數

        Args:
            process_name: 製程名稱 (例如 "lithography")

        Returns:
            參數字典 {parameter_name: {optimal_value, tolerance_min, ...}}
        """
        cursor = self.conn.execute("""
            SELECT * FROM optimal_parameters
            WHERE process_name = ?
        """, (process_name,))

        results = {}
        for row in cursor.fetchall():
            param_name = row["parameter_name"]
            results[param_name] = {
                "optimal_value": row["optimal_value"],
                "tolerance_min": row["tolerance_min"],
                "tolerance_max": row["tolerance_max"],
                "unit": row["unit"],
                "source": row["source"],
                "description": row["description"]
            }

        return results

    def get_parameter(self, process_name: str, parameter_name: str) -> Optional[Dict]:
        """
        取得單一參數的詳細資訊

        Args:
            process_name: 製程名稱
            parameter_name: 參數名稱

        Returns:
            參數資訊字典,若不存在則回傳 None
        """
        cursor = self.conn.execute("""
            SELECT * FROM optimal_parameters
            WHERE process_name = ? AND parameter_name = ?
        """, (process_name, parameter_name))

        row = cursor.fetchone()
        if row is None:
            return None

        return {
            "optimal_value": row["optimal_value"],
            "tolerance_min": row["tolerance_min"],
            "tolerance_max": row["tolerance_max"],
            "unit": row["unit"],
            "source": row["source"],
            "description": row["description"]
        }

    def check_parameter_status(self, process_name: str, parameter_name: str,
                              current_value: float) -> Dict:
        """
        檢查參數是否在正常範圍內

        Args:
            process_name: 製程名稱
            parameter_name: 參數名稱
            current_value: 當前值

        Returns:
            狀態字典 {status: "normal"/"warning"/"critical", deviation: 偏移量}
        """
        param_info = self.get_parameter(process_name, parameter_name)

        if param_info is None:
            return {"status": "unknown", "message": "參數不存在於資料庫"}

        optimal = param_info["optimal_value"]
        tolerance_min = param_info["tolerance_min"]
        tolerance_max = param_info["tolerance_max"]

        # 計算偏移量
        deviation = abs(current_value - optimal)
        deviation_percent = (deviation / optimal * 100) if optimal != 0 else 0

        # 判斷狀態
        if tolerance_min <= current_value <= tolerance_max:
            status = "normal"
            severity = 0
        elif tolerance_min * 0.95 <= current_value <= tolerance_max * 1.05:
            status = "warning"
            severity = 1
        else:
            status = "critical"
            severity = 2

        return {
            "status": status,
            "severity": severity,
            "current_value": current_value,
            "optimal_value": optimal,
            "tolerance_min": tolerance_min,
            "tolerance_max": tolerance_max,
            "deviation": deviation,
            "deviation_percent": deviation_percent,
            "unit": param_info["unit"]
        }

    # ==================== 更新方法 ====================

    def update_parameter(self, process_name: str, parameter_name: str,
                        new_optimal: float, new_min: float, new_max: float,
                        reason: str = "", operator: str = "system"):
        """
        更新參數的最佳值與容許範圍

        Args:
            process_name: 製程名稱
            parameter_name: 參數名稱
            new_optimal: 新的最佳值
            new_min: 新的最小容許值
            new_max: 新的最大容許值
            reason: 更新原因
            operator: 操作者
        """
        # 取得舊值
        old_param = self.get_parameter(process_name, parameter_name)
        old_optimal = old_param["optimal_value"] if old_param else None

        # 更新參數
        self.conn.execute("""
            UPDATE optimal_parameters
            SET optimal_value = ?, tolerance_min = ?, tolerance_max = ?
            WHERE process_name = ? AND parameter_name = ?
        """, (new_optimal, new_min, new_max, process_name, parameter_name))

        # 記錄歷史
        self.conn.execute("""
            INSERT INTO parameter_history
            (process_name, parameter_name, old_value, new_value, reason, operator)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (process_name, parameter_name, old_optimal, new_optimal, reason, operator))

        self.conn.commit()
        print(f"[OK] 參數已更新: {parameter_name} = {new_optimal} (原: {old_optimal})")

    # ==================== 製程設定檔方法 ====================

    def create_profile(self, profile_name: str, process_name: str,
                      parameters: Dict, description: str = ""):
        """
        建立製程設定檔 (組合多個參數)

        Args:
            profile_name: 設定檔名稱 (例如 "standard_lithography")
            process_name: 製程名稱
            parameters: 參數字典 {parameter_name: value}
            description: 描述
        """
        params_json = json.dumps(parameters, ensure_ascii=False)

        try:
            self.conn.execute("""
                INSERT INTO process_profiles (profile_name, process_name, description, parameters)
                VALUES (?, ?, ?, ?)
            """, (profile_name, process_name, description, params_json))
            self.conn.commit()
            print(f"[OK] 製程設定檔已建立: {profile_name}")
        except sqlite3.IntegrityError:
            print(f"[Warning] 設定檔 {profile_name} 已存在")

    def get_profile(self, profile_name: str) -> Optional[Dict]:
        """
        取得製程設定檔

        Args:
            profile_name: 設定檔名稱

        Returns:
            設定檔資訊 {process_name, description, parameters}
        """
        cursor = self.conn.execute("""
            SELECT * FROM process_profiles WHERE profile_name = ?
        """, (profile_name,))

        row = cursor.fetchone()
        if row is None:
            return None

        return {
            "profile_name": row["profile_name"],
            "process_name": row["process_name"],
            "description": row["description"],
            "parameters": json.loads(row["parameters"]),
            "created_at": row["created_at"]
        }

    def list_profiles(self, process_name: str = None) -> List[str]:
        """
        列出所有設定檔名稱

        Args:
            process_name: 若指定,僅列出該製程的設定檔

        Returns:
            設定檔名稱列表
        """
        if process_name:
            cursor = self.conn.execute("""
                SELECT profile_name FROM process_profiles WHERE process_name = ?
            """, (process_name,))
        else:
            cursor = self.conn.execute("SELECT profile_name FROM process_profiles")

        return [row[0] for row in cursor.fetchall()]

    # ==================== 統計分析 ====================

    def get_parameter_statistics(self, process_name: str) -> Dict:
        """
        取得製程參數統計資訊

        Args:
            process_name: 製程名稱

        Returns:
            統計字典 {total_params, sources, ...}
        """
        cursor = self.conn.execute("""
            SELECT source, COUNT(*) as count
            FROM optimal_parameters
            WHERE process_name = ?
            GROUP BY source
        """, (process_name,))

        sources = {row["source"]: row["count"] for row in cursor.fetchall()}

        cursor = self.conn.execute("""
            SELECT COUNT(*) as total FROM optimal_parameters WHERE process_name = ?
        """, (process_name,))

        total = cursor.fetchone()["total"]

        return {
            "total_parameters": total,
            "sources": sources,
            "process_name": process_name
        }

    def close(self):
        """關閉資料庫連線"""
        self.conn.close()


# ==================== 測試程式 ====================

if __name__ == "__main__":
    print("=" * 60)
    print("製程參數資料庫測試")
    print("=" * 60)

    # 建立資料庫
    db = ProcessParameterDB()

    print("\n[測試 1] 取得所有光刻製程參數")
    print("-" * 60)
    params = db.get_optimal_parameters("lithography")
    for name, info in params.items():
        print(f"{name:20s} = {info['optimal_value']:8.2e} {info['unit']:6s} "
              f"[{info['tolerance_min']:.2e} ~ {info['tolerance_max']:.2e}]")

    print("\n[測試 2] 檢查參數狀態")
    print("-" * 60)
    test_cases = [
        ("cooling_flow", 5.0, "正常值"),
        ("cooling_flow", 4.5, "偏低"),
        ("cooling_flow", 3.5, "嚴重偏低"),
        ("lens_temp", 23.0, "正常值"),
        ("lens_temp", 26.5, "過高"),
    ]

    for param_name, value, desc in test_cases:
        status = db.check_parameter_status("lithography", param_name, value)
        print(f"{param_name:20s} = {value:6.1f} ({desc:12s}) → "
              f"狀態: {status['status']:8s} 偏移: {status['deviation_percent']:5.1f}%")

    print("\n[測試 3] 建立製程設定檔")
    print("-" * 60)
    standard_profile = {
        "cooling_flow": 5.0,
        "lens_temp": 23.0,
        "vacuum_pressure": 1.0e-6,
        "light_intensity": 100.0
    }
    db.create_profile(
        profile_name="standard_lithography",
        process_name="lithography",
        parameters=standard_profile,
        description="標準光刻製程設定"
    )

    print("\n[測試 4] 取得製程設定檔")
    print("-" * 60)
    profile = db.get_profile("standard_lithography")
    if profile:
        print(f"設定檔: {profile['profile_name']}")
        print(f"描述: {profile['description']}")
        print("參數:")
        for param_name, value in profile['parameters'].items():
            print(f"  {param_name:20s} = {value}")

    print("\n[測試 5] 統計資訊")
    print("-" * 60)
    stats = db.get_parameter_statistics("lithography")
    print(f"總參數數量: {stats['total_parameters']}")
    print(f"參數來源:")
    for source, count in stats['sources'].items():
        print(f"  {source:10s}: {count} 個")

    print("\n" + "=" * 60)
    print("測試完成！")
    print("=" * 60)

    db.close()
