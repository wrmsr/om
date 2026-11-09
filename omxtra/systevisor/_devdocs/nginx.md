# Managing nginx

Systevisor should run nginx as a foreground master, not allow nginx to daemonize and then try to rediscover it. A
representative unit is:

```yaml
manager:
  observation:
    interval_secs: 2

units:
  nginx:
    exec:
      argv:
        - /usr/sbin/nginx
        - -c
        - /etc/nginx/nginx.conf
        - -g
        - daemon off; master_process on; error_log /dev/stderr notice;
    restart:
      mode: unexpected
      start_secs: 2
      start_retries: 5
    stop:
      signal: QUIT
      timeout_secs: 30
      kill_signal: KILL
      scope: session
    stdio:
      stdout:
        mode: capture
        back_buffer_bytes: 4194304
      stderr:
        mode: capture
        back_buffer_bytes: 4194304
    health:
      - name: ready
        role: readiness
        kind: http
        url: http://127.0.0.1:8080/healthz
        interval_secs: 2
        timeout_secs: 1
        failure_threshold: 5
      - name: live
        role: liveness
        kind: process
        interval_secs: 5
        failure_threshold: 2
        recovery: restart
```

The nginx config should send its access log to `/dev/stdout`, bind only its intended listener addresses, and avoid a
pid-file-based control workflow. `daemon off` keeps the master as Systevisor's direct child. `QUIT` asks the master and
workers to drain gracefully; the isolated session lets timeout escalation cover stragglers while still requiring the
run's live signal lease. If the master exits only after workers drain, final session cleanup is a no-op.

An optional cgroup makes worker CPU/memory/I/O visible as one run and supplies hard resource bounds. Its root must
already be delegated to Systevisor, for example by an enclosing systemd unit. Systevisor never uses that cgroup as a
kill target. Nginx does not universally consume systemd `LISTEN_FDS`; activation sockets should be selected only when
the installed build/config or a deliberate launcher supports them.

Today, changing nginx execution/config inputs is reconciled as a restart. A future typed unit reload action can map to
nginx's `HUP` behavior, but it must travel through the same run-scoped signal lease rather than invoking `nginx -s` or
trusting a pidfile.
