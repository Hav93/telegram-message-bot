#!/bin/bash

# Telegram Message Bot v3.0 一键部署脚本

set -e

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# 打印带颜色的消息
print_info() {
    echo -e "${BLUE}ℹ️  $1${NC}"
}

print_success() {
    echo -e "${GREEN}✅ $1${NC}"
}

print_warning() {
    echo -e "${YELLOW}⚠️  $1${NC}"
}

print_error() {
    echo -e "${RED}❌ $1${NC}"
}

print_header() {
    echo ""
    echo -e "${BLUE}🚀 Telegram Message Bot v3.0 一键部署${NC}"
    echo "=================================================="
}

# 检查依赖
check_dependencies() {
    print_info "检查系统依赖..."
    
    if ! command -v docker &> /dev/null; then
        print_error "Docker 未安装，请先安装 Docker"
        exit 1
    fi
    
    if ! command -v docker-compose &> /dev/null; then
        print_error "Docker Compose 未安装，请先安装 Docker Compose"
        exit 1
    fi
    
    print_success "系统依赖检查通过"
}

# 创建数据目录
create_directories() {
    print_info "创建数据目录..."
    
    mkdir -p data logs temp sessions config
    chmod 755 data logs temp sessions config
    
    print_success "数据目录创建完成"
}

# 交互式配置
interactive_config() {
    print_info "开始交互式配置..."
    
    # 检查是否已存在配置
    if [ -f "docker-compose.yml" ] && [ -f ".env" ]; then
        echo ""
        read -p "检测到现有配置，是否重新配置？(y/N): " reconfigure
        if [[ ! $reconfigure =~ ^[Yy]$ ]]; then
            print_info "跳过配置，使用现有配置"
            return
        fi
    fi
    
    echo ""
    print_warning "请准备以下信息："
    echo "1. Telegram API_ID 和 API_HASH (从 https://my.telegram.org 获取)"
    echo "2. Bot Token (从 @BotFather 获取)"
    echo "3. 手机号 (国际格式，如: +8613800138000)"
    echo "4. 管理员用户ID (从 @userinfobot 获取)"
    echo ""
    
    read -p "按 Enter 继续..."
    echo ""
    
    # API配置
    read -p "请输入 API_ID: " api_id
    while [[ ! "$api_id" =~ ^[0-9]+$ ]]; do
        print_error "API_ID 必须是数字"
        read -p "请重新输入 API_ID: " api_id
    done
    
    read -p "请输入 API_HASH: " api_hash
    while [[ -z "$api_hash" ]]; do
        print_error "API_HASH 不能为空"
        read -p "请重新输入 API_HASH: " api_hash
    done
    
    read -p "请输入 BOT_TOKEN: " bot_token
    while [[ ! "$bot_token" =~ ^[0-9]+:.+ ]]; do
        print_error "BOT_TOKEN 格式不正确"
        read -p "请重新输入 BOT_TOKEN: " bot_token
    done
    
    read -p "请输入手机号 (如: +8613800138000): " phone_number
    while [[ ! "$phone_number" =~ ^\+[0-9]{10,15}$ ]]; do
        print_error "手机号格式不正确，请使用国际格式"
        read -p "请重新输入手机号: " phone_number
    done
    
    read -p "请输入管理员用户ID (多个用逗号分隔): " admin_user_ids
    while [[ ! "$admin_user_ids" =~ ^[0-9]+(,[0-9]+)*$ ]]; do
        print_error "用户ID格式不正确"
        read -p "请重新输入管理员用户ID: " admin_user_ids
    done
    
    # 可选配置
    echo ""
    print_info "可选配置 (直接按Enter跳过):"
    
    read -p "HTTP代理地址 (如: http://127.0.0.1:1080): " http_proxy
    read -p "HTTPS代理地址 (如: http://127.0.0.1:1080): " https_proxy
    
    # 生成配置文件
    generate_config_files "$api_id" "$api_hash" "$bot_token" "$phone_number" "$admin_user_ids" "$http_proxy" "$https_proxy"
}

