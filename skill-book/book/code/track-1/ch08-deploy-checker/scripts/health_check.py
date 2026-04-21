#!/usr/bin/env python3
"""health_check.py — 检查服务健康状态

用法: python health_check.py <url> [--timeout 5]
stdout: JSON 检查结果
stderr: 状态信息
"""

import sys
import json
import time
import urllib.request
import urllib.error


def check_health(url, timeout=5):
    """发送 GET 请求检查健康状态"""
    print(f"正在检查: {url}", file=sys.stderr)

    result = {
        'url': url,
        'timestamp': time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime()),
    }

    start = time.time()
    try:
        req = urllib.request.Request(url, method='GET')
        req.add_header('User-Agent', 'deploy-checker/1.0')

        with urllib.request.urlopen(req, timeout=timeout) as resp:
            elapsed = time.time() - start
            body = resp.read().decode('utf-8', errors='replace')

            result['status_code'] = resp.status
            result['response_time_ms'] = round(elapsed * 1000)
            result['body_length'] = len(body)

            # 检查常见的健康标记
            health_markers = ['ok', 'healthy', 'alive', '"status"']
            result['has_health_marker'] = any(
                m in body.lower() for m in health_markers
            )

            # 判断结果
            checks = []
            checks.append({
                'name': 'HTTP 200',
                'pass': resp.status == 200,
                'detail': f'状态码: {resp.status}'
            })
            checks.append({
                'name': '响应时间 < 5s',
                'pass': elapsed < 5,
                'detail': f'{result["response_time_ms"]}ms'
            })
            checks.append({
                'name': '健康标记',
                'pass': result['has_health_marker'],
                'detail': '包含健康标记' if result['has_health_marker'] else '未检测到健康标记'
            })

            result['checks'] = checks
            result['status'] = 'PASS' if all(c['pass'] for c in checks) else 'WARN'

    except urllib.error.HTTPError as e:
        elapsed = time.time() - start
        result['status_code'] = e.code
        result['response_time_ms'] = round(elapsed * 1000)
        result['error'] = str(e)
        result['status'] = 'FAIL'
        print(f"  ✗ HTTP {e.code}: {e}", file=sys.stderr)

    except (urllib.error.URLError, TimeoutError) as e:
        elapsed = time.time() - start
        result['response_time_ms'] = round(elapsed * 1000)
        result['error'] = str(e)
        result['status'] = 'FAIL'
        print(f"  ✗ 连接失败: {e}", file=sys.stderr)

    return result


def main():
    if len(sys.argv) < 2:
        print("用法: python health_check.py <url> [--timeout 5]", file=sys.stderr)
        sys.exit(1)

    url = sys.argv[1]
    timeout = 5

    if '--timeout' in sys.argv:
        idx = sys.argv.index('--timeout')
        if idx + 1 < len(sys.argv):
            timeout = int(sys.argv[idx + 1])

    result = check_health(url, timeout)
    json.dump(result, sys.stdout, indent=2, ensure_ascii=False)

    print(f"\n健康检查完成: {result['status']}", file=sys.stderr)
    sys.exit(0 if result['status'] != 'FAIL' else 1)


if __name__ == '__main__':
    main()
