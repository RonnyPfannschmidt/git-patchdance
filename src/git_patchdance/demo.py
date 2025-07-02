"""Demo repository creation for Git Patchdance."""

from pathlib import PurePath

from .core.models import CommitRequest
from .git.fake_repository import FakeRepository


def create_demo_repository() -> FakeRepository:
    """Create a demo repository with commits containing line runs at positions.

    This function creates a series of commits that add line runs (multiple
    consecutive lines) at different positions in files. Each commit creates
    a new numbered file in a submodule to demonstrate patch manipulation.

    Returns:
        FakeRepository with demo commits showing various line run patterns
    """
    # Create empty fake repository
    repo = FakeRepository.create_test_repository(commit_count=0)

    # Initial commit: Basic structure
    request = CommitRequest(
        message="Initial commit: Create submodule structure",
        author="Demo User",
        email="demo@example.com",
        file_operations={
            PurePath(
                "submodule/__init__.py"
            ): '"""Demo submodule for patch manipulation."""\n',
            PurePath(
                "README.md"
            ): "# Demo Repository\n\nDemonstrates patch manipulation.\n",
        },
    )
    repo.create_commit(request)

    # Commit 1: Add file with imports at top (line run at beginning)
    file1_content = '''#!/usr/bin/env python3
"""Module 1: Demonstrates line runs at the beginning."""

import sys
import os
import logging
from pathlib import Path
from typing import Optional


def main():
    print("Hello from module 1!")


if __name__ == "__main__":
    main()
'''

    request = CommitRequest(
        message="Add module1.py with import line run at top",
        author="Demo User",
        email="demo@example.com",
        file_operations={PurePath("submodule/module1.py"): file1_content},
        parent_ids=(repo.head_commit,) if repo.head_commit else (),
    )
    repo.create_commit(request)

    # Commit 2: Add file with function block in middle (line run in middle)
    file2_content = '''#!/usr/bin/env python3
"""Module 2: Demonstrates line runs in the middle."""

import sys


def validate_input(data):
    """Validate input data with multiple checks."""
    if not data:
        return False
    if not isinstance(data, str):
        return False
    if len(data) < 3:
        return False
    return True


def main():
    print("Hello from module 2!")


if __name__ == "__main__":
    main()
'''

    request = CommitRequest(
        message="Add module2.py with validation function in middle",
        author="Demo User",
        email="demo@example.com",
        file_operations={PurePath("submodule/module2.py"): file2_content},
        parent_ids=(repo.head_commit,) if repo.head_commit else (),
    )
    repo.create_commit(request)

    # Commit 3: Add file with class definition (large line run)
    file3_content = '''#!/usr/bin/env python3
"""Module 3: Demonstrates large line runs with class definition."""

import sys


class DataProcessor:
    """Process data with various methods."""

    def __init__(self, config=None):
        self.config = config or {}
        self.processed_count = 0

    def process_item(self, item):
        """Process a single item."""
        if not self.validate_item(item):
            return None
        result = self._transform_item(item)
        self.processed_count += 1
        return result

    def validate_item(self, item):
        """Validate item before processing."""
        return item is not None

    def _transform_item(self, item):
        """Transform item internally."""
        return str(item).upper()


def main():
    processor = DataProcessor()
    print(f"Processor created: {processor}")


if __name__ == "__main__":
    main()
'''

    request = CommitRequest(
        message="Add module3.py with DataProcessor class",
        author="Demo User",
        email="demo@example.com",
        file_operations={PurePath("submodule/module3.py"): file3_content},
        parent_ids=(repo.head_commit,) if repo.head_commit else (),
    )
    repo.create_commit(request)

    # Commit 4: Add file with error handling at end (line run at end)
    file4_content = '''#!/usr/bin/env python3
"""Module 4: Demonstrates line runs at the end."""

import sys


def risky_operation():
    """Simulate a risky operation."""
    return 42 / 0


def main():
    print("Hello from module 4!")
    result = risky_operation()
    print(f"Result: {result}")


if __name__ == "__main__":
    try:
        main()
    except ZeroDivisionError:
        print("Error: Division by zero!")
        sys.exit(1)
    except KeyboardInterrupt:
        print("\\nInterrupted by user")
        sys.exit(130)
    except Exception as e:
        print(f"Unexpected error: {e}")
        sys.exit(1)
'''

    request = CommitRequest(
        message="Add module4.py with error handling at end",
        author="Demo User",
        email="demo@example.com",
        file_operations={PurePath("submodule/module4.py"): file4_content},
        parent_ids=(repo.head_commit,) if repo.head_commit else (),
    )
    repo.create_commit(request)

    # Commit 5: Add file with configuration block after imports
    file5_content = '''#!/usr/bin/env python3
"""Module 5: Demonstrates line runs with configuration."""

import sys
import os
from dataclasses import dataclass

# Configuration section
DEFAULT_TIMEOUT = 30
MAX_RETRIES = 3
BUFFER_SIZE = 1024
DEBUG_MODE = os.getenv("DEBUG", "false").lower() == "true"
LOG_LEVEL = "INFO" if not DEBUG_MODE else "DEBUG"


@dataclass
class Config:
    """Configuration data class."""
    timeout: int = DEFAULT_TIMEOUT
    retries: int = MAX_RETRIES
    buffer_size: int = BUFFER_SIZE
    debug: bool = DEBUG_MODE


def main():
    config = Config()
    print(f"Running with config: {config}")


if __name__ == "__main__":
    main()
'''

    request = CommitRequest(
        message="Add module5.py with configuration constants",
        author="Demo User",
        email="demo@example.com",
        file_operations={PurePath("submodule/module5.py"): file5_content},
        parent_ids=(repo.head_commit,) if repo.head_commit else (),
    )
    repo.create_commit(request)

    # Commit 6: Add file with mixed line runs at different positions
    file6_content = '''#!/usr/bin/env python3
"""Module 6: Demonstrates mixed line run patterns."""

# Multiple imports at top
import sys
import os
import json
import logging
from typing import Dict, List, Any

# Constants section
VERSION = "1.0.0"
AUTHOR = "Demo User"


def setup_logging():
    """Setup logging configuration."""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    return logging.getLogger(__name__)


def process_data(data: List[Dict[str, Any]]) -> List[str]:
    """Process a list of data items."""
    results = []
    for item in data:
        processed = transform_item(item)
        if processed:
            results.append(processed)
    return results


def transform_item(item: Dict[str, Any]) -> str:
    """Transform a single data item."""
    if not isinstance(item, dict):
        return ""
    return json.dumps(item, sort_keys=True)


def main():
    logger = setup_logging()
    sample_data = [{"id": 1, "name": "test"}]
    results = process_data(sample_data)
    logger.info(f"Processed {len(results)} items")


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print(f"Error in main: {e}")
        sys.exit(1)
'''

    request = CommitRequest(
        message="Add module6.py with mixed line run patterns",
        author="Demo User",
        email="demo@example.com",
        file_operations={PurePath("submodule/module6.py"): file6_content},
        parent_ids=(repo.head_commit,) if repo.head_commit else (),
    )
    repo.create_commit(request)

    return repo
