#!/usr/bin/env python3
"""
Worker Instantiation Test
==========================
Quick test to verify if workers can be instantiated.

This test checks:
1. Can we import the worker classes?
2. What dependencies do they need?
3. Can we create instances without DB?
4. What's their interface?
"""

import sys
import os
import logging

# Add project root to path
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(current_dir)
if project_root not in sys.path:
    sys.path.insert(0, project_root)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def test_construction_workers():
    """Test Construction Workers"""
    print("\n" + "="*80)
    print("CONSTRUCTION WORKERS")
    print("="*80)
    
    try:
        from backend.agents.veritas_api_agent_construction import (
            BuildingPermitWorker,
            UrbanPlanningWorker,
            HeritageProtectionWorker
        )
        print("✅ Import successful")
        
        # Try to instantiate
        try:
            worker = BuildingPermitWorker(db_pool=None)
            print(f"✅ BuildingPermitWorker instantiated: {type(worker)}")
            print(f"   Methods: {[m for m in dir(worker) if not m.startswith('_')][:5]}...")
        except TypeError as e:
            print(f"⚠️ BuildingPermitWorker needs DB: {e}")
        except Exception as e:
            print(f"❌ BuildingPermitWorker error: {e}")
        
        try:
            worker = UrbanPlanningWorker(db_pool=None)
            print(f"✅ UrbanPlanningWorker instantiated")
        except Exception as e:
            print(f"⚠️ UrbanPlanningWorker: {e}")
        
        try:
            worker = HeritageProtectionWorker(db_pool=None)
            print(f"✅ HeritageProtectionWorker instantiated")
        except Exception as e:
            print(f"⚠️ HeritageProtectionWorker: {e}")
            
    except ImportError as e:
        print(f"❌ Import failed: {e}")

def test_environmental_worker():
    """Test Environmental Worker"""
    print("\n" + "="*80)
    print("ENVIRONMENTAL WORKER")
    print("="*80)
    
    try:
        from backend.agents.veritas_api_agent_environmental import (
            EnvironmentalAgent,
            EnvironmentalAgentConfig
        )
        print("✅ Import successful")
        
        try:
            config = EnvironmentalAgentConfig()
            worker = EnvironmentalAgent(config=config)
            print(f"✅ EnvironmentalAgent instantiated")
            print(f"   Config: timeout={config.timeout_seconds}s")
        except Exception as e:
            print(f"⚠️ EnvironmentalAgent: {e}")
            
    except ImportError as e:
        print(f"❌ Import failed: {e}")

def test_traffic_workers():
    """Test Traffic Workers"""
    print("\n" + "="*80)
    print("TRAFFIC WORKERS")
    print("="*80)
    
    try:
        from backend.agents.veritas_api_agent_traffic import (
            TrafficManagementWorker,
            PublicTransportWorker,
            ParkingManagementWorker
        )
        print("✅ Import successful")
        
        try:
            worker = TrafficManagementWorker(db_pool=None)
            print(f"✅ TrafficManagementWorker instantiated")
        except Exception as e:
            print(f"⚠️ TrafficManagementWorker: {e}")
        
        try:
            worker = PublicTransportWorker(db_pool=None)
            print(f"✅ PublicTransportWorker instantiated")
        except Exception as e:
            print(f"⚠️ PublicTransportWorker: {e}")
        
        try:
            worker = ParkingManagementWorker(db_pool=None)
            print(f"✅ ParkingManagementWorker instantiated")
        except Exception as e:
            print(f"⚠️ ParkingManagementWorker: {e}")
            
    except ImportError as e:
        print(f"❌ Import failed: {e}")

def test_social_workers():
    """Test Social Workers"""
    print("\n" + "="*80)
    print("SOCIAL WORKERS")
    print("="*80)
    
    try:
        from backend.agents.veritas_api_agent_social import (
            SocialBenefitsWorker,
            CitizenServicesWorker,
            HealthInsuranceWorker
        )
        print("✅ Import successful")
        
        try:
            worker = SocialBenefitsWorker(db_pool=None)
            print(f"✅ SocialBenefitsWorker instantiated")
        except Exception as e:
            print(f"⚠️ SocialBenefitsWorker: {e}")
        
        try:
            worker = CitizenServicesWorker(db_pool=None)
            print(f"✅ CitizenServicesWorker instantiated")
        except Exception as e:
            print(f"⚠️ CitizenServicesWorker: {e}")
        
        try:
            worker = HealthInsuranceWorker(db_pool=None)
            print(f"✅ HealthInsuranceWorker instantiated")
        except Exception as e:
            print(f"⚠️ HealthInsuranceWorker: {e}")
            
    except ImportError as e:
        print(f"❌ Import failed: {e}")

