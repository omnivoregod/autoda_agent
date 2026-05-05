#!/bin/bash
# wait-for-it.sh - 等待服务就绪脚本
# 确保应用在依赖服务（MySQL、Redis等）就绪后再启动

set -e

TIMEOUT=60
QUIET=0
HOST=""
PORT=""

usage() {
    echo "Usage: $0 HOST:PORT [-t timeout] [-q] [-- command args]"
    echo "  -t TIMEOUT      等待超时时间（秒），默认60"
    echo "  -q              静默模式，减少输出"
    echo "  -- COMMAND ARGS 在服务就绪后执行的命令"
    exit 1
}

wait_for() {
    local host=$1
    local port=$2
    local timeout=$3

    echo "等待服务 $host:$port 就绪..."

    for i in $(seq 1 "$timeout"); do
        if nc -z "$host" "$port" 2>/dev/null; then
            echo "$host:$port 已就绪"
            return 0
        fi
        if [ $i -lt $timeout ]; then
            sleep 1
        fi
    done

    echo "等待超时: $host:$port 在 ${timeout} 秒内未就绪"
    return 1
}

# 解析参数
while [[ $# -gt 0 ]]; do
    case "$1" in
        *:*)
            HOST_PORT="$1"
            HOST="${HOST_PORT%:*}"
            PORT="${HOST_PORT#*:}"
            shift
            ;;
        -t)
            TIMEOUT="$2"
            shift 2
            ;;
        -q)
            QUIET=1
            shift
            ;;
        --)
            shift
            break
            ;;
        *)
            echo "未知参数: $1"
            usage
            ;;
    esac
done

if [ -z "$HOST" ] || [ -z "$PORT" ]; then
    echo "错误: 必须指定 HOST:PORT"
    usage
fi

if [ "$QUIET" -eq 0 ]; then
    wait_for "$HOST" "$PORT" "$TIMEOUT"
else
    wait_for "$HOST" "$PORT" "$TIMEOUT" > /dev/null 2>&1
fi

RESULT=$?

if [ $RESULT -eq 0 ] && [ $# -gt 0 ]; then
    exec "$@"
fi

exit $RESULT
