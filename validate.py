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


class InvalidProblem(Exception):
    pass


def validate_plots(plot_adjacency):
    if not isinstance(plot_adjacency, dict):
        raise InvalidProblem('plot_adjacency must be a dict mapping plots to '
                             'lists of their neighbors')

    plots = frozenset(plot_adjacency.keys())
    for plot, neighbors in plot_adjacency.items():
        for v in neighbors:
            if v not in plots:
                raise InvalidProblem(f'"{v}" is not a plot (referenced in '
                                     f'adjacency list of plot {plot})')
            if v == plot:
                raise InvalidProblem(f'plot {v} cannot be adjacent to itself.')


def validate_crops(crops, time_units):
    if not isinstance(crops, dict):
        raise InvalidProblem('crops must be a dict mapping crops to crop '
                             'definitions')

    for crop, dict_ in crops.items():
        if not isinstance(dict_, dict):
            raise InvalidProblem(f'crop {crop} definition must be a dict')

        for name in ('family', 'planting', 'grow_time'):
            if name not in dict_:
                raise InvalidProblem(f'crop {crop} definition is missing '
                                     f'field "{name}"')

        family = dict_['family']
        planting = dict_['planting']
        grow_time = dict_['grow_time']

        if (not isinstance(planting, list)) or len(planting) != 2:
            raise InvalidProblem(f'"planting" field of crop {crop} must be a '
                                 'two-element list.')

        for value, label in ((planting[0], 'first element of "planting"'),
                             (planting[1], 'second element of "planting"')):

            if not isinstance(value, int):
                raise InvalidProblem(f'{label} field of crop {crop} must be '
                                     'an integer')

            if not (1 <= value <= time_units):
                raise InvalidProblem(f'{label} field of crop {crop} must be '
                                     f'in the range [1 .. {time_units}].')

        if planting[0] > planting[1]:
            print(f'W: "planting" field of crop {crop} defines an empty range')

        if (not isinstance(grow_time, int)) or grow_time < 1:
            raise InvalidProblem(f'grow_time must be a positive integer')


def validate_problem(data, path):
    for name in ('time_units', 'plot_adjacency', 'crops'):
        if name not in data:
            raise InvalidProblem(f'missing element "{name}" in problem file '
                                 f'{path}')

    time_units = data['time_units']
    plot_adjacency = data['plot_adjacency']
    crops = data['crops']

    if (not isinstance(time_units, int)) or time_units < 1:
        raise InvalidProblem(f'time_units must be a positive integer')

    validate_plots(plot_adjacency)
    validate_crops(crops, time_units)