def test_financial_workers():
    """Test Financial Workers"""
    print("\n" + "="*80)
    print("FINANCIAL WORKERS")
    print("="*80)
    
    try:
        from backend.agents.veritas_api_agent_financial import (
            TaxAssessmentWorker,
            FundingOpportunitiesWorker,
            BusinessTaxOptimizationWorker
        )
        print("✅ Import successful")
        
        try:
            worker = TaxAssessmentWorker(db_pool=None)
            print(f"✅ TaxAssessmentWorker instantiated")
        except Exception as e:
            print(f"⚠️ TaxAssessmentWorker: {e}")
        
        try:
            worker = FundingOpportunitiesWorker(db_pool=None)
            print(f"✅ FundingOpportunitiesWorker instantiated")
        except Exception as e:
            print(f"⚠️ FundingOpportunitiesWorker: {e}")
        
        try:
            worker = BusinessTaxOptimizationWorker(db_pool=None)
            print(f"✅ BusinessTaxOptimizationWorker instantiated")
        except Exception as e:
            print(f"⚠️ BusinessTaxOptimizationWorker: {e}")
            
    except ImportError as e:
        print(f"❌ Import failed: {e}")

def test_specialized_agents():
    """Test Specialized Agents"""
    print("\n" + "="*80)
    print("SPECIALIZED AGENTS")
    print("="*80)
    
    # Chemical Data
    try:
        from backend.agents.veritas_api_agent_chemical_data import ChemicalDataAgent
        print("✅ ChemicalDataAgent import successful")
        try:
            agent = ChemicalDataAgent()
            print(f"✅ ChemicalDataAgent instantiated")
        except Exception as e:
            print(f"⚠️ ChemicalDataAgent: {e}")
    except ImportError as e:
        print(f"❌ ChemicalDataAgent import failed: {e}")
    
    # DWD Weather
    try:
        from backend.agents.veritas_api_agent_dwd_weather import DwdWeatherAgent
        print("✅ DwdWeatherAgent import successful")
        try:
            agent = DwdWeatherAgent()
            print(f"✅ DwdWeatherAgent instantiated")
        except Exception as e:
            print(f"⚠️ DwdWeatherAgent: {e}")
    except ImportError as e:
        print(f"❌ DwdWeatherAgent import failed: {e}")
    
    # Technical Standards
    try:
        from backend.agents.veritas_api_agent_technical_standards import TechnicalStandardsAgent
        print("✅ TechnicalStandardsAgent import successful")
        try:
            agent = TechnicalStandardsAgent()
            print(f"✅ TechnicalStandardsAgent instantiated")
        except Exception as e:
            print(f"⚠️ TechnicalStandardsAgent: {e}")
    except ImportError as e:
        print(f"❌ TechnicalStandardsAgent import failed: {e}")
    
    # Wikipedia
    try:
        from backend.agents.veritas_api_agent_wikipedia import WikipediaAgent
        print("✅ WikipediaAgent import successful")
        try:
            agent = WikipediaAgent()
            print(f"✅ WikipediaAgent instantiated")
        except Exception as e:
            print(f"⚠️ WikipediaAgent: {e}")
    except ImportError as e:
        print(f"❌ WikipediaAgent import failed: {e}")
    
    # Atmospheric Flow
    try:
        from backend.agents.veritas_api_agent_atmospheric_flow import AtmosphericFlowAgent
        print("✅ AtmosphericFlowAgent import successful")
        try:
            agent = AtmosphericFlowAgent()
            print(f"✅ AtmosphericFlowAgent instantiated")
        except Exception as e:
            print(f"⚠️ AtmosphericFlowAgent: {e}")
    except ImportError as e:
        print(f"❌ AtmosphericFlowAgent import failed: {e}")
    
    # Database
    try:
        from backend.agents.veritas_api_agent_database import DatabaseAgent
        print("✅ DatabaseAgent import successful")
        try:
            agent = DatabaseAgent()
            print(f"✅ DatabaseAgent instantiated")
        except Exception as e:
            print(f"⚠️ DatabaseAgent: {e}")
    except ImportError as e:
        print(f"❌ DatabaseAgent import failed: {e}")

def main():
    print("\n" + "="*80)
    print("WORKER INSTANTIATION TEST")
    print("="*80)
    print("\nThis test verifies if worker classes can be imported and instantiated.")
    print("⚠️ Some workers may require DB connections - that's expected.\n")
    
    test_construction_workers()
    test_environmental_worker()
    test_traffic_workers()
    test_social_workers()
    test_financial_workers()
    test_specialized_agents()
    
    print("\n" + "="*80)
    print("TEST COMPLETE")
    print("="*80)
    print("\n✅ Check results above to see which workers are ready.")
    print("⚠️ Workers with DB requirements will need registry integration.")

if __name__ == "__main__":
    main()
