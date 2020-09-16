import logging
import os
import sys
from enum import Enum, auto

import click

from pdst.Config import Config
from pdst.MetadataService import MetadataService
from pdst.db.PlexDao import PlexDao
from pdst.image.ImageGenerator import ImageGenerator
from pdst.image.ImageService import ImageService
from pdst.SportService import SportService

log = logging.getLogger(__name__)

CONTEXT_SETTINGS = dict(auto_envvar_prefix="PDST")


class Environment:
    def __init__(self):
        self.verbose = 0
        self.config = None
        self.force = None
        self.recurse = False
        self.mode = None

        self.sportService = None
        self.imageService = None
        self.outDir = os.getcwd()

    def log(self, msg, *args, **kwargs):
        if args:
            msg %= args
        click.echo(msg, **kwargs)

    def vlog(self, msg, *args, **kwargs):
        if self.verbose > 0:
            self.log(msg, *args, **kwargs)


class OpMode(Enum):
    IMAGE = auto()
    VIDEO = auto()

    @staticmethod
    def fromString(string):
        return {
            'image': OpMode.IMAGE,
            'video': OpMode.VIDEO
        }.get(string.lower(), None)


def verbosity_option(f):
    def callback(ctx, param, value):
        env = ctx.ensure_object(Environment)
        env.verbose = value

        root = logging.getLogger('pdst')
        root.setLevel(logging.WARNING)

        handler = logging.StreamHandler(sys.stdout)
        handler.setLevel(logging.WARNING)

        formatter = logging.Formatter('%(levelname)s: %(message)s')
        handler.setFormatter(formatter)
        root.addHandler(handler)

        if env.verbose > 0:
            root.setLevel(logging.INFO)
            handler.setLevel(logging.INFO)
        if env.verbose > 1:
            root.setLevel(logging.DEBUG)
            handler.setLevel(logging.DEBUG)

        return value

    return click.option("-v", "--verbose", count=True,
                        help="Sets verbosity level",
                        expose_value=False, callback=callback)(f)


def config_option(f):
    def callback(ctx, param, value):
        env = ctx.ensure_object(Environment)
        env.configFile = value
        env.config = Config(value)
        env.imageGenerator = ImageGenerator(env.config)
        env.sportService = SportService(env.config)
        env.metadataService = MetadataService(PlexDao(env.config.plexLibPath), env.sportService)
        env.imageService = ImageService(env.config,
                                        imageGen=env.imageGenerator,
                                        sportService=env.sportService,
                                        metadataService=env.metadataService)

        return value

    return click.option("-c", "--config", type=click.Path(exists=True),
                        envvar='PDST_CFG',
                        help="Specify a configuration JSON file",
                        expose_value=False, callback=callback)(f)


def recurse_option(f):
    def callback(ctx, param, value):
        env = ctx.ensure_object(Environment)
        env.recurse = value
        return value

    return click.option("-R", "--recurse", is_flag=True,
                        help="Recursively traverse directories",
                        expose_value=False, callback=callback)(f)


def out_dir_option(f):
    def callback(ctx, param, out):
        env = ctx.ensure_object(Environment)
        if out is None:
            if env.mode is OpMode.IMAGE:
                env.outDir = os.getcwd()
            else:
                env.outDir = None
        else:
            env.outDir = os.path.abspath(click.format_filename(out))

        return out

    return click.option("-o", "--out", type=click.Path(exists=True),
                        help="Sets the output directory for created files",
                        expose_value=False, callback=callback)(f)


def force_option(f):
    def callback(ctx, param, value):
        env = ctx.ensure_object(Environment)
        env.force = value
        return value

    return click.option("-f", "--force", is_flag=True,
                        help="Process files that would otherwise be skipped",
                        expose_value=False, callback=callback)(f)


def mode_option(f):
    def callback(ctx, param, value):
        env = ctx.ensure_object(Environment)
        env.mode = OpMode.fromString(value)
        return value

    return click.option('-m', '--mode', type=click.Choice(['video', 'image'], case_sensitive=False),
                        default='video', help="Operation mode (type of files to process)",
                        expose_value=False, callback=callback)(f)


def common_options(f):
    f = verbosity_option(f)
    f = config_option(f)
    f = recurse_option(f)
    f = force_option(f)
    f = out_dir_option(f)
    f = mode_option(f)
    return f


pass_environment = click.make_pass_decorator(Environment, ensure=True)
cmd_folder = os.path.abspath(os.path.join(os.path.dirname(__file__), "commands"))


class ComplexCLI(click.MultiCommand):
    def list_commands(self, ctx):
        rv = []
        for filename in os.listdir(cmd_folder):
            if filename.endswith(".py") and filename.startswith("cmd_"):
                rv.append(filename[4:-3])
        rv.sort()
        return rv

    def get_command(self, ctx, name):
        try:
            mod = __import__(f"pdst.commands.cmd_{name}", None, None, ["cli"])
        except ImportError:
            return
        return mod.cli


@click.command(cls=ComplexCLI, context_settings=CONTEXT_SETTINGS)
@click.version_option()
@pass_environment
def cli(ctx):
    pass
