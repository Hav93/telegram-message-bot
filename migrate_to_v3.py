#!/usr/bin/env python3
"""
数据库迁移脚本 - 升级到v3.0架构
"""
import sqlite3
import os
from pathlib import Path
from datetime import datetime

def migrate_to_v3():
    """迁移数据库到v3.0架构"""
    db_path = "data/bot.db"
    
    # 确保数据目录存在
    Path("data").mkdir(exist_ok=True)
    
    # 连接数据库
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    try:
        print("🚀 开始迁移数据库到v3.0架构...")
        
        # 获取现有字段
        cursor.execute("PRAGMA table_info(forward_rules)")
        existing_columns = [column[1] for column in cursor.fetchall()]
        print(f"📋 当前字段: {existing_columns}")
        
        # v3.0新增的字段
        new_columns_v3 = [
            # 客户端选择
            ("client_id", "VARCHAR(50) DEFAULT 'main_user'"),
            ("client_type", "VARCHAR(20) DEFAULT 'user'"),
            
            # 消息类型支持
            ("enable_text", "BOOLEAN DEFAULT 1"),
            ("enable_photo", "BOOLEAN DEFAULT 1"),
            ("enable_video", "BOOLEAN DEFAULT 1"),
            ("enable_document", "BOOLEAN DEFAULT 1"),
            ("enable_audio", "BOOLEAN DEFAULT 1"),
            ("enable_voice", "BOOLEAN DEFAULT 1"),
            ("enable_sticker", "BOOLEAN DEFAULT 0"),
            ("enable_animation", "BOOLEAN DEFAULT 1"),
            ("enable_webpage", "BOOLEAN DEFAULT 1"),
            
            # 时间过滤设置
            ("time_filter_type", "VARCHAR(20) DEFAULT 'after_start'"),
            ("start_time", "DATETIME"),
            ("end_time", "DATETIME"),
        ]
        
        # 添加缺失的字段
        print("🔄 添加v3.0新字段...")
        for column_name, column_definition in new_columns_v3:
            if column_name not in existing_columns:
                print(f"  ➕ 添加字段: {column_name}")
                try:
                    cursor.execute(f"ALTER TABLE forward_rules ADD COLUMN {column_name} {column_definition}")
                except sqlite3.OperationalError as e:
                    if "duplicate column name" not in str(e):
                        print(f"    ⚠️ 添加字段失败: {e}")
                    else:
                        print(f"    ✅ 字段已存在: {column_name}")
            else:
                print(f"  ✅ 字段已存在: {column_name}")
        
        # 确保旧字段的默认值正确
        print("🔧 更新现有数据的默认值...")
        
        # 为没有client_id的规则设置默认值
        cursor.execute("UPDATE forward_rules SET client_id = 'main_user' WHERE client_id IS NULL OR client_id = ''")
        cursor.execute("UPDATE forward_rules SET client_type = 'user' WHERE client_type IS NULL OR client_type = ''")
        
        # 为消息类型字段设置默认值
        cursor.execute("UPDATE forward_rules SET enable_text = 1 WHERE enable_text IS NULL")
        cursor.execute("UPDATE forward_rules SET enable_photo = 1 WHERE enable_photo IS NULL")
        cursor.execute("UPDATE forward_rules SET enable_video = 1 WHERE enable_video IS NULL")
        cursor.execute("UPDATE forward_rules SET enable_document = 1 WHERE enable_document IS NULL")
        cursor.execute("UPDATE forward_rules SET enable_audio = 1 WHERE enable_audio IS NULL")
        cursor.execute("UPDATE forward_rules SET enable_voice = 1 WHERE enable_voice IS NULL")
        cursor.execute("UPDATE forward_rules SET enable_sticker = 0 WHERE enable_sticker IS NULL")
        cursor.execute("UPDATE forward_rules SET enable_animation = 1 WHERE enable_animation IS NULL")
        cursor.execute("UPDATE forward_rules SET enable_webpage = 1 WHERE enable_webpage IS NULL")
        
        # 设置时间过滤类型默认值
        cursor.execute("UPDATE forward_rules SET time_filter_type = 'after_start' WHERE time_filter_type IS NULL OR time_filter_type = ''")
        
        # 提交更改
        conn.commit()
        
        print("✅ 数据库迁移到v3.0完成！")
        
        # 验证迁移结果
        print("\n🔍 验证迁移结果:")
        cursor.execute("PRAGMA table_info(forward_rules)")
        all_columns = [column[1] for column in cursor.fetchall()]
        print(f"📋 迁移后字段数量: {len(all_columns)}")
        
        # 检查数据完整性
        cursor.execute("SELECT COUNT(*) FROM forward_rules")
        rule_count = cursor.fetchone()[0]
        print(f"📊 转发规则数量: {rule_count}")
        
        if rule_count > 0:
            # 检查新字段是否有正确的默认值
            cursor.execute("""
            SELECT 
                COUNT(*) as total,
                SUM(CASE WHEN client_id IS NOT NULL AND client_id != '' THEN 1 ELSE 0 END) as with_client_id,
                SUM(CASE WHEN enable_text = 1 THEN 1 ELSE 0 END) as enable_text_count
            FROM forward_rules
            """)
            stats = cursor.fetchone()
            print(f"📈 数据完整性检查:")
            print(f"  总规则数: {stats[0]}")
            print(f"  有client_id的规则: {stats[1]}")
            print(f"  启用文本转发的规则: {stats[2]}")
        
    except Exception as e:
        print(f"❌ 数据库迁移失败: {e}")
        conn.rollback()
        raise
    
    finally:
        conn.close()

def check_migration_needed():
    """检查是否需要迁移"""
    db_path = "data/bot.db"
    
    if not os.path.exists(db_path):
        print("📝 数据库不存在，将在首次启动时自动创建")
        return False
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    try:
        # 检查是否有v3.0的字段
        cursor.execute("PRAGMA table_info(forward_rules)")
        columns = [column[1] for column in cursor.fetchall()]
        
        v3_fields = ['client_id', 'client_type', 'enable_text', 'time_filter_type']
        missing_fields = [field for field in v3_fields if field not in columns]
        
        if missing_fields:
            print(f"🔍 检测到缺失的v3.0字段: {missing_fields}")
            return True
        else:
            print("✅ 数据库架构已是v3.0版本")
            return False
            
    except Exception as e:
        print(f"❌ 检查数据库架构失败: {e}")
        return True
    finally:
        conn.close()

if __name__ == "__main__":
    print("🔧 Telegram Message Bot v3.0 数据库迁移工具")
    print("=" * 50)
    
    if check_migration_needed():
        print("\n🚀 开始迁移...")
        migrate_to_v3()
        print("\n🎉 迁移完成！现在可以启动v3.0版本了。")
    else:
        print("\n✅ 数据库已是最新版本，无需迁移。")

