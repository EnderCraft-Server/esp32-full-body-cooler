# -*- coding: utf-8 -*-
r"""
serial_term.py -- 交互式串口终端（能收也能发）

用法:
    .\.venv\Scripts\python.exe .\scripts\serial_term.py --port COM6
    或    .\scripts\term.ps1 --port COM6

  直接打字 -> 回车发送   Backspace 删除   Ctrl+C 退出
  ESP32 的输出会实时打印在同一屏上
"""
import argparse, os, sys, time, threading

try:
    import serial
except ImportError:
    print('[term] 缺 pyserial。用工作区 venv 的 python 运行:')
    print('       .\\.venv\\Scripts\\python.exe .\\scripts\\serial_term.py --port COM6')
    raise SystemExit(1)

if not hasattr(serial, 'Serial'):
    print('[term] 导入到的不是 pyserial（模块路径: %s）' % getattr(serial, '__file__', '?'))
    print('[term] 你用的是系统 python。请改用工作区 venv:')
    print('       .\\.venv\\Scripts\\python.exe .\\scripts\\serial_term.py --port COM6')
    raise SystemExit(1)

import msvcrt


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--port', default='COM6')
    ap.add_argument('--baud', type=int, default=115200)
    a = ap.parse_args()

    try:
        sys.stdout.reconfigure(encoding='utf-8', errors='replace')
    except Exception:
        pass
    os.system('chcp 65001 >nul 2>&1')

    try:
        ser = serial.Serial(a.port, a.baud, timeout=0.05)
    except Exception as e:
        print('[term] 打不开 %s: %s' % (a.port, e))
        return 1

    print('=' * 58)
    print('  串口终端  %s @ %d' % (a.port, a.baud))
    print('  打字后按回车发送   Backspace 删除   Ctrl+C 退出')
    print('  常用: status / scan / map skin_chest 0 / save')
    print('        pump on / pump off / enable off / mode 2 / mode 0')
    print('=' * 58)

    alive = True

    def reader():
        while alive:
            try:
                d = ser.read(4096)
            except Exception:
                return
            if d:
                sys.stdout.write(d.decode('utf-8', 'replace'))
                sys.stdout.flush()

    th = threading.Thread(target=reader, daemon=True)
    th.start()

    buf = ''
    try:
        while alive:
            if msvcrt.kbhit():
                ch = msvcrt.getwch()
                if ch in ('\x00', '\xe0'):
                    msvcrt.getwch()
                    continue
                if ch == '\x03':
                    break
                if ch == '\r':
                    sys.stdout.write('\n')
                    sys.stdout.flush()
                    try:
                        ser.write((buf + '\r\n').encode())
                    except Exception as e:
                        print('[term] 发送失败:', e)
                    buf = ''
                    continue
                if ch == '\x08':
                    if buf:
                        buf = buf[:-1]
                        sys.stdout.write('\b \b')
                        sys.stdout.flush()
                    continue
                buf += ch
                sys.stdout.write(ch)
                sys.stdout.flush()
            time.sleep(0.01)
    except KeyboardInterrupt:
        pass
    finally:
        alive = False
        time.sleep(0.1)
        try:
            ser.close()
        except Exception:
            pass
        print('\n[term] 已断开')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())