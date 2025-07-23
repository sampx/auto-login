

import os
import sys
import uuid
import json
from pathlib import Path

# Ensure the scheduler_engine can be imported
sys.path.insert(0, str(Path(__file__).parent))

from scheduler_engine import Task, TaskExecutor

def test_load_env_file_and_filter_private_vars(tmp_path):
    """
    Tests that the TaskExecutor correctly:
    1. Loads environment variables from an _ENV_FILE specified in task_env.
    2. Gives task_env variables precedence over .env file variables.
    3. Filters out any environment variables starting with an underscore.
    """
    # 1. Create a temporary .env file
    env_file = tmp_path / ".test.env"
    env_file.write_text("FROM_FILE=file_value\nCOMMON_VAR=file_common")

    # 2. Create a temporary Python script for the task to execute
    output_file = tmp_path / "output.json"
    script_file = tmp_path / "task_script.py"
    script_content = f"""
import os
import json

# Capture all environment variables available to the script
env_vars = dict(os.environ)

# Write them to an output file for the test to inspect
with open(r'{str(output_file)}', 'w') as f:
    json.dump(env_vars, f)
"""
    script_file.write_text(script_content)

    # 3. Define the test task
    task = Task(
        task_id="test-env-task",
        task_name="Test Environment Loading",
        task_exec=f"python {script_file}",
        task_schedule="* * * * *",
        task_env={
            "_ENV_FILE": str(env_file),
            "FROM_TASK_ENV": "task_value",
            "COMMON_VAR": "task_common",
            "_PRIVATE_VAR": "should_be_filtered"
        }
    )

    # 4. Execute the task
    executor = TaskExecutor()
    execution_result = executor.execute_task(task)

    assert execution_result.status == "success"
    assert output_file.exists()

    # 5. Read the environment variables captured by the script
    with open(output_file, 'r') as f:
        captured_env = json.load(f)

    # 6. Assertions
    # Variable from .env file should exist
    assert "FROM_FILE" in captured_env
    assert captured_env["FROM_FILE"] == "file_value"

    # Variable from task_env should exist
    assert "FROM_TASK_ENV" in captured_env
    assert captured_env["FROM_TASK_ENV"] == "task_value"

    # task_env variable should override .env file variable
    assert "COMMON_VAR" in captured_env
    assert captured_env["COMMON_VAR"] == "task_common"

    # Variable starting with an underscore should NOT exist
    assert "_PRIVATE_VAR" not in captured_env
    
    # The _ENV_FILE variable itself should also be filtered
    assert "_ENV_FILE" not in captured_env

    # System environment variables should still be present (picking one as a sample)
    assert "PATH" in captured_env

