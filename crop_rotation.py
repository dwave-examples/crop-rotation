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

from collections import defaultdict
from itertools import combinations
from os.path import dirname, join
import random
import sys
import tempfile

import click
from dwave.system import LeapHybridDQMSampler
import matplotlib.pyplot as plt
from matplotlib.colors import hsv_to_rgb
from matplotlib.ticker import MultipleLocator
import yaml

from caselabeldqm import CaseLabelDQM
from validate import validate_problem, InvalidProblem

DEFAULT_PATH = join(dirname(__file__), 'data', 'problem1.yaml')


def load_problem_file(path):
    """Load a problem file.

    Args:
        path (string): Path to input file.

    Returns:
        Tuple of time_units (int), plot_adjacency (dict), and crops (dict).
    """
    try:
        data = list(yaml.safe_load_all(path))[0]
    except IndexError:
        raise InvalidProblem('empty file')

    validate_problem(data, path)

    time_units = data['time_units']
    plot_adjacency = data['plot_adjacency']
    crops = data['crops']
    return time_units, plot_adjacency, crops


def crop_colors(crop_families):
    """Generate colors for crops to be used in visualization of solution.

    All crops should have a unique color and crops in the same family should
    have similar colors.

    Args:
        crop_families (dict):
            Dictionary of crop family names mapped to crops.

    Returns:
        Dictionary of crop names mapped to colors.
    """
    h_scale = 2 / (3 * len(crop_families))
    colors = {}

    for k, crops in enumerate(crop_families.values()):
        h_fam = k / len(crop_families)

        for crop in crops:
            h = h_fam + (random.random() - 0.5) * h_scale
            colors[crop] = (min(1, max(0, h)),
                            0.7 + (random.random() - 0.5) * 0.3,
                            0.7 + (random.random() - 0.5) * 0.3)

    return {crop: hsv_to_rgb(color) for crop, color in colors.items()}