# 生成配置文件
generate_config_files() {
    local api_id=$1
    local api_hash=$2
    local bot_token=$3
    local phone_number=$4
    local admin_user_ids=$5
    local http_proxy=$6
    local https_proxy=$7
    
    print_info "生成配置文件..."
    
    # 获取当前目录的绝对路径
    current_dir=$(pwd)
    
    # 生成 docker-compose.yml
    cat > docker-compose.yml << EOF
version: '3.8'

services:
  telegram-message-bot:
    image: hav93/telegram-message-bot:3.0
    container_name: telegram-message-bot
    restart: always
    networks:
      - telegram-net

    ports:
      - 9393:9393

    environment:
      - TZ=Asia/Shanghai
      # === Telegram API配置 ===
      - API_ID=${api_id}
      - API_HASH=${api_hash}
      - BOT_TOKEN=${bot_token}
      - PHONE_NUMBER=${phone_number}
      - ADMIN_USER_IDS=${admin_user_ids}
EOF

    # 添加代理配置（如果提供）
    if [ -n "$http_proxy" ]; then
        echo "      - HTTP_PROXY=${http_proxy}" >> docker-compose.yml
    fi
    
    if [ -n "$https_proxy" ]; then
        echo "      - HTTPS_PROXY=${https_proxy}" >> docker-compose.yml
    fi
    
    # 添加其余配置
    cat >> docker-compose.yml << EOF
      - DATABASE_URL=sqlite:///data/bot.db
      
      # Web界面配置
      - WEB_HOST=0.0.0.0
      - WEB_PORT=9393
      
      # 权限配置
      - PUID=1000
      - PGID=1000
      
    volumes:
      - ${current_dir}/data:/app/data
      - ${current_dir}/logs:/app/logs
      - ${current_dir}/temp:/app/temp
      - ${current_dir}/sessions:/app/sessions
      - ${current_dir}/config:/app/config
      
    healthcheck:
      test: ["CMD", "python", "-c", "import requests; requests.get('http://localhost:9393/').raise_for_status()"]
      interval: 30s
      timeout: 10s
      retries: 3
      start_period: 40s

networks:
  telegram-net:
    driver: bridge
EOF
    
    print_success "配置文件生成完成"
}

# 部署服务
deploy_service() {
    print_info "开始部署服务..."
    
    # 拉取最新镜像
    print_info "拉取Docker镜像..."
    docker-compose pull
    
    # 启动服务
    print_info "启动服务..."
    docker-compose up -d
    
    # 等待服务启动
    print_info "等待服务启动..."
    sleep 10
    
    # 检查服务状态
    if docker-compose ps | grep -q "Up"; then
        print_success "服务启动成功！"
        
        echo ""
        echo "🌐 Web管理界面: http://localhost:9393"
        echo "📊 服务状态: docker-compose ps"
        echo "📝 查看日志: docker-compose logs -f"
        echo "🔄 重启服务: docker-compose restart"
        echo "🛑 停止服务: docker-compose down"
        echo ""
        
        print_info "初次使用请访问Web界面进行客户端配置"
    else
        print_error "服务启动失败，请查看日志: docker-compose logs"
        exit 1
    fi
}

# 显示帮助
show_help() {
    echo "用法: $0 [选项]"
    echo ""
    echo "选项:"
    echo "  -h, --help     显示帮助信息"
    echo "  -q, --quick    快速模式（使用现有配置）"
    echo "  -c, --config   仅生成配置文件"
    echo "  -d, --deploy   仅部署服务"
    echo ""
}

# 主函数
main() {
    local quick_mode=false
    local config_only=false
    local deploy_only=false
    
    # 解析命令行参数
    while [[ $# -gt 0 ]]; do
        case $1 in
            -h|--help)
                show_help
                exit 0
                ;;
            -q|--quick)
                quick_mode=true
                shift
                ;;
            -c|--config)
                config_only=true
                shift
                ;;
            -d|--deploy)
                deploy_only=true
                shift
                ;;
            *)
                print_error "未知选项: $1"
                show_help
                exit 1
                ;;
        esac
    done
    
    print_header
    
    if [ "$config_only" = false ]; then
        check_dependencies
        create_directories
    fi
    
    if [ "$deploy_only" = false ]; then
        if [ "$quick_mode" = false ]; then
            interactive_config
        else
            if [ ! -f "docker-compose.yml" ]; then
                print_error "快速模式需要现有的 docker-compose.yml 文件"
                exit 1
            fi
            print_info "使用快速模式，跳过配置"
        fi
    fi
    
    if [ "$config_only" = false ]; then
        deploy_service
    fi
    
    print_success "部署完成！"
}

# 运行主函数
main "$@"
