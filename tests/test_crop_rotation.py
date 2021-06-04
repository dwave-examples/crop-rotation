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

import os
import unittest

from crop_rotation import CropRotation


class TestCropRotation(unittest.TestCase):
    @unittest.skipIf(os.getenv('SKIP_INT_TESTS'), "Skipping integration test.")
    def test_crop_rotation(self):
        crop1 = {'family': 'y',
                 'planting': [1, 2],
                 'grow_time': 1}
        rotation = CropRotation(2, {1: []}, {'x': crop1}, False)
        rotation.build_dqm()
        rotation.solve()

        num_solutions = len(rotation.sampleset)
        self.assertGreater(num_solutions, 0)

        num_errors = len(rotation.validate(rotation.solution))
        self.assertEqual(num_errors, 0)
