"""
Health Check Script for Database Adapters
Tests connectivity to ThemisDB and UDS3 Polyglot
"""
import asyncio
import sys
import logging
from typing import Dict, Any

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


async def check_themisdb() -> Dict[str, Any]:
    """
    Check ThemisDB adapter availability and health
    
    Returns:
        Status dict with availability and health info
    """
    try:
        from backend.adapters import is_themisdb_available
        from backend.adapters.themisdb_adapter import ThemisDBAdapter, ThemisDBConfig
        
        logger.info("🔍 Checking ThemisDB adapter...")
        
        # Check basic availability
        available = is_themisdb_available()
        
        if available:
            # Get detailed health info
            config = ThemisDBConfig.from_env()
            adapter = ThemisDBAdapter(config)
            
            try:
                health = await adapter.health_check()
                stats = adapter.get_stats()
                
                await adapter.close()
                
                return {
                    'available': True,
                    'status': 'healthy',
                    'health_info': health,
                    'config': {
                        'host': config.host,
                        'port': config.port,
                        'ssl': config.use_ssl
                    },
                    'stats': stats
                }
            except Exception as e:
                await adapter.close()
                return {
                    'available': False,
                    'status': 'unhealthy',
                    'error': str(e)
                }
        else:
            return {
                'available': False,
                'status': 'unavailable',
                'error': 'ThemisDB adapter initialization failed'
            }
            
    except Exception as e:
        logger.error(f"❌ ThemisDB check failed: {e}")
        return {
            'available': False,
            'status': 'error',
            'error': str(e)
        }


def check_uds3() -> Dict[str, Any]:
    """
    Check UDS3 adapter availability
    
    Returns:
        Status dict with availability info
    """
    try:
        from backend.adapters import is_uds3_available
        
        logger.info("🔍 Checking UDS3 Polyglot adapter...")
        
        available = is_uds3_available()
        
        if available:
            return {
                'available': True,
                'status': 'healthy'
            }
        else:
            return {
                'available': False,
                'status': 'unavailable',
                'error': 'UDS3 adapter initialization failed'
            }
            
    except Exception as e:
        logger.error(f"❌ UDS3 check failed: {e}")
        return {
            'available': False,
            'status': 'error',
            'error': str(e)
        }


async def check_adapter_selection() -> Dict[str, Any]:
    """
    Check which adapter gets selected by factory
    
    Returns:
        Selected adapter info
    """
    try:
        from backend.adapters import get_database_adapter, get_adapter_type
        
        logger.info("🔍 Checking adapter selection...")
        
        adapter_type = get_adapter_type()
        adapter = get_database_adapter(enable_fallback=True)
        
        adapter_name = adapter.__class__.__name__
        
        return {
            'selected': True,
            'adapter_type': str(adapter_type),
            'adapter_class': adapter_name
        }
        
    except Exception as e:
        logger.error(f"❌ Adapter selection failed: {e}")
        return {
            'selected': False,
            'error': str(e)
        }


def print_status(name: str, status: Dict[str, Any]):
    """Pretty-print adapter status"""
    print(f"\n{'='*60}")
    print(f"  {name}")
    print(f"{'='*60}")
    
    if status.get('available') or status.get('selected'):
        print(f"✅ Status: {status.get('status', 'healthy')}")
        
        if 'config' in status:
            print(f"\n📡 Configuration:")
            for key, value in status['config'].items():
                print(f"  - {key}: {value}")
        
        if 'health_info' in status:
            print(f"\n💚 Health Info:")
            for key, value in status['health_info'].items():
                print(f"  - {key}: {value}")
        
        if 'stats' in status:
            print(f"\n📊 Statistics:")
            stats = status['stats']
            print(f"  - Total Queries: {stats.get('total_queries', 0)}")
            print(f"  - Success Rate: {stats.get('success_rate', 0):.2%}")
            print(f"  - Avg Latency: {stats.get('avg_latency_ms', 0):.1f}ms")
        
        if 'adapter_type' in status:
            print(f"\n🎯 Adapter Type: {status['adapter_type']}")
            print(f"   Class: {status.get('adapter_class', 'N/A')}")
    else:
        print(f"❌ Status: {status.get('status', 'error')}")
        print(f"   Error: {status.get('error', 'Unknown error')}")


async def main():
    """Main health check routine"""
    print("\n" + "="*60)
    print("  VCC-Veritas Database Adapter Health Check")
    print("="*60)
    
    # Check ThemisDB
    themis_status = await check_themisdb()
    print_status("ThemisDB Adapter", themis_status)
    
    # Check UDS3
    uds3_status = check_uds3()
    print_status("UDS3 Polyglot Adapter", uds3_status)
    
    # Check adapter selection
    selection_status = await check_adapter_selection()
    print_status("Adapter Selection", selection_status)
    
    # Summary
    print(f"\n{'='*60}")
    print("  Summary")
    print(f"{'='*60}")
    
    themis_ok = themis_status.get('available', False)
    uds3_ok = uds3_status.get('available', False)
    selection_ok = selection_status.get('selected', False)
    
    print(f"ThemisDB:   {'✅' if themis_ok else '❌'}")
    print(f"UDS3:       {'✅' if uds3_ok else '❌'}")
    print(f"Selection:  {'✅' if selection_ok else '❌'}")
    
    if themis_ok or uds3_ok:
        print("\n✅ At least one adapter is available - System operational")
        return 0
    else:
        print("\n❌ No adapters available - System will fail to start")
        return 1


if __name__ == '__main__':
    try:
        exit_code = asyncio.run(main())
        sys.exit(exit_code)
    except KeyboardInterrupt:
        print("\n⚠️ Health check interrupted")
        sys.exit(130)
    except Exception as e:
        logger.error(f"❌ Health check failed: {e}")
        sys.exit(1)
