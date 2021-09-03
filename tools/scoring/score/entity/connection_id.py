# Copyright 2021 Google LLC
#
# Licensed under the Apache License, Version 2.0 (the License);
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#    https://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an AS IS BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.


# Entity Connection Identification

# Connections are scored on targets (because this is where they are defined).

# Connections can be scored:

#  (correctly defined connections) - (incorrectly defined connections) total connections

# In addition to overall score, sub-scored should be available for connections where the source is another piece of equipment vs. a Facilities entity (building/floor).

from score.score import Score


class ConnectionId(Score):
    def __init__(self):
        return False
