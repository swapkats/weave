"""Environment variable substitution."""

import os
import re
from typing import List


def substitute_env_vars(text: str, strict: bool = True) -> str:
    """
    Replace ${VAR} patterns with environment variables.

    Args:
        text: Text containing ${VAR} patterns
        strict: If True, raise error on missing vars. If False, leave unchanged.

    Returns:
        Text with environment variables substituted

    Raises:
        ValueError: If strict=True and a referenced variable is not set
    """
    pattern = r"\$\{([^}]+)\}"
    missing_vars: List[str] = []

    def replacer(match: re.Match[str]) -> str:
        var_name = match.group(1)
        value = os.environ.get(var_name)

        if value is None:
            if strict:
                missing_vars.append(var_name)
                return match.group(0)  # Return original for better error message
            else:
                return match.group(0)  # Leave unchanged

        return value

    result = re.sub(pattern, replacer, text)

    if missing_vars and strict:
        vars_list = ", ".join(missing_vars)
        raise ValueError(
            f"Environment variables not set: {vars_list}\n"
            f"Please set these variables or remove them from your config."
        )

    return result
