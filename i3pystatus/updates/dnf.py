from i3pystatus.updates import Backend
try:
    import dnf
    HAS_DNF_BINDINGS = True
except ImportError:
    HAS_DNF_BINDINGS = False


class Dnf(Backend):
    """
    Gets updates for RPM-based distributions using the `DNF API`_

    The notification body consists of the package name and version for each
    available update.

    .. _`DNF API`: http://dnf.readthedocs.io/en/latest/api.html
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
