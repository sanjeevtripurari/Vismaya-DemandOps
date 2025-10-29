"""
Unit tests for Cost Management Agent
Tests cost analysis, budget monitoring, and optimization recommendations
"""

import pytest
import asyncio
from datetime import datetime, timedelta
from unittest.mock import Mock, AsyncMock, patch
from decimal import Decimal

from