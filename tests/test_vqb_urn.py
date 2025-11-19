"""
Tests for VCC-URN Implementation

Tests the URN class and factory functions.
"""

import unittest
from vqb_frontend.utils.urn import (
    URN, URNNamespace,
    create_vpb_process_urn,
    create_vpb_process_step_urn,
    create_chunk_urn,
    create_legal_domain_urn,
    create_legal_norm_urn,
    create_federal_urn,
    create_authority_urn,
    create_document_urn,
    create_graph_relationship_urn
)


class TestURN(unittest.TestCase):
    """Tests for URN class"""
    
    def test_basic_urn_creation(self):
        """Test creating a basic URN"""
        urn = URN(
            namespace=URNNamespace.VPB,
            type="process",
            identifier="proc-001"
        )
        
        self.assertEqual(str(urn), "urn:vcc:vpb:process:proc-001")
    
    def test_urn_with_subidentifiers(self):
        """Test URN with subidentifiers"""
        urn = URN(
            namespace=URNNamespace.VPB,
            type="process",
            identifier="proc-001",
            subidentifiers=[("step", "step-001")]
        )
        
        self.assertEqual(str(urn), "urn:vcc:vpb:process:proc-001:step:step-001")
    
    def test_parse_basic_urn(self):
        """Test parsing URN from string"""
        urn_string = "urn:vcc:vpb:process:proc-001"
        urn = URN.from_string(urn_string)
        
        self.assertEqual(urn.namespace, URNNamespace.VPB)
        self.assertEqual(urn.type, "process")
        self.assertEqual(urn.identifier, "proc-001")
        self.assertEqual(len(urn.subidentifiers), 0)
    
    def test_parse_urn_with_subidentifiers(self):
        """Test parsing URN with subidentifiers"""
        urn_string = "urn:vcc:vpb:process:proc-001:step:step-001"
        urn = URN.from_string(urn_string)
        
        self.assertEqual(urn.namespace, URNNamespace.VPB)
        self.assertEqual(len(urn.subidentifiers), 1)
        self.assertEqual(urn.subidentifiers[0], ("step", "step-001"))
    
    def test_parse_invalid_urn(self):
        """Test parsing invalid URN raises error"""
        with self.assertRaises(ValueError):
            URN.from_string("invalid:urn")
        
        with self.assertRaises(ValueError):
            URN.from_string("urn:vcc:")  # Too short
    
    def test_add_subidentifier(self):
        """Test adding subidentifier"""
        urn = URN(URNNamespace.VPB, "process", "proc-001")
        urn2 = urn.add_subidentifier("step", "step-001")
        
        # Original unchanged
        self.assertEqual(len(urn.subidentifiers), 0)
        
        # New URN has subidentifier
        self.assertEqual(len(urn2.subidentifiers), 1)
        self.assertEqual(str(urn2), "urn:vcc:vpb:process:proc-001:step:step-001")
    
    def test_get_subidentifier(self):
        """Test getting subidentifier value"""
        urn = URN(
            URNNamespace.LEGAL,
            "norm",
            "bimschg:2024",
            subidentifiers=[("para", "5"), ("abs", "1")]
        )
        
        self.assertEqual(urn.get_subidentifier("para"), "5")
        self.assertEqual(urn.get_subidentifier("abs"), "1")
        self.assertIsNone(urn.get_subidentifier("unknown"))
    
    def test_has_subidentifier(self):
        """Test checking for subidentifier"""
        urn = URN(
            URNNamespace.LEGAL,
            "norm",
            "bimschg:2024",
            subidentifiers=[("para", "5")]
        )
        
        self.assertTrue(urn.has_subidentifier("para"))
        self.assertFalse(urn.has_subidentifier("abs"))
    
    def test_urn_equality(self):
        """Test URN equality"""
        urn1 = URN(URNNamespace.VPB, "process", "proc-001")
        urn2 = URN(URNNamespace.VPB, "process", "proc-001")
        urn3 = URN(URNNamespace.VPB, "process", "proc-002")
        
        self.assertEqual(urn1, urn2)
        self.assertNotEqual(urn1, urn3)
    
    def test_urn_hash(self):
        """Test URN hashing"""
        urn = URN(URNNamespace.VPB, "process", "proc-001")
        hash_str = urn.get_hash(8)
        
        self.assertEqual(len(hash_str), 8)
        self.assertIsInstance(hash_str, str)
    
    def test_to_dict(self):
        """Test URN to dict conversion"""
        urn = URN(
            URNNamespace.VPB,
            "process",
            "proc-001",
            subidentifiers=[("step", "step-001")]
        )
        
        urn_dict = urn.to_dict()
        
        self.assertEqual(urn_dict["urn"], "urn:vcc:vpb:process:proc-001:step:step-001")
        self.assertEqual(urn_dict["namespace"], "vpb")
        self.assertEqual(urn_dict["type"], "process")
        self.assertEqual(urn_dict["identifier"], "proc-001")
        self.assertEqual(urn_dict["subidentifiers"]["step"], "step-001")


