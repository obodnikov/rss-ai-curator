"""Disable ChromaDB telemetry completely."""
import os
import sys
import logging

# Set environment variable
os.environ['ANONYMIZED_TELEMETRY'] = 'False'

# Monkey-patch chromadb telemetry before it loads
def _disable_telemetry():
    """Completely disable ChromaDB telemetry."""
    try:
        import chromadb.telemetry.product.posthog as posthog
        
        # Replace the problematic capture method
        class DummyPostHog:
            def capture(self, *args, **kwargs):
                pass
        
        posthog.Posthog = DummyPostHog
        
    except Exception:
        pass

_disable_telemetry()

# Suppress all telemetry loggers
logging.getLogger('chromadb.telemetry').setLevel(logging.CRITICAL)
logging.getLogger('chromadb.telemetry.product').setLevel(logging.CRITICAL)
logging.getLogger('chromadb.telemetry.product.posthog').setLevel(logging.CRITICAL)