class CropRotation:
    """Solve a crop rotation problem.
    """
    def __init__(self, time_units, plot_adjacency, crops, verbose):
        self.time_units = time_units
        self.plot_adjacency = plot_adjacency
        self.crops = crops
        self.verbose = verbose
        self.dqm = None
        self.grow_time = {crop: dict_['grow_time']
                          for crop, dict_ in crops.items()}
        self.gamma = 1 + max(self.grow_time.values())
        self.period_crops = {1 + period: [] for period in range(self.time_units)}
        self.crop_families = defaultdict(list)

        for crop, dict_ in self.crops.items():
            for period in range(dict_['planting'][0], dict_['planting'][1] + 1):
                self.period_crops[period].append(crop)
            self.crop_families[dict_['family']].append(crop)

        self._crop_r = []
        for crop in self.crops.keys():
            range_ = range(self.grow_time[crop])
            self._crop_r.extend([(crop, r) for r in range_])

        self._neighbor_pairs = []
        for plot, neighbors in plot_adjacency.items():
            self._neighbor_pairs.extend([(plot, v) for v in neighbors])

        self.crop_colors = crop_colors(self.crop_families)

    def rollover_period(self, period):
        """Ensure that `period` is between 1 and `self.time_units` by adding or
        subtracting multiples of `self.time_units`.
        """
        while period > self.time_units:
            period -= self.time_units
        while period < 1:
            period += self.time_units
        return period

    def crop_r_combinations(self, plot, period, crop_r):
        """Generate combinations of variables and cases from an input sequence.

        Args:
            plot: The plot to generate combinations for.

            period: The period to generate combinations for.

            crop_r: Sequence of crops paired with r-values.  R-values are
                integers used to identify earlier or later growing periods on
                a plot relative to `period`.

        Returns:
            Generator yielding four-tuples: var1, crop1, var2, crop2.
        """
        for (crop1, r1), (crop2, r2) in combinations(crop_r, 2):
            if r1 == r2:
                # DQM enforces one-hot constraint for all variables so we can
                # ignore this case.
                continue

            r1_period = self.rollover_period(period - r1)
            if crop1 not in self.period_crops[r1_period]:
                continue

            r2_period = self.rollover_period(period - r2)
            if crop2 not in self.period_crops[r2_period]:
                continue

            var1 = f'{plot},{r1_period}'
            var2 = f'{plot},{r2_period}'
            yield var1, crop1, var2, crop2

    def plot_crop_r_combinations(self, period, plot_crop_r):
        """Generate combinations of variables and cases from an input sequence.

        Args:
            period: The period to generate combinations for.

            plot_crop_r: Sequence of (plot, crop, r-value) triples.  R-values
                are integers used to identify earlier or later growing periods
                on a plot relative to `period`.

        Returns:
            Generator yielding four-tuples: var1, crop1, var2, crop2.
        """
        for (u, crop1, r1), (v, crop2, r2) in combinations(plot_crop_r, 2):
            if (u, r1) == (v, r2):
                # DQM enforces one-hot constraint for all variables so we can
                # ignore this case.
                continue

            r1_period = self.rollover_period(period - r1)
            if crop1 not in self.period_crops[r1_period]:
                continue

            r2_period = self.rollover_period(period - r2)
            if crop2 not in self.period_crops[r2_period]:
                continue

            var1 = f'{u},{r1_period}'
            var2 = f'{v},{r2_period}'
            yield var1, crop1, var2, crop2

    def build_dqm(self):
        """Build a discrete quadratic model that encodes the problem.
        """
        self.dqm = dqm = CaseLabelDQM()

        # add variables and set linear biases.
        for period in range(1, self.time_units + 1):
            for plot in self.plot_adjacency:
                var = f'{plot},{period}'

                dqm.add_variable(
                    [None] + self.period_crops[period], label=var)

                for crop in self.period_crops[period]:
                    dqm.set_linear_case(var, crop, -self.grow_time[crop])

        # set quadratic biases for first constraint set.
        for period in range(1, self.time_units + 1):
            for plot in self.plot_adjacency:
                for args in self.crop_r_combinations(plot, period, self._crop_r):
                    dqm.set_quadratic_case(*args, self.gamma)

        # set quadratic biases for second constraint set.
        for period in range(1, self.time_units + 1):
            for plot in self.plot_adjacency:
                for F_p in self.crop_families.values():
                    crop_r = []
                    for crop in F_p:
                        range_ = range(self.grow_time[crop] + 1)
                        crop_r.extend([(crop, r) for r in range_])

                    for args in self.crop_r_combinations(plot, period, crop_r):
                        dqm.set_quadratic_case(*args, self.gamma)

        # set quadratic biases for third constraint set.
        for period in range(1, self.time_units + 1):
            for u, v in self._neighbor_pairs:
                for F_p in self.crop_families.values():
                    plot_crop_r = []
                    for crop in F_p:
                        range_ = range(self.grow_time[crop])
                        plot_crop_r.extend([(u, crop, r) for r in range_])
                        plot_crop_r.extend([(v, crop, r) for r in range_])

                    for args in self.plot_crop_r_combinations(period, plot_crop_r):
                        dqm.set_quadratic_case(*args, self.gamma)


        if self.verbose:
            n_v = dqm.num_variables()
            n_v_i = dqm.num_variable_interactions()
            max_n_v_i = n_v * (n_v - 1) // 2

            n_c = dqm.num_cases()
            n_c_i = dqm.num_case_interactions()
            n_plots = len(self.plot_adjacency)

            # this is the number of case interactions that are disallowed by
            # DQM (cases of a variable interacting with itself).
            illegal_c_i = sum((1 + len(x)) * len(x) // 2
                              for x in self.period_crops.values()) * n_plots

            max_n_c_i = (n_c * (n_c - 1) // 2) - illegal_c_i

            print(f'DQM num. variables: {n_v}')
            print(f'DQM num. variable interactions: {n_v_i} '
                  f'({n_v_i * 100 / max_n_v_i:.1f} % of max)')
            print(f'DQM num. cases: {n_c}')
            print(f'DQM num. case interactions: {n_c_i} '
                  f'({n_c_i * 100 / max_n_c_i:.1f} % of max)')

    def solve(self):
        """Solve the problem using LeapHybridDQMSampler.
        """
        sampler = LeapHybridDQMSampler()
        self.sampleset = sampler.sample_dqm(self.dqm,
            label='Example - Crop Rotation')

    def validate(self, sample):
        """Check that the constraints of the problem are satisfied.
        """
        errors = []

        # check first constraint set.
        for period in range(1, self.time_units + 1):
            for plot in self.plot_adjacency:
                var = f'{plot},{period}'
                crop = sample[var]

                if crop:
                    for r in range(1, self.grow_time[crop]):
                        r_period = self.rollover_period(period + r)
                        r_var = f'{plot},{r_period}'
                        r_crop = sample[r_var]

                        if r_crop:
                            errors += [f'Constraint 1 violated: {var} {crop} '
                                       f'{r_var} {r_crop} {self.grow_time[crop]}']

        # check second constraint set.
        for period in range(1, self.time_units + 1):
            for plot in self.plot_adjacency:
                var = f'{plot},{period}'
                crop = sample[var]

                if crop:
                    family = self.crops[crop]['family']
                    related_crops = set(self.crop_families[family]) - {crop}

                    for r in range(1, self.grow_time[crop] + 1):
                        r_period = self.rollover_period(period + r)
                        r_var = f'{plot},{r_period}'
                        r_crop = sample[r_var]

                        if r_crop in related_crops:
                            errors += [f'Constraint 2 violated: {var} {crop} '
                                       f'{r_var} {r_crop}']

        # check third constraint set.
        for period in range(1, self.time_units + 1):
            for plot, neighbors in self.plot_adjacency.items():
                var = f'{plot},{period}'
                crop = sample[var]

                if crop:
                    family = self.crops[crop]['family']
                    related_crops = set(self.crop_families[family])

                    for r in range(0, self.grow_time[crop]):
                        r_period = self.rollover_period(period + r)

                        for neighbor in neighbors:
                            var2 = f'{neighbor},{r_period}'
                            crop2 = sample[var2]

                            if crop2 in related_crops:
                                errors += [f'Constraint 3 violated: {var} {crop} '
                                           f'{var2} {crop2}']

        return errors

    @property
    def solution(self):
        return self.dqm.map_sample(self.sampleset.first.sample)

    def render_solution(self, path):
        """Generate a visual representation of the solution.
        """
        sample = self.solution
        labels = set()  # keep track of labels so legend won't have duplicates.
        width = 1
        max_x = self.time_units
        fig, ax = plt.subplots()

        for k, plot in enumerate(self.plot_adjacency):
            for period in range(1, self.time_units + 1):
                crop = sample[f'{plot},{period}']

                if crop:
                    xs = list(range(period, period + self.grow_time[crop]))
                    max_x = max(max_x, max(xs))
                    ys = [1] * len(xs)
                    color = self.crop_colors[crop]
                    bottom = [k] * len(xs)
                    label = crop if crop not in labels else None
                    labels.add(crop)
                    ax.bar(xs, ys, width, bottom=bottom, color=color,
                           label=label, align='edge')

        # indicate wrap-around periods by repeating the 1..time_units labels.
        period_labels = [1 + (x % self.time_units) for x in range(max_x + 1)]

        plt.title('Crop Rotation Demo')
        ax.set_xlabel('Period')
        ax.set_ylabel('Plot')
        ax.set_xticks(list(range(1, max_x + 2)))
        ax.set_xticklabels(period_labels)
        ax.set_yticks(list(range(1, len(self.plot_adjacency) + 1)))
        ax.set_yticklabels(list(self.plot_adjacency.keys()))

        period_divisor = max_x // 4
        if period_divisor:
            # hide a fraction of period labels or they will be hard to read.
            ax.xaxis.set_major_locator(MultipleLocator(period_divisor))
            ax.xaxis.set_minor_locator(MultipleLocator(1))

        # place legend to right of chart.
        box = ax.get_position()
        ax.set_position([box.x0, box.y0, box.width * 0.7, box.height])
        ax.legend(loc='upper center', bbox_to_anchor=(1.3, 1), shadow=True)

        # show grid lines.
        if period_divisor:
            plt.grid(axis='x', which='both')
        else:
            plt.grid(axis='x')
        plt.grid(axis='y')

        fig.savefig(path)
        print(f'Saved illustration of solution to {path}')

    @property
    def utilization(self):
        """Return the fraction of the maximum possible plot utilization for the
        found solution.
        """
        utilization = 0
        for k, plot in enumerate(self.plot_adjacency):
            for period in range(1, self.time_units + 1):
                crop = self.solution[f'{plot},{period}']
                if crop:
                    utilization += self.grow_time[crop]
        return utilization / (len(self.plot_adjacency) * self.time_units)

    def evaluate(self):
        """Evaluate the solution.
        """
        if self.verbose:
            print(self.sampleset)

        sample = self.solution
        print(f'Solution: {dict(((k, v) for k, v in sample.items() if v))}')
        print(f'Solution energy: {self.sampleset.first.energy}')
        print(f'Plot utilization: {100 * self.utilization:.1f} %')

        for error in self.validate(sample):
            print(f'Solution is invalid: {error}')


@click.command(help='Solve an instance of the Crop Rotation problem using '
                    'LeapHybridDQMSampler.')
@click.option('--path', type=click.File(), default=DEFAULT_PATH,
              help=f'Path to problem file.  Default is {DEFAULT_PATH!r}')
@click.option('--output-tempfile', is_flag=True,
              help='Output solution illustration to a unique, named temporary '
                   'file.')
@click.option('--verbose', is_flag=True)
def main(path, output_tempfile, verbose):
    try:
        rotation = CropRotation(*load_problem_file(path), verbose)
    except InvalidProblem as e:
        sys.exit(f'E: {e.args[0]}')

    rotation.build_dqm()
    rotation.solve()
    rotation.evaluate()

    if output_tempfile:
        with tempfile.NamedTemporaryFile(delete=False, suffix='.png') as f:
            output_path = f.name
    else:
        output_path = 'output.png'

    rotation.render_solution(output_path)


if __name__ == '__main__':
    main()
