from routers.ssh_autodetect import ssh_autodetect
from routers.ssh_autodetect_generic import ssh_autodetect_generic
from routers.ssh_brctl import ssh_brctl
from routers.fake_router import fake_router
from routers.ssh_routeros import ssh_routeros
from routers.ssh_routeros_arp import ssh_routeros_arp
from routers.ssh_zyxel_arp import ssh_zyxel_arp
from routers.ssh_unifi_usg_arp import ssh_unifi_usg_arp


poll_methods = {
    'default': ssh_autodetect,
    'forcegeneric': ssh_autodetect_generic,
    'brctl': ssh_brctl,
    'routeros': ssh_routeros,
    'routeros-arp': ssh_routeros_arp,
    'zyxel-arp': ssh_zyxel_arp,
    'unifiusg-arp': ssh_unifi_usg_arp,
    'dummy': fake_router
}