# -*- coding: utf-8 -*-

import logging
import json
import os
import sys
from pathlib import Path

from .utils import mangle
#from meross_powermon.modified_device import Mss310
from meross_iot.supported_devices.light_bulbs import GenericBulb

CONFIG = "~/.config/meross/config.json"

_LOGGER = logging.getLogger("meross_offline")

def exists(user=CONFIG, fail=True):
    cfgfile = Path.expanduser(Path(CONFIG))
    if fail and not cfgfile.exists():
        sys.exit("No configuration file, run 'meross init' first")
    return cfgfile.exists()


def load(user=CONFIG):
    cfgfile = Path.expanduser(Path(user))
    if not cfgfile.exists():
        # Prevent root triggering this for the user config
        if os.getuid() == 0 and "~" not in user:
            msg = 'No user configuration file "{}".\n'.format(cfgfile)
            msg += 'Ask user to run "meross init" before continuing.'
            sys.exit(msg)
        cfgfile.parent.mkdir(parents=True, exist_ok=True)
        save(dict())
        return dict()
    cfg = json.loads(cfgfile.read_text())
    return cfg


def update(cfg, opts, attrs=["server", "port", "ca_cert"]):
    for attr in attrs:
        if getattr(opts, attr):
            cfg[attr] = getattr(opts, attr)


def user_config_file(user):
    return "/Users/" + user + "/.config/meross_powermon/config.json"


def load_user(user):
    return load(user_config_file(user))


def save(cfg, user=CONFIG):
    cfgfile = Path.expanduser(Path(user))
    cfgfile.write_text(json.dumps(cfg, indent=4))
    cfgfile.chmod(0o600)


def save_user(cfg, user):
    save(cfg, user_config_file(user))


def add_device(dev, opts, user):
    cfg = load_user(user)
    cfg["devices"] = cfg.get("devices", dict())
    devices = cfg.get("devices")
    if list(dev.keys())[0] in devices:
        if not opts.force:
            sys.exit("Unable to overwrite device unless you use --force")
    cfg["devices"].update(dev)
    save_user(cfg, user)


def list_devices(cfg):
    return list(cfg["devices"].keys())


def connect(name):
    cfg = load()
    devices = list_devices(cfg)
    if name in devices:
        p = dict()
        p["domain"] = cfg["server"]
        p["port"] = cfg["port"]
        p["ca_cert"] = cfg["ca_cert"]
        device = cfg["devices"][name]
        key = mangle(name)
        p["uuid"] = device["hardware"]["uuid"]
        p["devName"] = name
        p["devType"] = device["hardware"]["type"]
        p["hdwareVersion"] = device["hardware"]["version"]
        p["fmwareVersion"] = device["firmware"]["version"]
        return GenericBulb("token", key, None, **p)
