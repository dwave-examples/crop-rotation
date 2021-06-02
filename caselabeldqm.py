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
    labels instead of ints.
    '''
    def __init__(self, *args, **kwargs):
        DiscreteQuadraticModel.__init__(self, *args, **kwargs)
        assert not hasattr(self, '_case_label')
        self._case_label = {}
        assert not hasattr(self, '_label_case')
        self._label_case = {}

    def add_variable(self, cases, label):
        var = label
        if var in self._label_case:
            raise Exception(f'variable exists: {var}')

        if isinstance(cases, int):
            cases = list(range(cases))

        if len(set(cases)) != len(cases):
            raise Exception(f'cases for variable {var} are not unique')

        self._label_case[var] = {case: k for k, case in enumerate(cases)}
        self._case_label[var] = {k: case for k, case in enumerate(cases)}
        DiscreteQuadraticModel.add_variable(self, len(cases), label=var)

    def set_linear_case(self, var, case, bias):
        k = self._label_case[var][case]
        DiscreteQuadraticModel.set_linear_case(self, var, k, bias)

    def set_quadratic_case(self, u, u_case, v, v_case, bias):
        k = self._label_case[u][u_case]
        m = self._label_case[v][v_case]
        DiscreteQuadraticModel.set_quadratic_case(self, u, k, v, m, bias)

    def map_sample(self, sample):
        return {var: self._case_label[var][value]
                for var, value in sample.items()}