class TestURNFactories(unittest.TestCase):
    """Tests for URN factory functions"""
    
    def test_create_vpb_process_urn(self):
        """Test VPB process URN creation"""
        urn = create_vpb_process_urn("baugenehmigung-2024-001")
        
        self.assertEqual(str(urn), "urn:vcc:vpb:process:baugenehmigung-2024-001")
        self.assertEqual(urn.namespace, URNNamespace.VPB)
        self.assertEqual(urn.type, "process")
    
    def test_create_vpb_process_step_urn(self):
        """Test VPB process step URN creation"""
        urn = create_vpb_process_step_urn("proc-001", "step-001")
        
        expected = "urn:vcc:vpb:process:proc-001:step:step-001"
        self.assertEqual(str(urn), expected)
        self.assertTrue(urn.has_subidentifier("step"))
    
    def test_create_chunk_urn(self):
        """Test chunk URN creation"""
        urn = create_chunk_urn("bimschg", "bimschg-2024-001", 42)
        
        expected = "urn:vcc:chunk:bimschg:bimschg-2024-001:42"
        self.assertEqual(str(urn), expected)
        self.assertEqual(urn.namespace, URNNamespace.CHUNK)
        self.assertEqual(urn.type, "bimschg")
    
    def test_create_legal_domain_urn(self):
        """Test legal domain URN creation"""
        # Without subdomain
        urn1 = create_legal_domain_urn("baurecht")
        self.assertEqual(str(urn1), "urn:vcc:legal:domain:baurecht")
        
        # With subdomain
        urn2 = create_legal_domain_urn("umweltrecht", "immissionsschutz")
        self.assertEqual(str(urn2), "urn:vcc:legal:domain:umweltrecht:subdomain:immissionsschutz")
    
    def test_create_legal_norm_urn(self):
        """Test legal norm URN creation"""
        # Basic norm
        urn1 = create_legal_norm_urn("bimschg", 2024)
        self.assertEqual(str(urn1), "urn:vcc:legal:norm:bimschg:year:2024")
        
        # With paragraph
        urn2 = create_legal_norm_urn("vwvfg", 1976, paragraph="28")
        self.assertEqual(str(urn2), "urn:vcc:legal:norm:vwvfg:year:1976:para:28")
        
        # With paragraph and absatz
        urn3 = create_legal_norm_urn("bgb", 2002, paragraph="110", absatz=1)
        self.assertEqual(str(urn3), "urn:vcc:legal:norm:bgb:year:2002:para:110:abs:1")
    
    def test_create_federal_urn(self):
        """Test federal level URN creation"""
        urn1 = create_federal_urn("bund", "de")
        self.assertEqual(str(urn1), "urn:vcc:fed:bund:de")
        
        urn2 = create_federal_urn("land", "brandenburg")
        self.assertEqual(str(urn2), "urn:vcc:fed:land:brandenburg")
    
    def test_create_authority_urn(self):
        """Test authority URN creation"""
        urn = create_authority_urn("bmu")
        self.assertEqual(str(urn), "urn:vcc:org:authority:bmu")
    
    def test_create_document_urn(self):
        """Test document URN creation"""
        # Without version
        urn1 = create_document_urn("pdf", "doc-001")
        self.assertEqual(str(urn1), "urn:vcc:doc:pdf:doc-001")
        
        # With version
        urn2 = create_document_urn("docx", "doc-002", version="2")
        self.assertEqual(str(urn2), "urn:vcc:doc:docx:doc-002:version:2")
    
    def test_create_graph_relationship_urn(self):
        """Test graph relationship URN creation"""
        source_urn = create_chunk_urn("bimschg", "doc-001", 42)
        target_urn = create_legal_domain_urn("umweltrecht")
        
        rel_urn = create_graph_relationship_urn("belongs-to", source_urn, target_urn)
        
        self.assertEqual(rel_urn.namespace, URNNamespace.GRAPH)
        self.assertEqual(rel_urn.type, "rel")
        self.assertIn("belongs-to", rel_urn.identifier)


class TestURNRoundTrip(unittest.TestCase):
    """Test URN serialization/deserialization"""
    
    def test_roundtrip_simple_urn(self):
        """Test round-trip for simple URN"""
        original = create_vpb_process_urn("proc-001")
        urn_string = str(original)
        parsed = URN.from_string(urn_string)
        
        self.assertEqual(original, parsed)
    
    def test_roundtrip_complex_urn(self):
        """Test round-trip for complex URN"""
        original = create_legal_norm_urn("bgb", 2002, paragraph="110", absatz=1)
        urn_string = str(original)
        parsed = URN.from_string(urn_string)
        
        self.assertEqual(original, parsed)
        self.assertEqual(parsed.get_subidentifier("para"), "110")
        self.assertEqual(parsed.get_subidentifier("abs"), "1")


if __name__ == "__main__":
    unittest.main()
