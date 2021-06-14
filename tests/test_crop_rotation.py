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
import re
import subprocess
import sys
import unittest

from crop_rotation import CropRotation


def get_illustration_path(output):
    for line in output.splitlines():
        match = re.match('Saved illustration of solution to (.*)', line)
        if match:
            return match.groups()[0]


class TestCropRotation(unittest.TestCase):
    def test_build_dqm(self):
        crop1 = {'family': 'y',
                 'planting': [1, 2],
                 'grow_time': 1}
        rotation = CropRotation(2, {1: []}, {'x': crop1}, False)
        rotation.build_dqm()
        self.assertEqual(rotation.dqm.num_variables(), 2)
        self.assertEqual(rotation.dqm.num_cases(), 4)

    @unittest.skipIf(os.getenv('SKIP_INT_TESTS'), "Skipping integration test.")
    def test_crop_rotation(self):
        args = [sys.executable, 'crop_rotation.py', '--output-tempfile']
        output = subprocess.check_output(args).decode('utf8')
        self.assertIn('Solution:', output)
        self.assertIn('Solution energy:', output)
        self.assertNotIn('invalid', output)
        path = get_illustration_path(output)
        self.assertIsNotNone(path)
        self.assertGreater(os.stat(path).st_size, 0)
        os.remove(path)
