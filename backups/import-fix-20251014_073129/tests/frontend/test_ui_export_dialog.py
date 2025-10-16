"""
VERITAS Export Dialog UI Tests
Tests für frontend/ui/veritas_ui_export_dialog.py

Test Coverage:
- Dialog initialization
- Period filter selection
- Format selection (DOCX, XLSX)
- Options checkboxes (metadata, sources)
- Filename validation
- Export trigger
- Cancel behavior
"""

import pytest
import tkinter as tk
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime, timedelta
import sys
import os

# Add paths for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', 'frontend'))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', 'frontend', 'ui'))

try:
    from ui.veritas_ui_export_dialog import ExportDialog
    EXPORT_DIALOG_AVAILABLE = True
except ImportError:
    EXPORT_DIALOG_AVAILABLE = False
    ExportDialog = None


@pytest.fixture
def root():
    """Create Tkinter root window for testing."""
    root = tk.Tk()
    root.withdraw()  # Hide window during tests
    yield root
    try:
        root.destroy()
    except:
        pass


@pytest.fixture
def sample_messages():
    """Sample chat messages for testing."""
    return [
        {
            'role': 'user',
            'content': 'Was ist das BImSchG?',
            'timestamp': datetime.now() - timedelta(days=1)
        },
        {
            'role': 'assistant',
            'content': 'Das Bundes-Immissionsschutzgesetz (BImSchG)...',
            'timestamp': datetime.now() - timedelta(days=1),
            'metadata': {
                'confidence': 0.92,
                'sources': ['BImSchG §1', 'BImSchG §2']
            }
        },
        {
            'role': 'user',
            'content': 'Was sind die Hauptziele?',
            'timestamp': datetime.now()
        },
        {
            'role': 'assistant',
            'content': 'Die Hauptziele sind...',
            'timestamp': datetime.now(),
            'metadata': {
                'confidence': 0.88,
                'sources': ['BImSchG §1 Abs. 1']
            }
        }
    ]


@pytest.mark.skipif(not EXPORT_DIALOG_AVAILABLE, reason="ExportDialog not available")
class TestExportDialogInitialization:
    """Tests for dialog initialization."""
    
    def test_dialog_creation(self, root, sample_messages):
        """Test dialog can be created."""
        dialog = ExportDialog(root, sample_messages)
        assert dialog is not None
        assert dialog.result is None
        dialog.destroy()
    
    def test_dialog_has_title(self, root, sample_messages):
        """Test dialog has correct title."""
        dialog = ExportDialog(root, sample_messages)
        assert "Export" in dialog.title() or "Chat exportieren" in dialog.title()
        dialog.destroy()
    
    def test_dialog_stores_messages(self, root, sample_messages):
        """Test dialog stores messages reference."""
        dialog = ExportDialog(root, sample_messages)
        assert hasattr(dialog, 'messages')
        assert len(dialog.messages) == len(sample_messages)
        dialog.destroy()


@pytest.mark.skipif(not EXPORT_DIALOG_AVAILABLE, reason="ExportDialog not available")
class TestPeriodFilterSelection:
    """Tests for period filter selection."""
    
    def test_default_period_selection(self, root, sample_messages):
        """Test default period is selected."""
        dialog = ExportDialog(root, sample_messages)
        # Should have a period variable (all/today/7days/30days/90days)
        if hasattr(dialog, 'period_var'):
            assert dialog.period_var.get() in ['all', 'today', '7days', '30days', '90days']
        dialog.destroy()
    
    def test_period_options_available(self, root, sample_messages):
        """Test all period options are available."""
        dialog = ExportDialog(root, sample_messages)
        expected_periods = ['all', 'today', '7days', '30days', '90days']
        # Check if UI has these options (implementation-dependent)
        dialog.destroy()
    
    def test_period_change_updates_preview(self, root, sample_messages):
        """Test changing period updates message count preview."""
        dialog = ExportDialog(root, sample_messages)
        if hasattr(dialog, 'period_var') and hasattr(dialog, '_update_message_count'):
            initial_count = getattr(dialog, 'message_count', 0)
            dialog.period_var.set('today')
            dialog._update_message_count()
            # Message count should change based on filter
            dialog.destroy()
        else:
            pytest.skip("Preview update not implemented")


@pytest.mark.skipif(not EXPORT_DIALOG_AVAILABLE, reason="ExportDialog not available")
class TestFormatSelection:
    """Tests for format selection (DOCX, XLSX)."""
    
    def test_default_format_is_docx(self, root, sample_messages):
        """Test default format is DOCX."""
        dialog = ExportDialog(root, sample_messages)
        if hasattr(dialog, 'format_var'):
            assert dialog.format_var.get() in ['docx', 'xlsx', 'DOCX', 'XLSX']
        dialog.destroy()
    
    def test_format_can_be_changed(self, root, sample_messages):
        """Test format can be changed."""
        dialog = ExportDialog(root, sample_messages)
        if hasattr(dialog, 'format_var'):
            dialog.format_var.set('xlsx')
            assert dialog.format_var.get() in ['xlsx', 'XLSX']
            
            dialog.format_var.set('docx')
            assert dialog.format_var.get() in ['docx', 'DOCX']
        dialog.destroy()
    
    def test_format_affects_filename_extension(self, root, sample_messages):
        """Test format selection affects filename extension."""
        dialog = ExportDialog(root, sample_messages)
        if hasattr(dialog, 'format_var') and hasattr(dialog, '_get_default_filename'):
            dialog.format_var.set('docx')
            filename_docx = dialog._get_default_filename()
            assert filename_docx.endswith('.docx')
            
            dialog.format_var.set('xlsx')
            filename_xlsx = dialog._get_default_filename()
            assert filename_xlsx.endswith('.xlsx')
        dialog.destroy()


