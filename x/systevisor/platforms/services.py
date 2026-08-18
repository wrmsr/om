# ruff: noqa: UP006 UP007 UP045
import dataclasses as dc
import json
import typing as ta
import xml.sax.saxutils


@dc.dataclass(frozen=True)
class SystevisorServiceTemplateConfig:
    executable: str
    config_paths: ta.Sequence[str]
    identifier: str = 'systevisor'
    recursive: bool = False
    state_directory: ta.Optional[str] = None

    def argv(self) -> ta.Sequence[str]:
        argv = [self.executable, 'serve']
        for path in self.config_paths:
            argv.extend(('-c', path))
        if self.recursive:
            argv.append('--recursive')
        if self.state_directory is not None:
            argv.extend(('--state-directory', self.state_directory))
        return tuple(argv)


def _systevisor_services_systemd_quote(value: str) -> str:
    return json.dumps(value.replace('%', '%%'), ensure_ascii=True)


def systevisor_render_systemd_service(config: SystevisorServiceTemplateConfig) -> str:
    if not config.executable or not config.config_paths:
        raise ValueError('service template requires an executable and at least one config path')
    exec_start = ' '.join(_systevisor_services_systemd_quote(argument) for argument in config.argv())
    return '\n'.join((
        '[Unit]',
        f'Description={config.identifier} process manager',
        'After=network.target',
        '',
        '[Service]',
        'Type=notify',
        'NotifyAccess=main',
        f'ExecStart={exec_start}',
        'Restart=on-failure',
        'KillMode=process',
        '',
        '[Install]',
        'WantedBy=multi-user.target',
        '',
    ))


def _systevisor_services_launchd_string(value: str) -> str:
    return f'    <string>{xml.sax.saxutils.escape(value)}</string>'


def systevisor_render_launchd_plist(config: SystevisorServiceTemplateConfig) -> str:
    if not config.executable or not config.config_paths:
        raise ValueError('service template requires an executable and at least one config path')
    arguments = '\n'.join(_systevisor_services_launchd_string(argument) for argument in config.argv())
    return '\n'.join((
        '<?xml version="1.0" encoding="UTF-8"?>',
        '<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN"',
        '  "http://www.apple.com/DTDs/PropertyList-1.0.dtd">',
        '<plist version="1.0">',
        '<dict>',
        '  <key>Label</key>',
        _systevisor_services_launchd_string(config.identifier),
        '  <key>ProgramArguments</key>',
        '  <array>',
        arguments,
        '  </array>',
        '  <key>RunAtLoad</key>',
        '  <true/>',
        '  <key>KeepAlive</key>',
        '  <dict>',
        '    <key>SuccessfulExit</key>',
        '    <false/>',
        '  </dict>',
        '  <key>ProcessType</key>',
        '  <string>Background</string>',
        '</dict>',
        '</plist>',
        '',
    ))
