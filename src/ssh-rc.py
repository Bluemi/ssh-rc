#!/usr/bin/env python3
import sys
from pathlib import Path

import paramiko
import argparse
import dns.resolver

import pygame as pg


def init_keymap():
    keymap = {
        8: 'BackSpace',
        27: 'Escape',
        32: 'space',
        13: 'Return',
        1073742049: 'Shift',
        1073742051: 'Super_L',
        1073742048: 'Control_L',
        1073742052: 'Control_R',
        1073741881: 'CapsLock',
    }
    for key, unicode in enumerate('abcdefghijklmnopqrstuvwxyz'):
        keymap[key+97] = unicode

    return keymap


def parse_args():
    parser = argparse.ArgumentParser(description='A small tool to use x commands over ssh')
    parser.add_argument('user', type=str, help='The user on the remote system')
    parser.add_argument('host', type=str, help='The host to connect to')
    parser.add_argument('--pkey', type=Path, help='The private key to use for connection')
    return parser.parse_args()


def main():
    keymap = init_keymap()
    ssh_client = setup_ssh_client()
    setup_pygame()

    running = True
    while running:
        mouse_rel = (0, 0)
        mouse_button_down = []
        mouse_button_up = []

        key_down = []
        key_up = []

        events = [pg.event.wait()]
        events = events + pg.event.get()

        for event in events:
            if event.type == pg.QUIT:
                running = False

            if event.type == pg.MOUSEMOTION:
                if event.pos != (200, 200):
                    mouse_rel = (mouse_rel[0] + event.rel[0], mouse_rel[1] + event.rel[1])
                    pg.mouse.set_pos(200, 200)

            if event.type == pg.MOUSEBUTTONDOWN:
                mouse_button_down.append(event.button)
            if event.type == pg.MOUSEBUTTONUP:
                mouse_button_up.append(event.button)

            if event.type == pg.KEYDOWN:
                keyname = keymap.get(event.key)
                if keyname is None:
                    print('unsupported key: {}'.format(event.key))
                else:
                    key_down.append(keyname)
            if event.type == pg.KEYUP:
                keyname = keymap.get(event.key)
                if keyname is not None:
                    key_up.append(keyname)

        commands = []
        if mouse_rel != (0, 0):
            commands.append('DISPLAY=:0 xdotool mousemove_relative -- {} {}'.format(*mouse_rel))

        for mbd in mouse_button_down:
            commands.append('DISPLAY=:0 xdotool mousedown {}'.format(mbd))
        for mbd in mouse_button_up:
            commands.append('DISPLAY=:0 xdotool mouseup {}'.format(mbd))

        for kd in key_down:
            commands.append('DISPLAY=:0 xdotool keydown "{}"'.format(kd))
        for kd in key_up:
            commands.append('DISPLAY=:0 xdotool keyup "{}"'.format(kd))

        ssh_client.exec_command(';'.join(commands))



def setup_pygame():
    pg.init()
    pg.display.set_caption('ssh-rc')
    surface = pg.display.set_mode((400, 400))
    return surface


def setup_ssh_client():
    args = parse_args()

    # resolve hostname
    hostnames = dns.resolver.resolve(args.host)
    if len(hostnames) < 1:
        print('unable to resolve: {}'.format(args.host))
        sys.exit(1)
    host = hostnames[0].address

    # load private key
    pkey = None
    if args.pkey:
        pkey = paramiko.RSAKey.from_private_key_file(args.pkey)

    # connect ssh
    ssh_client = paramiko.SSHClient()
    ssh_client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    ssh_client.connect(host, username=args.user, pkey=pkey)

    return ssh_client


if __name__ == '__main__':
    main()