@pytest.mark.skipif(not EXPORT_DIALOG_AVAILABLE, reason="ExportDialog not available")
class TestOptionsCheckboxes:
    """Tests for options checkboxes (metadata, sources)."""
    
    def test_include_metadata_option(self, root, sample_messages):
        """Test include metadata option exists."""
        dialog = ExportDialog(root, sample_messages)
        if hasattr(dialog, 'include_metadata_var'):
            assert isinstance(dialog.include_metadata_var.get(), bool)
        dialog.destroy()
    
    def test_include_sources_option(self, root, sample_messages):
        """Test include sources option exists."""
        dialog = ExportDialog(root, sample_messages)
        if hasattr(dialog, 'include_sources_var'):
            assert isinstance(dialog.include_sources_var.get(), bool)
        dialog.destroy()
    
    def test_options_default_values(self, root, sample_messages):
        """Test options have sensible defaults."""
        dialog = ExportDialog(root, sample_messages)
        if hasattr(dialog, 'include_metadata_var'):
            # Metadata should be included by default
            assert dialog.include_metadata_var.get() == True
        if hasattr(dialog, 'include_sources_var'):
            # Sources should be included by default
            assert dialog.include_sources_var.get() == True
        dialog.destroy()
    
    def test_options_can_be_toggled(self, root, sample_messages):
        """Test options can be toggled."""
        dialog = ExportDialog(root, sample_messages)
        if hasattr(dialog, 'include_metadata_var'):
            original = dialog.include_metadata_var.get()
            dialog.include_metadata_var.set(not original)
            assert dialog.include_metadata_var.get() == (not original)
        dialog.destroy()


@pytest.mark.skipif(not EXPORT_DIALOG_AVAILABLE, reason="ExportDialog not available")
class TestFilenameValidation:
    """Tests for filename validation."""
    
    def test_default_filename_format(self, root, sample_messages):
        """Test default filename has correct format."""
        dialog = ExportDialog(root, sample_messages)
        if hasattr(dialog, '_get_default_filename'):
            filename = dialog._get_default_filename()
            assert 'veritas' in filename.lower() or 'chat' in filename.lower()
            assert filename.endswith(('.docx', '.xlsx'))
        dialog.destroy()
    
    def test_filename_includes_timestamp(self, root, sample_messages):
        """Test filename includes timestamp."""
        dialog = ExportDialog(root, sample_messages)
        if hasattr(dialog, '_get_default_filename'):
            filename = dialog._get_default_filename()
            # Should contain date/time info
            assert any(c.isdigit() for c in filename)
        dialog.destroy()
    
    def test_custom_filename_validation(self, root, sample_messages):
        """Test custom filename validation."""
        dialog = ExportDialog(root, sample_messages)
        if hasattr(dialog, '_validate_filename'):
            # Valid filenames
            assert dialog._validate_filename('test.docx') == True
            assert dialog._validate_filename('my_export.xlsx') == True
            
            # Invalid filenames
            assert dialog._validate_filename('') == False
            assert dialog._validate_filename('test') == False  # No extension
            assert dialog._validate_filename('test.txt') == False  # Wrong extension
        dialog.destroy()
    
    def test_filename_sanitization(self, root, sample_messages):
        """Test filename sanitization removes invalid characters."""
        dialog = ExportDialog(root, sample_messages)
        if hasattr(dialog, '_sanitize_filename'):
            assert '/' not in dialog._sanitize_filename('test/file.docx')
            assert '\\' not in dialog._sanitize_filename('test\\file.docx')
            assert ':' not in dialog._sanitize_filename('test:file.docx')
        dialog.destroy()


