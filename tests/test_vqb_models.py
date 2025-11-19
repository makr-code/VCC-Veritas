"""
Tests for VQB Frontend Models

Basic unit tests for Process and Document models.
"""

import unittest
from datetime import datetime, timedelta

from vqb_frontend.models.process_model import (
    Process, ProcessModel, ProcessStatus
)
from vqb_frontend.models.document_model import (
    Document, DocumentModel, DocumentType, Relationship, RelationshipType
)


class TestProcessModel(unittest.TestCase):
    """Tests for Process and ProcessModel"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.model = ProcessModel()
        self.now = datetime.now()
        
        self.process1 = Process(
            id="p1",
            title="Process 1",
            start_time=self.now,
            end_time=self.now + timedelta(days=7),
            status=ProcessStatus.PLANNED
        )
        
        self.process2 = Process(
            id="p2",
            title="Process 2",
            start_time=self.now + timedelta(days=7),
            end_time=self.now + timedelta(days=14),
            status=ProcessStatus.IN_PROGRESS
        )
    
    def test_add_process(self):
        """Test adding a process"""
        self.model.add_process(self.process1)
        
        self.assertEqual(self.model.get_count(), 1)
        self.assertEqual(self.model.get_process("p1"), self.process1)
    
    def test_update_process(self):
        """Test updating a process"""
        self.model.add_process(self.process1)
        
        self.model.update_process("p1", status=ProcessStatus.COMPLETED)
        
        updated = self.model.get_process("p1")
        self.assertEqual(updated.status, ProcessStatus.COMPLETED)
    
    def test_remove_process(self):
        """Test removing a process"""
        self.model.add_process(self.process1)
        self.model.remove_process("p1")
        
        self.assertEqual(self.model.get_count(), 0)
        self.assertIsNone(self.model.get_process("p1"))
    
    def test_get_all_processes(self):
        """Test getting all processes"""
        self.model.add_process(self.process1)
        self.model.add_process(self.process2)
        
        all_processes = self.model.get_all_processes()
        self.assertEqual(len(all_processes), 2)
    
    def test_filter_by_status(self):
        """Test filtering by status"""
        self.model.add_process(self.process1)
        self.model.add_process(self.process2)
        
        planned = self.model.get_processes_by_status(ProcessStatus.PLANNED)
        self.assertEqual(len(planned), 1)
        self.assertEqual(planned[0].id, "p1")
        
        in_progress = self.model.get_processes_by_status(ProcessStatus.IN_PROGRESS)
        self.assertEqual(len(in_progress), 1)
        self.assertEqual(in_progress[0].id, "p2")
    
    def test_process_duration(self):
        """Test process duration calculation"""
        duration = self.process1.duration_days
        self.assertEqual(duration, 7.0)
    
    def test_observer_notification(self):
        """Test that observers are notified"""
        notifications = []
        
        def observer(event, **kwargs):
            notifications.append(event)
        
        self.model.attach(observer)
        self.model.add_process(self.process1)
        self.model.update_process("p1", status=ProcessStatus.COMPLETED)
        self.model.remove_process("p1")
        
        self.assertEqual(len(notifications), 3)
        self.assertIn("process_added", notifications)
        self.assertIn("process_updated", notifications)
        self.assertIn("process_removed", notifications)


class TestDocumentModel(unittest.TestCase):
    """Tests for Document and DocumentModel"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.model = DocumentModel()
        
        self.doc1 = Document(
            id="d1",
            title="Document 1",
            doc_type=DocumentType.PDF,
            authority="Authority A",
            year=2024
        )
        
        self.doc2 = Document(
            id="d2",
            title="Document 2",
            doc_type=DocumentType.DOCX,
            authority="Authority B",
            year=2024
        )
    
    def test_add_document(self):
        """Test adding a document"""
        self.model.add_document(self.doc1)
        
        self.assertEqual(self.model.get_count(), 1)
        self.assertEqual(self.model.get_document("d1"), self.doc1)
    
    def test_update_document(self):
        """Test updating a document"""
        self.model.add_document(self.doc1)
        
        self.model.update_document("d1", relevance_score=0.95)
        
        updated = self.model.get_document("d1")
        self.assertEqual(updated.relevance_score, 0.95)
    
    def test_remove_document(self):
        """Test removing a document"""
        self.model.add_document(self.doc1)
        self.model.remove_document("d1")
        
        self.assertEqual(self.model.get_count(), 0)
        self.assertIsNone(self.model.get_document("d1"))
    
    def test_filter_by_type(self):
        """Test filtering by document type"""
        self.model.add_document(self.doc1)
        self.model.add_document(self.doc2)
        
        pdfs = self.model.get_documents_by_type(DocumentType.PDF)
        self.assertEqual(len(pdfs), 1)
        self.assertEqual(pdfs[0].id, "d1")
    
    def test_relationships(self):
        """Test document relationships"""
        # Add relationship
        rel = Relationship(
            source_id="p1",
            target_id="d1",
            rel_type=RelationshipType.GRAPH,
            weight=0.8
        )
        self.doc1.relationships.append(rel)
        self.model.add_document(self.doc1)
        
        # Get related documents
        related = self.model.get_related_documents("p1")
        self.assertEqual(len(related), 1)
        self.assertEqual(related[0].id, "d1")
        
        # Filter by relationship type
        graph_related = self.model.get_related_documents("p1", RelationshipType.GRAPH)
        self.assertEqual(len(graph_related), 1)
        
        vector_related = self.model.get_related_documents("p1", RelationshipType.VECTOR)
        self.assertEqual(len(vector_related), 0)
    
    def test_observer_notification(self):
        """Test that observers are notified"""
        notifications = []
        
        def observer(event, **kwargs):
            notifications.append(event)
        
        self.model.attach(observer)
        self.model.add_document(self.doc1)
        self.model.update_document("d1", relevance_score=0.9)
        self.model.remove_document("d1")
        
        self.assertEqual(len(notifications), 3)
        self.assertIn("document_added", notifications)
        self.assertIn("document_updated", notifications)
        self.assertIn("document_removed", notifications)


class TestSerialization(unittest.TestCase):
    """Tests for model serialization"""
    
    def test_process_serialization(self):
        """Test Process to_dict and from_dict"""
        now = datetime.now()
        process = Process(
            id="p1",
            title="Test Process",
            start_time=now,
            end_time=now + timedelta(days=7),
            status=ProcessStatus.PLANNED,
            authority="Test Authority"
        )
        
        # Serialize
        data = process.to_dict()
        
        # Deserialize
        restored = Process.from_dict(data)
        
        self.assertEqual(restored.id, process.id)
        self.assertEqual(restored.title, process.title)
        self.assertEqual(restored.status, process.status)
        self.assertEqual(restored.authority, process.authority)
    
    def test_document_serialization(self):
        """Test Document to_dict and from_dict"""
        doc = Document(
            id="d1",
            title="Test Document",
            doc_type=DocumentType.PDF,
            authority="Test Authority",
            year=2024
        )
        
        # Add relationship
        rel = Relationship(
            source_id="p1",
            target_id="d1",
            rel_type=RelationshipType.GRAPH
        )
        doc.relationships.append(rel)
        
        # Serialize
        data = doc.to_dict()
        
        # Deserialize
        restored = Document.from_dict(data)
        
        self.assertEqual(restored.id, doc.id)
        self.assertEqual(restored.title, doc.title)
        self.assertEqual(restored.doc_type, doc.doc_type)
        self.assertEqual(len(restored.relationships), 1)
        self.assertEqual(restored.relationships[0].rel_type, RelationshipType.GRAPH)


if __name__ == "__main__":
    unittest.main()
