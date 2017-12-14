# ==============================================================================
# Copyright (C) 2011 Diego Duclos
# Copyright (C) 2011-2017 Anton Vorobyov
#
# This file is part of Eos.
#
# Eos is free software: you can redistribute it and/or modify
# it under the terms of the GNU Lesser General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# Eos is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Lesser General Public License for more details.
#
# You should have received a copy of the GNU Lesser General Public License
# along with Eos. If not, see <http://www.gnu.org/licenses/>.
# ==============================================================================


from logging import getLogger

from eos.const.eos import EosTypeId
from eos.const.eos import ModDomain
from eos.const.eos import ModTgtFilter
from eos.util.keyed_storage import KeyedStorage
from .exception import UnexpectedDomainError
from .exception import UnknownTgtFilterError


logger = getLogger(__name__)


class AffectionRegister:
    """Keeps track of connections between affectors and affectees.

    Deals only with affectors which have dogma modifiers. Having information
    about connections is hard requirement for efficient partial attribute
    recalculation.
    """

    def __init__(self, calc_svc):
        self.__calc_svc = calc_svc

        # All known items
        # Format: {items}
        self.__affectee = set()

        # Items belonging to certain domain
        # Format: {domain: set(affectee items)}
        self.__affectee_domain = KeyedStorage()

        # Items belonging to certain domain and group
        # Format: {(domain, group ID): set(affectee items)}
        self.__affectee_domain_group = KeyedStorage()

        # Items belonging to certain domain and having certain skill requirement
        # Format: {(domain, skill type ID): set(affectee items)}
        self.__affectee_domain_skillrq = KeyedStorage()

        # Owner-modifiable items which have certain skill requirement
        # Format: {skill type ID: set(affectee items)}
        self.__affectee_owner_skillrq = KeyedStorage()

        # Affectors which target 'other' location are always stored here,
        # regardless if they actually affect something or not
        # Format: {carrier item: set(affectors)}
        self.__affector_item_other = KeyedStorage()

        # Affectors which should affect only one item (ship, character or self),
        # when this item is not registered as affectee
        # Format: {carrier item: set(affectors)}
        self.__affector_item_awaitable = KeyedStorage()

        # All active affectors which target specific item (via ship, character,
        # other reference or self) are kept here
        # Format: {affectee item: set(affectors)}
        self.__affector_item_active = KeyedStorage()

        # Affectors influencing all items belonging to certain domain
        # Format: {domain: set(affectors)}
        self.__affector_domain = KeyedStorage()

        # Affectors influencing items belonging to certain domain and group
        # Format: {(domain, group ID): set(affectors)}
        self.__affector_domain_group = KeyedStorage()

        # Affectors influencing items belonging to certain domain and having
        # certain skill requirement
        # Format: {(domain, skill type ID): set(affectors)}
        self.__affector_domain_skillrq = KeyedStorage()

        # Affectors influencing owner-modifiable items which have certain skill
        # requirement
        # Format: {skill type ID: set(affectors)}
        self.__affector_owner_skillrq = KeyedStorage()

    # Helpers for affectee getter - they find map and get data from it according
    # to passed affector
    def __get_affectees_item_self(self, affector):
        return self.__get_registered_affectees([affector.carrier_item])

    def __get_affectees_item_character(self, _):
        character = self.__calc_svc._current_char
        if character is not None:
            return self.__get_registered_affectees([character])
        else:
            return ()

    def __get_affectees_item_ship(self, _):
        ship = self.__calc_svc._current_ship
        if ship is not None:
            return self.__get_registered_affectees([ship])
        else:
            return ()

    def __get_affectees_item_other(self, affector):
        return self.__get_registered_affectees(affector.carrier_item._others)

    __affectees_getters_item = {
        ModDomain.self: __get_affectees_item_self,
        ModDomain.character: __get_affectees_item_character,
        ModDomain.ship: __get_affectees_item_ship,
        ModDomain.other: __get_affectees_item_other}

    def __get_affectees_item(self, affector):
        try:
            getter = self.__affectees_getters_item[affector.modifier.tgt_domain]
        except KeyError as e:
            raise UnexpectedDomainError(affector.modifier.tgt_domain) from e
        else:
            return getter(self, affector)

    def __get_affectees_domain(self, affector):
        domain = self.__contextize_tgt_filter_domain(affector)
        return self.__affectee_domain.get(domain, ())

    def __get_affectees_domain_group(self, affector):
        domain = self.__contextize_tgt_filter_domain(affector)
        group_id = affector.modifier.tgt_filter_extra_arg
        return self.__affectee_domain_group.get((domain, group_id), ())

    def __get_affectees_domain_skillrq(self, affector):
        domain = self.__contextize_tgt_filter_domain(affector)
        skill_type_id = affector.modifier.tgt_filter_extra_arg
        if skill_type_id == EosTypeId.current_self:
            skill_type_id = affector.carrier_item._type_id
        return self.__affectee_domain_skillrq.get((domain, skill_type_id), ())

    def __get_affectees_owner_skillrq(self, affector):
        skill_type_id = affector.modifier.tgt_filter_extra_arg
        if skill_type_id == EosTypeId.current_self:
            skill_type_id = affector.carrier_item._type_id
        return self.__affectee_owner_skillrq.get(skill_type_id, ())

    __affectees_getters = {
        ModTgtFilter.item: __get_affectees_item,
        ModTgtFilter.domain: __get_affectees_domain,
        ModTgtFilter.domain_group: __get_affectees_domain_group,
        ModTgtFilter.domain_skillrq: __get_affectees_domain_skillrq,
        ModTgtFilter.owner_skillrq: __get_affectees_owner_skillrq}

    # Affectee processing
    def get_affectees(self, affector):
        """Get iterable with items influenced by passed affector."""
        try:
            mod_tgt_filter = affector.modifier.tgt_filter
            try:
                getter = self.__affectees_getters[mod_tgt_filter]
            except KeyError as e:
                raise UnknownTgtFilterError(mod_tgt_filter) from e
            else:
                return getter(self, affector)
        except Exception as e:
            self.__handle_affector_errors(e, affector)
            return ()

    def register_affectee(self, affectee_item):
        """Add passed affectee item to register.

        We track affectees to efficiently update attributes when set of items
        influencing them changes.
        """
        self.__affectee.add(affectee_item)
        for key, affectee_map in self.__get_affectee_storages(affectee_item):
            affectee_map.add_data_entry(key, affectee_item)
        # When item like ship is added, there might already be affectors which
        # should affect it. Make sure that they are activated by calling this
        # method
        self.__activate_direct_affectors(affectee_item)

    def unregister_affectee(self, affectee_item):
        """Remove passed affectee item from register."""
        self.__affectee.discard(affectee_item)
        for key, affectee_map in self.__get_affectee_storages(affectee_item):
            affectee_map.rm_data_entry(key, affectee_item)
        # Deactivate all affectors for item being unregistered
        self.__deactivate_direct_affectors(affectee_item)

    def __get_affectee_storages(self, affectee_item):
        """Return all places where passed affectee should be stored.

        Returns:
            Iterable with multiple elements, where each element is tuple in
            (key, affectee map) format.
        """
        affectee_storages = []
        domain = affectee_item._modifier_domain
        if domain is not None:
            # Domain
            affectee_storages.append((domain, self.__affectee_domain))
            group_id = affectee_item._type.group_id
            if group_id is not None:
                # Domain and group
                affectee_storages.append(
                    ((domain, group_id), self.__affectee_domain_group))
            for skill_type_id in affectee_item._type.required_skills:
                # Domain and skill requirement
                affectee_storages.append(
                    ((domain, skill_type_id), self.__affectee_domain_skillrq))
        if affectee_item._owner_modifiable is True:
            for skill_type_id in affectee_item._type.required_skills:
                # Owner-modifiable and skill requirement
                affectee_storages.append(
                    (skill_type_id, self.__affectee_owner_skillrq))
        return affectee_storages

    def __activate_direct_affectors(self, affectee_item):
        """Activate direct affectors which should affect passed item."""
        affectors_awaitable = set()
        for carrier_item, affectors in self.__affector_item_awaitable.items():
            for affector in affectors:
                domain = affector.modifier.tgt_domain
                # Ship
                if domain == ModDomain.ship:
                    if affectee_item is self.__calc_svc._current_ship:
                        affectors_awaitable.add(affector)
                # Character
                elif domain == ModDomain.character:
                    if affectee_item is self.__calc_svc._current_char:
                        affectors_awaitable.add(affector)
                # Self
                elif domain == ModDomain.self:
                    if affectee_item is carrier_item:
                        affectors_awaitable.add(affector)
        # Move awaitable affectors from awaitable storage to active storage
        if affectors_awaitable:
            for affector in affectors_awaitable:
                self.__affector_item_awaitable.rm_data_entry(
                    affector.carrier_item, affector)
            self.__affector_item_active.add_data_set(
                affectee_item, affectors_awaitable)
        # Other
        affectors_other = set()
        for carrier_item, affectors in self.__affector_item_other.items():
            carrier_others = carrier_item._others
            for affector in affectors:
                if affectee_item in carrier_others:
                    affectors_other.add(affector)
        # Just add affectors to active storage, 'other' affectors should never
        # be removed from 'other'-specific storage
        if affectors_other:
            self.__affector_item_active.add_data_set(
                affectee_item, affectors_other)

    def __deactivate_direct_affectors(self, affectee_item):
        """Deactivate direct affectors which affect passed item."""
        if affectee_item not in self.__affector_item_active:
            return
        affectors_awaitable = set()
        for affector in self.__affector_item_active.get(affectee_item, ()):
            domain = affector.modifier.tgt_domain
            # Ship, character and self
            if domain in (ModDomain.ship, ModDomain.character, ModDomain.self):
                affectors_awaitable.add(affector)
        # Remove all affectors influencing this item directly, including 'other'
        del self.__affector_item_active[affectee_item]
        for affector in affectors_awaitable:
            self.__affector_item_awaitable.add_data_entry(
                affector.carrier_item, affector)

    # Affector processing
    def get_affectors(self, affectee_item):
        """Get all affectors, which influence passed item."""
        affectors = set()
        if affectee_item not in self.__affectee:
            return affectors
        # Item
        affectors.update(self.__affector_item_active.get(affectee_item, ()))
        domain = affectee_item._modifier_domain
        if domain is not None:
            # Domain
            affectors.update(self.__affector_domain.get(domain, ()))
            # Domain and group
            affectors.update(self.__affector_domain_group.get(
                (domain, affectee_item._type.group_id), ()))
            for skill_type_id in affectee_item._type.required_skills:
                # Domain and skill requirement
                affectors.update(self.__affector_domain_skillrq.get(
                    (domain, skill_type_id), ()))
        if affectee_item._owner_modifiable is True:
            for skill_type_id in affectee_item._type.required_skills:
                # Owner-modifiable and skill requirement
                affectors.update(self.__affector_owner_skillrq.get(
                    skill_type_id, ()))
        return affectors

    def register_affector(self, affector):
        """Make register aware of the affector.

        It makes it possible for the affector to modify other items.
        """
        try:
            affector_storages = self.__get_affector_storages(affector)
        except Exception as e:
            self.__handle_affector_errors(e, affector)
        else:
            for key, affector_map in affector_storages:
                affector_map.add_data_entry(key, affector)

    def unregister_affector(self, affector):
        """Remove the affector from register.

        It makes it impossible for the affector to modify any other items.
        """
        try:
            affector_storages = self.__get_affector_storages(affector)
        except Exception as e:
            self.__handle_affector_errors(e, affector)
        else:
            for key, affector_map in affector_storages:
                affector_map.rm_data_entry(key, affector)

    # Helpers for affector registering/unregistering, they find affector maps
    # and keys to them
    def __get_affector_storages_item_self(self, affector):
        if affector.carrier_item in self.__affectee:
            return [(affector.carrier_item, self.__affector_item_active)]
        else:
            return [(affector.carrier_item, self.__affector_item_awaitable)]

    def __get_affector_storages_item_character(self, affector):
        character = self.__calc_svc._current_char
        if character is not None and character in self.__affectee:
            return [(character, self.__affector_item_active)]
        else:
            return [(affector.carrier_item, self.__affector_item_awaitable)]

    def __get_affector_storages_item_ship(self, affector):
        ship = self.__calc_svc._current_ship
        if ship is not None and ship in self.__affectee:
            return [(ship, self.__affector_item_active)]
        else:
            return [(affector.carrier_item, self.__affector_item_awaitable)]

    def __get_affector_storages_item_other(self, affector):
        # Affectors with 'other' modifiers are always stored in their special
        # place
        storages = [(affector.carrier_item, self.__affector_item_other)]
        # And all those which have valid target are also stored in storage for
        # active direct affectors
        for other_item in self.__get_registered_affectees(
            affector.carrier_item._others
        ):
            storages.append((other_item, self.__affector_item_active))
        return storages

    __affector_storages_getters_item = {
        ModDomain.self: __get_affector_storages_item_self,
        ModDomain.character: __get_affector_storages_item_character,
        ModDomain.ship: __get_affector_storages_item_ship,
        ModDomain.other: __get_affector_storages_item_other}

    def __get_affector_storages_item(self, affector):
        tgt_domain = affector.modifier.tgt_domain
        try:
            getter = self.__affector_storages_getters_item[tgt_domain]
        except KeyError as e:
            raise UnexpectedDomainError(tgt_domain) from e
        else:
            return getter(self, affector)

    def __get_affector_storages_domain(self, affector):
        domain = self.__contextize_tgt_filter_domain(affector)
        return [(domain, self.__affector_domain)]

    def __get_affector_storages_domain_group(self, affector):
        domain = self.__contextize_tgt_filter_domain(affector)
        group_id = affector.modifier.tgt_filter_extra_arg
        return [((domain, group_id), self.__affector_domain_group)]

    def __get_affector_storages_domain_skillrq(self, affector):
        domain = self.__contextize_tgt_filter_domain(affector)
        skill_type_id = affector.modifier.tgt_filter_extra_arg
        if skill_type_id == EosTypeId.current_self:
            skill_type_id = affector.carrier_item._type_id
        return [((domain, skill_type_id), self.__affector_domain_skillrq)]

    def __get_affector_storages_owner_skillrq(self, affector):
        skill_type_id = affector.modifier.tgt_filter_extra_arg
        if skill_type_id == EosTypeId.current_self:
            skill_type_id = affector.carrier_item._type_id
        return [(skill_type_id, self.__affector_owner_skillrq)]

    __affector_storages_getters = {
        ModTgtFilter.item: __get_affector_storages_item,
        ModTgtFilter.domain: __get_affector_storages_domain,
        ModTgtFilter.domain_group: __get_affector_storages_domain_group,
        ModTgtFilter.domain_skillrq: __get_affector_storages_domain_skillrq,
        ModTgtFilter.owner_skillrq: __get_affector_storages_owner_skillrq}

    def __get_affector_storages(self, affector):
        """Get places where passed affector should be stored.

        Args:
            affector: Affector, for which storage is looked up.

        Returns:
            Iterable with tuples in (key, affector map) format, which defines
            where affector should be stored.

        Raises:
            UnexpectedDomainError: If affector's modifier target domain is not
                supported for context of passed affector.
            UnknownTgtFilterError: If affector's modifier filter type is not
                supported.
        """
        tgt_filter = affector.modifier.tgt_filter
        try:
            getter = self.__affector_storages_getters[tgt_filter]
        except KeyError as e:
            raise UnknownTgtFilterError(affector.modifier.tgt_filter) from e
        else:
            return getter(self, affector)

    # Shared helpers
    def __get_registered_affectees(self, items):
        return self.__affectee.intersection(items)

    def __contextize_tgt_filter_domain(self, affector):
        """Convert relative domain into absolute.

        Applicable only to en-masse modifications. That is, when modification
        affects multiple items in target domain. If modification targets single
        item, it should not be handled via this method.

        Raises:
            UnexpectedDomainError: If affector's modifier target domain is not
                supported.
        """
        carrier_item = affector.carrier_item
        domain = affector.modifier.tgt_domain
        if domain == ModDomain.self:
            if carrier_item is self.__calc_svc._current_ship:
                return ModDomain.ship
            elif carrier_item is self.__calc_svc._current_char:
                return ModDomain.character
            else:
                raise UnexpectedDomainError(domain)
        # Just return untouched domain for all other valid cases. Valid cases
        # include 'globally' visible (within the fit scope) domains only. I.e.
        # if item on fit refers this target domain, it should always refer the
        # same target item regardless of source item.
        elif domain in (ModDomain.character, ModDomain.ship):
            return domain
        # Raise error if domain is invalid
        else:
            raise UnexpectedDomainError(domain)

    def __handle_affector_errors(self, error, affector):
        """Handles affector-related exceptions.

        Multiple register methods which get data based on passed affector raise
        similar exceptions. To handle them in consistent fashion, it is done
        from centralized place - this method. If error cannot be handled by the
        method, it is re-raised.
        """
        if isinstance(error, UnexpectedDomainError):
            msg = (
                'malformed modifier on item type {}: '
                'unsupported target domain {}'
            ).format(affector.carrier_item._type_id, error.args[0])
            logger.warning(msg)
        elif isinstance(error, UnknownTgtFilterError):
            msg = (
                'malformed modifier on item type {}: invalid target filter {}'
            ).format(affector.carrier_item._type_id, error.args[0])
            logger.warning(msg)
        else:
            raise error
