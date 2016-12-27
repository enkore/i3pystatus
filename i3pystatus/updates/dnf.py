from i3pystatus.updates import Backend
import sys

# Remove first dir from sys.path to avoid shadowing dnf module from
# site-packages dir when this module executed directly on the CLI.
__module_dir = sys.path.pop(0)
try:
    import dnf
    HAS_DNF_BINDINGS = True
except ImportError:
    HAS_DNF_BINDINGS = False
finally:
    # Replace the directory we popped earlier
    sys.path.insert(0, __module_dir)


class Dnf(Backend):
    """
    Gets updates for RPM-based distributions using the `DNF API`_

    The notification body consists of the package name and version for each
    available update.

    .. _`DNF API`: http://dnf.readthedocs.io/en/latest/api.html

    .. note::
        Users running i3pystatus from a virtualenv may see the updates display
        as ``?`` due to an inability to import the ``dnf`` module. To ensure
        that i3pystatus can access the DNF Python bindings, the virtualenv
        should be created with ``--system-site-packages``.

        If using `pyenv-virtualenv`_, the virtualenv must additionally be
        created to use the system Python binary:

        .. code-block:: bash

            $ pyenv virtualenv --system-site-packages --python=/usr/bin/python3 pyenv_name

        To invoke i3pystatus with this virtualenv, your ``bar`` section in
        ``~/.config/i3/config`` would look like this:

        .. code-block:: bash

            bar {
                position top
                status_command PYENV_VERSION=pyenv_name python /path/to/i3pystatus/script.py
            }

    .. _`pyenv-virtualenv`: https://github.com/yyuu/pyenv-virtualenv
    """

    @property
    def updates(self):
        if HAS_DNF_BINDINGS:
            try:
                with dnf.Base() as base:
                    base.read_all_repos()
                    base.fill_sack()
                    upgrades = base.sack.query().upgrades().run()

                notif_body = ''.join([
                    '%s: %s-%s\n' % (pkg.name, pkg.version, pkg.release)
                    for pkg in upgrades
                ])
                return len(upgrades), notif_body
            except Exception as exc:
                self.logger.error('DNF update check failed', exc_info=True)
                return '?', exc.__str__()
        else:
            return '?', 'Failed to import DNF Python bindings'

Backend = Dnf

if __name__ == "__main__":
    """
    Call this module directly; Print the update count and notification body.
    """
    print("Updates: {}\n\n{}".format(*Backend().updates))
