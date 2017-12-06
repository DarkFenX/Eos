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


from eos.const.eve import EffectId
from eos.eve_object import EffectFactory
from .effect import add_aar_modifier


EffectFactory.reg_cust_instance_by_id(
    add_aar_modifier, EffectId.fueled_armor_repair)
EffectFactory.reg_cust_instance_by_id(
    add_aar_modifier, EffectId.module_bonus_ancillary_remote_armor_repairer)