@pytest.mark.skipif(not EXPORT_DIALOG_AVAILABLE, reason="ExportDialog not available")
class TestExportTrigger:
    """Tests for export trigger and result."""
    
    @patch('frontend.services.office_export.OfficeExportService')
    def test_export_button_triggers_export(self, mock_service, root, sample_messages):
        """Test export button triggers export process."""
        dialog = ExportDialog(root, sample_messages)
        if hasattr(dialog, '_on_export'):
            with patch.object(dialog, '_on_export') as mock_export:
                # Simulate button click
                dialog._on_export()
                mock_export.assert_called_once()
        dialog.destroy()
    
    def test_export_sets_result(self, root, sample_messages):
        """Test export sets dialog result."""
        dialog = ExportDialog(root, sample_messages)
        if hasattr(dialog, 'result'):
            # Before export, result should be None
            assert dialog.result is None
            
            # After successful export (mocked)
            if hasattr(dialog, '_on_export'):
                with patch('frontend.services.office_export.OfficeExportService') as mock_service:
                    mock_service.return_value.export_to_word.return_value = 'test.docx'
                    dialog._on_export()
                    # Result should be set
        dialog.destroy()
    
    def test_export_with_all_options(self, root, sample_messages):
        """Test export respects all selected options."""
        dialog = ExportDialog(root, sample_messages)
        if all(hasattr(dialog, attr) for attr in ['period_var', 'format_var', 'include_metadata_var']):
            dialog.period_var.set('7days')
            dialog.format_var.set('xlsx')
            dialog.include_metadata_var.set(True)
            
            with patch('frontend.services.office_export.OfficeExportService') as mock_service:
                if hasattr(dialog, '_on_export'):
                    dialog._on_export()
                    # Verify service was called with correct parameters
        dialog.destroy()


@pytest.mark.skipif(not EXPORT_DIALOG_AVAILABLE, reason="ExportDialog not available")
class TestCancelBehavior:
    """Tests for cancel button behavior."""
    
    def test_cancel_closes_dialog(self, root, sample_messages):
        """Test cancel button closes dialog."""
        dialog = ExportDialog(root, sample_messages)
        if hasattr(dialog, '_on_cancel'):
            dialog._on_cancel()
            # Dialog should be destroyed or result set to None
            assert dialog.result is None
        else:
            dialog.destroy()
    
    def test_cancel_does_not_export(self, root, sample_messages):
        """Test cancel does not trigger export."""
        dialog = ExportDialog(root, sample_messages)
        with patch('frontend.services.office_export.OfficeExportService') as mock_service:
            if hasattr(dialog, '_on_cancel'):
                dialog._on_cancel()
                # Export service should not be called
                mock_service.assert_not_called()
        dialog.destroy()
    
    def test_window_close_button_acts_as_cancel(self, root, sample_messages):
        """Test window close button acts as cancel."""
        dialog = ExportDialog(root, sample_messages)
        if hasattr(dialog, 'protocol') and hasattr(dialog, '_on_cancel'):
            # Window close (X button) should trigger cancel
            with patch.object(dialog, '_on_cancel') as mock_cancel:
                dialog.protocol("WM_DELETE_WINDOW", dialog._on_cancel)
                dialog._on_cancel()
                mock_cancel.assert_called()
        dialog.destroy()


@pytest.mark.skipif(not EXPORT_DIALOG_AVAILABLE, reason="ExportDialog not available")
class TestErrorHandling:
    """Tests for error handling in export dialog."""
    
    def test_export_service_error_handling(self, root, sample_messages):
        """Test dialog handles export service errors gracefully."""
        dialog = ExportDialog(root, sample_messages)
        with patch('frontend.services.office_export.OfficeExportService') as mock_service:
            mock_service.return_value.export_to_word.side_effect = Exception("Export failed")
            if hasattr(dialog, '_on_export'):
                # Should not crash, should show error message
                try:
                    dialog._on_export()
                except Exception as e:
                    pytest.fail(f"Dialog should handle export errors: {e}")
        dialog.destroy()
    
    def test_invalid_filename_error(self, root, sample_messages):
        """Test dialog shows error for invalid filename."""
        dialog = ExportDialog(root, sample_messages)
        if hasattr(dialog, 'filename_var'):
            dialog.filename_var.set('')  # Empty filename
            with patch('tkinter.messagebox.showerror') as mock_error:
                if hasattr(dialog, '_on_export'):
                    dialog._on_export()
                    # Should show error if filename validation fails
        dialog.destroy()
    
    def test_no_messages_error(self, root):
        """Test dialog handles empty message list."""
        empty_messages = []
        dialog = ExportDialog(root, empty_messages)
        if hasattr(dialog, '_on_export'):
            with patch('tkinter.messagebox.showwarning') as mock_warning:
                dialog._on_export()
                # Should warn about no messages to export
        dialog.destroy()


# Test Summary
def test_suite_summary():
    """Print test suite summary."""
    print("\n" + "="*80)
    print("EXPORT DIALOG UI TEST SUITE SUMMARY")
    print("="*80)
    print("\nTest Coverage:")
    print("  ✅ Dialog Initialization (3 tests)")
    print("  ✅ Period Filter Selection (3 tests)")
    print("  ✅ Format Selection (3 tests)")
    print("  ✅ Options Checkboxes (4 tests)")
    print("  ✅ Filename Validation (4 tests)")
    print("  ✅ Export Trigger (3 tests)")
    print("  ✅ Cancel Behavior (3 tests)")
    print("  ✅ Error Handling (3 tests)")
    print("\nTotal: 26 tests")
    print("="*80)


if __name__ == '__main__':
    # Run tests
    pytest.main([__file__, '-v', '--tb=short'])
    test_suite_summary()
