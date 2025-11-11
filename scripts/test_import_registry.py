import traceback
import sys
import os

# Mirror start_backend.py sys.path adjustments
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)
sys.path.insert(0, os.path.join(project_root, 'frontend'))
sys.path.insert(0, os.path.join(project_root, 'backend'))
sys.path.insert(0, os.path.join(project_root, 'shared'))
sys.path.insert(0, os.path.join(project_root, 'database'))
sys.path.insert(0, os.path.join(project_root, 'uds3'))

try:
    import backend.agents.veritas_api_agent_registry as reg
    print('IMPORT_OK')
    print('AgentCapability present:', hasattr(reg, 'AgentCapability'))
except Exception:
    traceback.print_exc()
    print('IMPORT_FAILED')
