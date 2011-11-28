#===============================================================================
# Copyright (C) 2011 Diego Duclos
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
#===============================================================================

import collections

class ExpressionInfo(object):
    """
    The ExpressionInfo objects are the actual "Core" of eos,
    they are what eventually applies an effect onto a fit.
    Which causes modules to actually do useful(tm) things.
    They are typically generated by the ExpressionBuild class
    but nothing prevents a user from making some of his own and running them onto a fit
    """
    def __init__(self):
        self.filters = []
        """
        List of ExpressionFilter objects, each describing a single filter. ALL filters must be matched before anything is done
        """

        self.operation = None
        """
        Which operation should be applied.
        Possible values: <None implemented yet, getting to that :)>
        Any other values will be ignored, causing the ExpressionInfo to do nothing
        """

        self.target = None
        """
        The target of this expression.
        Possible values: <None implemented yet, getting to that :)>
        Any other values will be ignored, causing the ExpressionInfo to do nothing
        """

        self.targetAttributeId = None
        """
        Which attribute will be affected by the operation on the target.
        This will be used as dictionary lookup key on all matched targets (if any)
        """

        self.sourceAttributeId = None
        """
        Which source attribute will be used as calculation base for the operation.
        This will be used as dictionary lookup key on the owner passed to the run method
        """

    def validate(self):
        return self.operation is not None \
           and self.target is not None \
           and self.targetAttributeId is not None \
           and self.sourceAttributeId is not None

ExpressionFilter = collections.namedtuple('ExpressionFilter', ('type', 'value'))
