import logging

import click

log = logging.getLogger(__name__)

CONTEXT_SETTINGS = dict(auto_envvar_prefix="PLEXTOOLS")


class Environment:
    def __init__(self):
        self.verbose = 0

    def log(self, msg, *args):
        if args:
            msg %= args
        click.echo(msg)

    def vlog(self, msg, *args):
        if self.verbose > 0:
            self.log(msg, *args)


pass_environment = click.make_pass_decorator(Environment, ensure=True)


@click.command(context_settings=CONTEXT_SETTINGS)
@click.version_option()
@pass_environment
def cli():
    pass
