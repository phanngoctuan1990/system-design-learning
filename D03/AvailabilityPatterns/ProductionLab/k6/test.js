import http from 'k6/http';
import { check, sleep } from 'k6';

export default function () {
    const res = http.get('http://nginx-lb:80/');
    check(res, {
        'is status 200': (r) => r.status === 200,
    });
    sleep(1);
}
