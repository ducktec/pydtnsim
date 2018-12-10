""" Testfile for the contact.py implementations """
import logging

from pydtnsim import Contact
from pydtnsim.backend import QSim

ptsimTestLogger = logging.getLogger('ptsimtest')
ptsimTestLogger.setLevel(logging.DEBUG)
logging.basicConfig(level=logging.DEBUG)


def test_contact_test_sorting():
    """Test function to verify correct sorting behaviour for Contact objects"""
    env = QSim()
    contactlist = []
    c1 = Contact(150, 310, 100, 'source', 'peer')
    c2 = Contact(100, 320, 100, 'source', 'peer')
    c3 = Contact(250, 330, 100, 'source', 'peer')
    contactlist.append(c1)
    contactlist.append(c2)
    contactlist.append(c3)
    assert (len(contactlist) == 3)
    sorted_contactlist = sorted(contactlist)
    assert (sorted_contactlist.pop(0) == c2)
    assert (sorted_contactlist.pop(0) == c1)
    assert (sorted_contactlist.pop(0) == c3)
