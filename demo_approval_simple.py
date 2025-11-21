"""
Simple demonstration of Approval Agent core functionality
Shows the key features implemented in task 6 without importing the full system
"""

import asyncio
import sys
import os
from datetime import datetime, timedelta
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any
from enum import Enum
import uuid
import json
import base64
import hmac
import hashlib

# Simple implementations to demonstrate functionality

class DecisionStatus(Enum):
    """Status of decision proposals"""
    DRAFT = "draft