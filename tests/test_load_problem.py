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

import unittest

from io import StringIO
from textwrap import dedent

from crop_rotation import load_problem_file, InvalidProblem


class TestLoadProblemFile(unittest.TestCase):
    def test_empty_file(self):
        buf = StringIO()
        with self.assertRaises(InvalidProblem) as cm:
            load_problem_file(buf)
        self.assertIn('empty file', cm.exception.args[0])

    def test_missing_element(self):
        buf = StringIO(dedent('''
                              time_units: 1
                              '''))
        with self.assertRaises(InvalidProblem) as cm:
            load_problem_file(buf)
        self.assertIn('missing element', cm.exception.args[0])

    def test_invalid_time_units_1(self):
        buf = StringIO(dedent('''
                              time_units: xyz
                              plot_adjacency:
                                1: []
                              crops:
                                abc:
                                    family:
                                    planting: [1, 1]
                                    grow_time: 1
                              '''))
        with self.assertRaises(InvalidProblem) as cm:
            load_problem_file(buf)
        self.assertIn('time_units', cm.exception.args[0])

    def test_invalid_time_units_2(self):
        buf = StringIO(dedent('''
                              time_units: -1
                              plot_adjacency:
                                1: []
                              crops:
                                abc:
                                    family:
                                    planting: [1, 1]
                                    grow_time: 1
                              '''))
        with self.assertRaises(InvalidProblem) as cm:
            load_problem_file(buf)
        self.assertIn('time_units', cm.exception.args[0])

    def test_invalid_plot_adjacency_1(self):
        buf = StringIO(dedent('''
                              time_units: 2
                              plot_adjacency: abc
                              crops:
                                abc:
                                    family:
                                    planting: [1, 2]
                                    grow_time: 1
                              '''))
        with self.assertRaises(InvalidProblem) as cm:
            load_problem_file(buf)
        self.assertIn('plot_adjacency', cm.exception.args[0])

    def test_invalid_plot_adjacency_2(self):
        buf = StringIO(dedent('''
                              time_units: 2
                              plot_adjacency:
                                1: [xyz]
                              crops:
                                abc:
                                    family:
                                    planting: [1, 2]
                                    grow_time: 1
                              '''))
        with self.assertRaises(InvalidProblem) as cm:
            load_problem_file(buf)
        self.assertIn('xyz', cm.exception.args[0])

    def test_invalid_plot_adjacency_3(self):
        buf = StringIO(dedent('''
                              time_units: 2
                              plot_adjacency:
                                1: [1]
                              crops:
                                abc:
                                    family:
                                    planting: [1, 2]
                                    grow_time: 1
                              '''))
        with self.assertRaises(InvalidProblem) as cm:
            load_problem_file(buf)
        self.assertIn('itself', cm.exception.args[0])

    def test_invalid_crops(self):
        buf = StringIO(dedent('''
                              time_units: 1
                              plot_adjacency:
                                1: []
                              crops: 123
                              '''))
        with self.assertRaises(InvalidProblem) as cm:
            load_problem_file(buf)
        self.assertIn('crops', cm.exception.args[0])

    def test_invalid_crop_definition_1(self):
        buf = StringIO(dedent('''
                              time_units: 1
                              plot_adjacency:
                                1: []
                              crops:
                                abc:
                              '''))
        with self.assertRaises(InvalidProblem) as cm:
            load_problem_file(buf)
        self.assertIn('abc', cm.exception.args[0])

    def test_invalid_crop_definition_2(self):
        buf = StringIO(dedent('''
                              time_units: 2
                              plot_adjacency:
                                1: []
                              crops:
                                abc:
                                    xyz:
                              '''))
        with self.assertRaises(InvalidProblem) as cm:
            load_problem_file(buf)
        self.assertIn('missing field', cm.exception.args[0])

    def test_invalid_planting_1(self):
        buf = StringIO(dedent('''
                              time_units: 2
                              plot_adjacency:
                                1: []
                              crops:
                                abc:
                                    family:
                                    planting: []
                                    grow_time: 1
                              '''))
        with self.assertRaises(InvalidProblem) as cm:
            load_problem_file(buf)
        self.assertIn('planting', cm.exception.args[0])

    def test_invalid_planting_2(self):
        buf = StringIO(dedent('''
                              time_units: 2
                              plot_adjacency:
                                1: []
                              crops:
                                abc:
                                    family:
                                    planting: [1]
                                    grow_time: 1
                              '''))
        with self.assertRaises(InvalidProblem) as cm:
            load_problem_file(buf)
        self.assertIn('planting', cm.exception.args[0])

    def test_invalid_planting_3(self):
        buf = StringIO(dedent('''
                              time_units: 2
                              plot_adjacency:
                                1: []
                              crops:
                                abc:
                                    family:
                                    planting: [1, xxx]
                                    grow_time: 1
                              '''))
        with self.assertRaises(InvalidProblem) as cm:
            load_problem_file(buf)
        self.assertIn('planting', cm.exception.args[0])

    def test_invalid_planting_4(self):
        buf = StringIO(dedent('''
                              time_units: 2
                              plot_adjacency:
                                1: []
                              crops:
                                abc:
                                    family:
                                    planting: [1, 3]
                                    grow_time: 1
                              '''))
        with self.assertRaises(InvalidProblem) as cm:
            load_problem_file(buf)
        self.assertIn('planting', cm.exception.args[0])

    def test_invalid_grow_time_1(self):
        buf = StringIO(dedent('''
                              time_units: 2
                              plot_adjacency:
                                1: []
                              crops:
                                abc:
                                    family:
                                    planting: [1, 2]
                                    grow_time: xxx
                              '''))
        with self.assertRaises(InvalidProblem) as cm:
            load_problem_file(buf)
        self.assertIn('grow_time', cm.exception.args[0])

    def test_invalid_grow_time_2(self):
        buf = StringIO(dedent('''
                              time_units: 2
                              plot_adjacency:
                                1: []
                              crops:
                                abc:
                                    family:
                                    planting: [1, 2]
                                    grow_time: 0
                              '''))
        with self.assertRaises(InvalidProblem) as cm:
            load_problem_file(buf)
        self.assertIn('grow_time', cm.exception.args[0])
