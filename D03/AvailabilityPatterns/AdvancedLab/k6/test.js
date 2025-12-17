import http from 'k6/http';
import { check, sleep } from 'k6';

export const options = {
    stages: [
        { duration: '30s', target: 50 }, // 50 VUs trong 30 giây
    ],
    thresholds: {
        // Đảm bảo không có lỗi 4xx/5xx quá 1%
        http_req_failed: ['rate<0.01'],
        // Latency p95 phải dưới 1000ms (1 giây)
        http_req_duration: ['p(95)<1000'],
    },
};

export default function () {
    const res = http.get('http://nginx-lb:80/');
    check(res, {
        'is status 200': (r) => r.status === 200,
    });
    sleep(1);
}