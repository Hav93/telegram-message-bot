#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
部署诊断脚本 - 检查前端构建和服务配置
"""

import os
import sys
from pathlib import Path
import json
from datetime import datetime

def check_frontend_build():
    """检查前端构建状态"""
    print("🔍 检查前端构建状态...")
    
    # 检查可能的构建路径
    possible_paths = [
        Path("frontend/dist"),      # Docker容器中的路径
        Path("app/frontend/dist"),  # 从项目根目录运行时
        Path("../frontend/dist"),   # 从backend目录运行时
    ]
    
    build_found = False
    for path in possible_paths:
        if path.exists():
            print(f"✅ 找到构建目录: {path.absolute()}")
            
            # 检查关键文件
            index_file = path / "index.html"
            assets_dir = path / "assets"
            
            if index_file.exists():
                print(f"✅ index.html 存在")
                # 检查文件修改时间
                mtime = datetime.fromtimestamp(index_file.stat().st_mtime)
                print(f"📅 最后修改时间: {mtime}")
            else:
                print(f"❌ index.html 不存在")
            
            if assets_dir.exists():
                print(f"✅ assets 目录存在")
                # 列出assets文件
                assets = list(assets_dir.glob("*"))
                print(f"📦 资源文件数量: {len(assets)}")
                for asset in assets[:5]:  # 只显示前5个
                    mtime = datetime.fromtimestamp(asset.stat().st_mtime)
                    print(f"   - {asset.name} ({mtime})")
            else:
                print(f"❌ assets 目录不存在")
                
            build_found = True
            break
        else:
            print(f"❌ 路径不存在: {path.absolute()}")
    
    if not build_found:
        print("❌ 未找到任何前端构建文件")
        print("💡 请运行构建脚本: build_and_deploy.bat 或 build_and_deploy.sh")
    
    return build_found

def check_backend_config():
    """检查后端配置"""
    print("\n🔍 检查后端配置...")
    
    backend_file = Path("app/backend/web_enhanced_clean.py")
    if not backend_file.exists():
        print("❌ 后端文件不存在")
        return False
    
    with open(backend_file, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # 检查静态文件配置
    if "StaticFiles" in content:
        print("✅ 找到静态文件配置")
    else:
        print("❌ 未找到静态文件配置")
    
    # 检查路径配置
    if "app/frontend/dist" in content:
        print("✅ 包含正确的前端路径配置")
    else:
        print("⚠️ 可能缺少正确的前端路径配置")
    
    return True

def check_package_json():
    """检查package.json和构建配置"""
    print("\n🔍 检查前端配置...")
    
    package_file = Path("app/frontend/package.json")
    if not package_file.exists():
        print("❌ package.json 不存在")
        return False
    
    with open(package_file, 'r', encoding='utf-8') as f:
        package_data = json.load(f)
    
    print(f"📦 项目名称: {package_data.get('name', '未知')}")
    print(f"📦 版本: {package_data.get('version', '未知')}")
    
    # 检查构建脚本
    scripts = package_data.get('scripts', {})
    if 'build' in scripts:
        print(f"✅ 构建脚本: {scripts['build']}")
    else:
        print("❌ 未找到构建脚本")
    
    return True

def check_git_status():
    """检查Git状态"""
    print("\n🔍 检查Git状态...")
    
    if not Path(".git").exists():
        print("❌ 不是Git仓库")
        return False
    
    try:
        import subprocess
        
        # 检查当前分支
        result = subprocess.run(['git', 'branch', '--show-current'], 
                              capture_output=True, text=True)
        if result.returncode == 0:
            print(f"🌿 当前分支: {result.stdout.strip()}")
        
        # 检查最新提交
        result = subprocess.run(['git', 'log', '-1', '--oneline'], 
                              capture_output=True, text=True)
        if result.returncode == 0:
            print(f"📝 最新提交: {result.stdout.strip()}")
        
        # 检查是否有未提交的更改
        result = subprocess.run(['git', 'status', '--porcelain'], 
                              capture_output=True, text=True)
        if result.returncode == 0:
            if result.stdout.strip():
                print("⚠️ 有未提交的更改")
            else:
                print("✅ 工作目录干净")
        
    except Exception as e:
        print(f"❌ Git检查失败: {e}")
    
    return True

def check_docker_environment():
    """检查是否在Docker环境中运行"""
    print("\n🐳 检查Docker环境...")
    
    # 检查是否在容器中
    is_docker = False
    
    # 方法1: 检查/.dockerenv文件
    if Path("/.dockerenv").exists():
        is_docker = True
        print("✅ 检测到Docker环境 (/.dockerenv文件存在)")
    
    # 方法2: 检查cgroup信息
    try:
        with open("/proc/1/cgroup", "r") as f:
            cgroup_content = f.read()
            if "docker" in cgroup_content or "containerd" in cgroup_content:
                is_docker = True
                print("✅ 检测到Docker环境 (cgroup信息)")
    except (FileNotFoundError, PermissionError):
        pass
    
    # 方法3: 检查工作目录
    if str(Path.cwd()) == "/app":
        is_docker = True
        print("✅ 可能在Docker环境中 (工作目录为/app)")
    
    if not is_docker:
        print("❌ 未检测到Docker环境")
    
    return is_docker

def main():
    """主函数"""
    print("🚀 部署状态诊断工具")
    print("=" * 50)
    
    # 检查当前工作目录
    print(f"📁 当前工作目录: {Path.cwd()}")
    
    # 检查Docker环境
    is_docker = check_docker_environment()
    
    # 运行各项检查
    frontend_ok = check_frontend_build()
    backend_ok = check_backend_config()
    package_ok = check_package_json()
    git_ok = check_git_status()
    
    print("\n" + "=" * 50)
    print("📊 诊断结果总结:")
    print(f"   Docker环境: {'✅' if is_docker else '❌'}")
    print(f"   前端构建: {'✅' if frontend_ok else '❌'}")
    print(f"   后端配置: {'✅' if backend_ok else '❌'}")
    print(f"   包配置: {'✅' if package_ok else '❌'}")
    print(f"   Git状态: {'✅' if git_ok else '❌'}")
    
    if is_docker:
        print("\n🐳 Docker环境检测到:")
        if frontend_ok:
            print("   ✅ 前端文件已正确部署到Docker容器")
        else:
            print("   ❌ Docker容器中缺少前端文件")
            print("   💡 请重新构建Docker镜像:")
            print("      docker pull hav93/telegram-message-bot:latest")
    else:
        if not frontend_ok:
            print("\n💡 本地环境建议操作:")
            print("   1. 运行构建脚本: ./build_and_deploy.sh")
            print("   2. 手动构建: cd app/frontend && npm run build")
            print("   3. 检查Node.js和npm是否正确安装")
    
    print("\n🔄 如果问题仍然存在:")
    if is_docker:
        print("   1. 重启Docker容器")
        print("   2. 拉取最新镜像: docker pull hav93/telegram-message-bot:latest")
        print("   3. 检查容器日志: docker logs <container_name>")
    else:
        print("   1. 重启Python服务")
        print("   2. 清除浏览器缓存 (Ctrl+F5)")
        print("   3. 检查服务器日志")

if __name__ == "__main__":
    main()
