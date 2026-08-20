version 1.0

################################## LICENSE ##################################
# Copyright 2026 Aisling "Ash" O'Farrell
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#       http://www.apache.org/licenses/LICENSE-2.0
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

task stringcheck {
    input {
        String truth
        String test
    }

    command <<<
        set -euo pipefail

        # Strict string comparison in Bash
        if [ "~{truth}" = "~{test}" ]
        then
            echo "true" > result.txt
        else
            echo "false" > result.txt
            exit 1
        fi
    >>>

    output {
        Boolean is_equal = read_boolean("result.txt")
    }

    runtime {
        docker: "ubuntu:latest"
        cpu: 1
        memory: "1 GiB"
    }
}