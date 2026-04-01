"""LingFlow Configuration Module

.. deprecated::
    Use ``lingflow.common.config.ConfigManager`` instead.
    This module is retained for backward compatibility only.
"""

import warnings
from dataclasses import asdict, dataclass
from typing import Any, Dict


@dataclass
class LingFlowConfig:
    """LingFlow configuration class (type-safe).

    .. deprecated::
        Use ``lingflow.common.config.ConfigManager`` for new code.
        This dataclass is retained for backward compatibility only.

    Provides type-safe configuration with validation and backward compatibility.
    File I/O is handled at application layer to avoid extra dependencies.

    Attributes:
        max_parallel: Maximum parallel tasks
        max_iterations: Maximum workflow iterations
        workflow_timeout: Workflow timeout in seconds
        skills_path: Path to skills directory
        skill_timeout: Individual skill timeout in seconds
        skill_cache_enabled: Enable skill caching
        agent_timeout: Agent timeout in seconds
        agent_context_limit: Agent context token limit
        compression_enabled: Enable context compression
        compression_target_tokens: Target token count for compression
        log_level: Logging level
    """

    # Coordinator configuration
    max_parallel: int = 2
    max_iterations: int = 100
    workflow_timeout: float = 600.0

    # Skill configuration
    skills_path: str = "skills"
    skill_timeout: float = 30.0
    skill_cache_enabled: bool = False

    # Agent configuration
    agent_timeout: float = 300.0
    agent_context_limit: int = 8000

    # Compression configuration
    compression_enabled: bool = True
    compression_target_tokens: int = 4000

    # Logging configuration
    log_level: str = "INFO"

    def __post_init__(self) -> None:
        warnings.warn(
            "LingFlowConfig is deprecated. Use lingflow.common.config.ConfigManager instead.",
            DeprecationWarning,
            stacklevel=2,
        )

    def validate(self) -> None:
        """Validate configuration values.

        Raises:
            ValueError: If any configuration value is invalid
        """
        if self.max_parallel < 1:
            raise ValueError("max_parallel must be >= 1")
        if self.max_iterations < 1:
            raise ValueError("max_iterations must be >= 1")
        if self.workflow_timeout < 0:
            raise ValueError("workflow_timeout must be >= 0")
        if self.skill_timeout < 0:
            raise ValueError("skill_timeout must be >= 0")
        if self.agent_timeout < 0:
            raise ValueError("agent_timeout must be >= 0")
        if self.agent_context_limit < 1000:
            raise ValueError("agent_context_limit must be >= 1000")
        if self.compression_target_tokens < 1000:
            raise ValueError("compression_target_tokens must be >= 1000")
        if self.log_level not in ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]:
            raise ValueError(
                f"log_level must be one of DEBUG, INFO, WARNING, ERROR, CRITICAL, got {self.log_level}"
            )

    @classmethod
    def from_dict(cls, config: Dict[str, Any]) -> "LingFlowConfig":
        """Create configuration from dictionary (backward compatibility).

        Filters out unknown keys to maintain compatibility with old configs.

        Args:
            config: Configuration dictionary

        Returns:
            LingFlowConfig instance

        Example:
            >>> config_dict = {"max_parallel": 4, "skill_timeout": 60.0}
            >>> config = LingFlowConfig.from_dict(config_dict)
        """
        # Filter unknown keys
        valid_keys = set(cls.__dataclass_fields__.keys())
        filtered_config = {k: v for k, v in config.items() if k in valid_keys}

        # Create configuration object
        return cls(**filtered_config)

    def to_dict(self) -> Dict[str, Any]:
        """Convert configuration to dictionary (backward compatibility).

        Returns:
            Dictionary representation of configuration

        Example:
            >>> config = LingFlowConfig(max_parallel=4)
            >>> config_dict = config.to_dict()
            >>> config_dict["max_parallel"]
            4
        """
        return asdict(self)
