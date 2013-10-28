from unittest.mock import Mock

from eos.const.eos import Location, State
from eos.const.eve import Attribute
from eos.fit.holder.item import Drone, Ship, Implant
from eos.tests.stat_tracker.stat_testcase import StatTestCase


class TestDroneBayVolume(StatTestCase):
    """Check functionality of drone bay volume stats"""

    def test_output(self):
        # Check that modified attribute of ship is used
        ship_item = self.ch.type_(type_id=1, attributes={Attribute.drone_capacity: 10})
        ship_holder = Mock(state=State.offline, item=ship_item, _location=None, spec_set=Ship)
        ship_holder.attributes = {Attribute.drone_capacity: 50}
        self.set_ship(ship_holder)
        self.assertEqual(self.st.dronebay.output, 50)
        self.set_ship(None)
        self.assertEqual(len(self.log), 0)
        self.assert_stat_buffers_empty()

    def test_output_no_ship(self):
        # None for output when no ship
        self.assertIsNone(self.st.dronebay.output)
        self.assertEqual(len(self.log), 0)
        self.assert_stat_buffers_empty()

    def test_output_no_attr(self):
        # None for output when no attribute on ship
        ship_item = self.ch.type_(type_id=1)
        ship_holder = Mock(state=State.offline, item=ship_item, _location=None, spec_set=Ship)
        ship_holder.attributes = {}
        self.set_ship(ship_holder)
        self.assertIsNone(self.st.dronebay.output)
        self.set_ship(None)
        self.assertEqual(len(self.log), 0)
        self.assert_stat_buffers_empty()

    def test_use_single_no_rounding(self):
        item = self.ch.type_(type_id=1, attributes={Attribute.volume: 0})
        holder = Mock(state=State.offline, item=item, _location=Location.space, spec_set=Drone)
        holder.attributes = {Attribute.volume: 55.5555555555}
        self.fit.drones.add(holder)
        self.track_holder(holder)
        self.assertEqual(self.st.dronebay.used, 55.5555555555)
        self.untrack_holder(holder)
        self.assertEqual(len(self.log), 0)
        self.assert_stat_buffers_empty()

    def test_use_multiple(self):
        item = self.ch.type_(type_id=1, attributes={Attribute.volume: 0})
        holder1 = Mock(state=State.offline, item=item, _location=Location.space, spec_set=Drone)
        holder1.attributes = {Attribute.volume: 50}
        self.fit.drones.add(holder1)
        self.track_holder(holder1)
        holder2 = Mock(state=State.offline, item=item, _location=Location.space, spec_set=Drone)
        holder2.attributes = {Attribute.volume: 30}
        self.fit.drones.add(holder2)
        self.track_holder(holder2)
        self.assertEqual(self.st.dronebay.used, 80)
        self.untrack_holder(holder1)
        self.untrack_holder(holder2)
        self.assertEqual(len(self.log), 0)
        self.assert_stat_buffers_empty()

    def test_use_negative(self):
        item = self.ch.type_(type_id=1, attributes={Attribute.volume: 0})
        holder1 = Mock(state=State.offline, item=item, _location=Location.space, spec_set=Drone)
        holder1.attributes = {Attribute.volume: 50}
        self.fit.drones.add(holder1)
        self.track_holder(holder1)
        holder2 = Mock(state=State.offline, item=item, _location=Location.space, spec_set=Drone)
        holder2.attributes = {Attribute.volume: -30}
        self.fit.drones.add(holder2)
        self.track_holder(holder2)
        self.assertEqual(self.st.dronebay.used, 20)
        self.untrack_holder(holder1)
        self.untrack_holder(holder2)
        self.assertEqual(len(self.log), 0)
        self.assert_stat_buffers_empty()

    def test_use_none(self):
        self.assertEqual(self.st.dronebay.used, 0)
        self.assertEqual(len(self.log), 0)
        self.assert_stat_buffers_empty()

    def test_use_other_class(self):
        # Make sure holders placed to other containers are unaffected
        item = self.ch.type_(type_id=1, attributes={Attribute.volume: 0})
        holder = Mock(state=State.offline, item=item, _location=Location.space, spec_set=Drone)
        holder.attributes = {Attribute.volume: 30}
        self.fit.rigs.add(holder)
        self.track_holder(holder)
        self.assertEqual(self.st.dronebay.used, 0)
        self.untrack_holder(holder)
        self.assertEqual(len(self.log), 0)
        self.assert_stat_buffers_empty()

    def test_cache(self):
        ship_item = self.ch.type_(type_id=1, attributes={Attribute.drone_capacity: 10})
        ship_holder = Mock(state=State.offline, item=ship_item, _location=None, spec_set=Ship)
        ship_holder.attributes = {Attribute.drone_capacity: 50}
        self.set_ship(ship_holder)
        item = self.ch.type_(type_id=2, attributes={Attribute.volume: 0})
        holder1 = Mock(state=State.offline, item=item, _location=Location.space, spec_set=Drone)
        holder1.attributes = {Attribute.volume: 50}
        self.fit.drones.add(holder1)
        self.track_holder(holder1)
        holder2 = Mock(state=State.offline, item=item, _location=Location.space, spec_set=Drone)
        holder2.attributes = {Attribute.volume: 30}
        self.fit.drones.add(holder2)
        self.track_holder(holder2)
        self.assertEqual(self.st.dronebay.used, 80)
        self.assertEqual(self.st.dronebay.output, 50)
        holder1.attributes[Attribute.volume] = 10
        ship_holder.attributes[Attribute.drone_capacity] = 60
        self.assertEqual(self.st.dronebay.used, 80)
        self.assertEqual(self.st.dronebay.output, 50)
        self.set_ship(None)
        self.untrack_holder(holder1)
        self.untrack_holder(holder2)
        self.assertEqual(len(self.log), 0)
        self.assert_stat_buffers_empty()

    def test_volatility(self):
        ship_item = self.ch.type_(type_id=1, attributes={Attribute.drone_capacity: 10})
        ship_holder = Mock(state=State.offline, item=ship_item, _location=None, spec_set=Ship)
        ship_holder.attributes = {Attribute.drone_capacity: 50}
        self.set_ship(ship_holder)
        item = self.ch.type_(type_id=2, attributes={Attribute.volume: 0})
        holder1 = Mock(state=State.offline, item=item, _location=Location.space, spec_set=Drone)
        holder1.attributes = {Attribute.volume: 50}
        self.fit.drones.add(holder1)
        self.track_holder(holder1)
        holder2 = Mock(state=State.offline, item=item, _location=Location.space, spec_set=Drone)
        holder2.attributes = {Attribute.volume: 30}
        self.fit.drones.add(holder2)
        self.track_holder(holder2)
        self.assertEqual(self.st.dronebay.used, 80)
        self.assertEqual(self.st.dronebay.output, 50)
        holder1.attributes[Attribute.volume] = 10
        ship_holder.attributes[Attribute.drone_capacity] = 60
        self.st._clear_volatile_attrs()
        self.assertEqual(self.st.dronebay.used, 40)
        self.assertEqual(self.st.dronebay.output, 60)
        self.set_ship(None)
        self.untrack_holder(holder1)
        self.untrack_holder(holder2)
        self.assertEqual(len(self.log), 0)
        self.assert_stat_buffers_empty()
