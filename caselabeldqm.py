# Copyright 2021 D-Wave Systems Inc.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

from dimod import DiscreteQuadraticModel


class CaseLabelDQM(DiscreteQuadraticModel):
    '''DiscreteQuadraticModel that identifies variable cases using arbitrary
    labels instead of integers.
    '''
    def __init__(self, *args, **kwargs):
        DiscreteQuadraticModel.__init__(self, *args, **kwargs)
        assert not hasattr(self, '_case_label')
        self._case_label = {}
        assert not hasattr(self, '_label_case')
        self._label_case = {}

    def add_variable(self, cases, label):
        """Add a discrete variable to the model.

        Args:
            cases (int or iterable):
                The number of cases in the variable, or an iterable containing
                the labels that will identify the cases of the variable.

            label (hashable):
                The name of the variable.

        Returns:
            None

        Raises:
            ValueError: If the variable exists or if any of the case labels are
                not unique.

            TypeError: If `label` is not hashable or if any of the case labels
                are not hashable.
        """
        var = label
        if var in self._label_case:
            raise ValueError(f'variable exists: {var}')

        if isinstance(cases, int):
            cases = list(range(cases))

        if len(set(cases)) != len(cases):
            raise ValueError(f'cases for variable {var} are not unique')

        self._label_case[var] = {case: k for k, case in enumerate(cases)}
        self._case_label[var] = {k: case for k, case in enumerate(cases)}
        DiscreteQuadraticModel.add_variable(self, len(cases), label=var)

    def set_linear_case(self, var, case, bias):
        """Set the linear bias associated with case `case` of variable `var`.

        Args:
            var: A variable in the model.

            case: The case of `var`.

            bias (float): The linear bias.
        """
        k = self._label_case[var][case]
        DiscreteQuadraticModel.set_linear_case(self, var, k, bias)

    def set_quadratic_case(self, u, u_case, v, v_case, bias):
        """Set the bias associated with the interaction between two cases of
        variables `u` and `v`.

        Args:
            u: A variable in the model.

            u_case: The case of `u`.

            v: A variable in the model.

            v_case: The case of `v`.

            bias (float): The quadratic bias.
        """
        k = self._label_case[u][u_case]
        m = self._label_case[v][v_case]
        DiscreteQuadraticModel.set_quadratic_case(self, u, k, v, m, bias)

    def map_sample(self, sample):
        """Translate the values assigned to each variable in the sample.
        """
        return {var: self._case_label[var][value]
                for var, value in sample.items()}
