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

import random
import string

import click
import yaml

from validate import validate_problem

def index(row, col, nrows):
    return row + col * nrows + 1


def random_letter():
    return random.choice(string.ascii_lowercase)


def make_name(length=None):
    length = length or random.choice(range(5, 10))
    return ''.join([random_letter().upper()]
                   + [random_letter() for _ in range(length)])


def make_crop(family, time_units):
    planting_start = random.choice(range(1, int(time_units * 3 / 4)))
    planting_end = random.choice(range(planting_start + 1, time_units + 1))
    return {'family': family,
            'planting': [planting_start, planting_end],
            'grow_time': random.choice(range(1, int(time_units * 3 / 4)))}


@click.command(help='Generate random Crop Rotation problem')
@click.argument('nrows', type=int)
@click.argument('ncols', type=int)
@click.option('-M', '--time-units', default=12, show_default=True)
@click.option('-N', '--num-crops', default=10, show_default=True)
@click.option('-N_f', '--num-crop-families', default=5, show_default=True)
def main(nrows, ncols, time_units, num_crops, num_crop_families):
    families = [make_name() for p in range(num_crop_families)]

    crops = {make_name(): make_crop(random.choice(families), time_units)
             for _ in range(num_crops)}

    adjacency = {1 + x: [] for x in range(nrows * ncols)}

    for row in range(nrows):
        for col in range(ncols):
            plot = index(row, col, nrows)
            if row:
                adjacency[plot] += [index(row - 1, col, nrows)]
            if col:
                adjacency[plot] += [index(row, col - 1, nrows)]
            if row < nrows - 1:
                adjacency[plot] += [index(row + 1, col, nrows)]
            if col < ncols - 1:
                adjacency[plot] += [index(row, col + 1, nrows)]

    data = {'time_units': time_units,
            'plot_adjacency': adjacency,
            'crops': crops}
    validate_problem(data, '<generated>')
    print(yaml.safe_dump(data))


if __name__ == '__main__':
    main()
