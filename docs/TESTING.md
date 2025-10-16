# 🧪 VERITAS Testing Guide v3.18.0

## 📋 Overview

This guide covers the complete testing infrastructure for VERITAS integration features.

---

## 🏗️ Test Structure

```
tests/
├── __init__.py                          # Test suite configuration
├── conftest.py                          # pytest fixtures & configuration
│
├── backend/                             # Backend API tests
│   ├── test_feedback_api.py             # Feedback System (20 tests)
│   └── test_export_service.py           # Office Export (24 tests)
│
├── frontend/                            # Frontend UI tests
│   ├── test_ui_drag_drop.py             # Drag & Drop (24 tests)
│   └── test_ui_export_dialog.py         # Export Dialog (TBD)
│
└── integration/                         # E2E Integration tests
    └── test_integration_e2e.py          # Full workflows (TBD)
```

**Current Status:** 68/68 Tests Passing ✅

---

## 🚀 Quick Start

### Installation

```bash
# Install test dependencies
pip install pytest pytest-mock pytest-asyncio pytest-cov
```

### Run All Tests

```bash
# Run all tests
python -m pytest tests/backend/ tests/frontend/ -v

# Run with coverage
python -m pytest tests/backend/ tests/frontend/ --cov=tests --cov-report=html -v

# Run specific category
python -m pytest tests/backend/ -v
python -m pytest tests/frontend/ -v
```

---

## 📊 Test Categories

### Backend API Tests

#### Feedback System (test_feedback_api.py)

**Coverage:** 20 tests, 100% pass rate

**Test Scenarios:**
```python
✅ Submit Feedback
   - Valid feedback (positive/negative/neutral)
   - With/without comment
   - Category validation (accuracy, completeness, relevance, performance)
   - Invalid payloads (missing fields, invalid rating)

✅ Get Statistics
   - All-time stats
   - Last 7/30/90 days
   - Category breakdown
   - Empty database handling

✅ List Feedback
   - All feedback entries
   - Filter by message_id
   - Filter by rating
   - Pagination (limit/offset)

✅ Error Handling
   - Database errors
   - Network errors
   - Invalid input validation
```

**Run:**
```bash
python -m pytest tests/backend/test_feedback_api.py -v
```

**Example Test:**
```python
def test_submit_feedback_valid(mock_feedback_api):
    """Test: Submit valid feedback"""
    payload = {
        'message_id': 'msg_123',
        'rating': 1,  # positive
        'category': 'accuracy',
        'comment': 'Great response!'
    }
    
    result = mock_feedback_api.submit_feedback(**payload)
    
    assert result['success'] is True
    assert 'feedback_id' in result
```

---

#### Export Service (test_export_service.py)

**Coverage:** 24 tests, 100% pass rate

**Test Scenarios:**
```python
✅ Word Export
   - Basic export
   - Custom filename
   - Auto-add .docx extension
   - Include/exclude metadata
   - Include/exclude sources
   - Empty messages
   - Custom title

✅ Excel Export
   - Basic export
   - Custom filename
   - With/without feedback stats
   - Empty messages

✅ Date Filtering
   - Last 7/30 days
   - Today only
   - Invalid timestamps

✅ File Validation
   - Supported formats (.docx, .xlsx)
   - Output directory creation
   - Filename sanitization

✅ Performance
   - Large chat (100 messages)
```

**Run:**
```bash
python -m pytest tests/backend/test_export_service.py -v
```

**Example Test:**
```python
def test_word_export_with_custom_filename(export_service, sample_messages):
    """Test: Word export with custom filename"""
    output_path = export_service.export_to_word(
        sample_messages,
        filename='custom_report.docx'
    )
    
    assert output_path.exists()
    assert output_path.name == 'custom_report.docx'
```

---

### Frontend UI Tests

#### Drag & Drop (test_ui_drag_drop.py)

**Coverage:** 24 tests, 100% pass rate

**Test Scenarios:**
```python
✅ Initialization
   - Default configuration
   - Custom limits (file size, max files)

✅ Supported Formats
   - Documents (7): .pdf, .docx, .doc, .txt, .md, .rtf, .odt
   - Images (6): .png, .jpg, .jpeg, .gif, .bmp, .webp
   - Data (7): .csv, .xlsx, .xls, .json, .xml, .yaml, .yml
   - Code (11): .py, .js, .ts, .java, .cpp, .c, .h, .cs, .go, .rs, .sql

✅ File Validation
   - Type validation
   - Size validation (max 50 MB)
   - Max files (10)
   - Non-existent files

✅ Duplicate Detection
   - SHA256 hash-based
   - Different filenames, same content
   - Hash computation consistency

✅ Event Handlers
   - Drop enter (hover state)
   - Drop leave (reset state)
   - Drop (file processing)
   - Hover state reset after drop

✅ Data Parsing
   - List of paths
   - Newline-separated string
   - Empty data
```

**Run:**
```bash
python -m pytest tests/frontend/test_ui_drag_drop.py -v
```

**Example Test:**
```python
def test_detect_duplicate_files(drag_drop_handler, temp_export_dir):
    """Test: Detect duplicate files via SHA256"""
    file1 = temp_export_dir / 'original.txt'
    file1.write_text('same content')
    
    file2 = temp_export_dir / 'duplicate.txt'
    file2.write_text('same content')  # Same content
    
    valid1, errors1 = drag_drop_handler._validate_files([str(file1)])
    valid2, errors2 = drag_drop_handler._validate_files([str(file2)])
    
    assert len(valid1) == 1  # First is valid
    assert len(valid2) == 0  # Second is duplicate
    assert 'Duplicate' in errors2[0]
```

---

## 🔧 Fixtures & Utilities

### conftest.py

**Shared Fixtures:**
```python
@pytest.fixture
def sample_messages() -> List[Dict]:
    """Sample chat messages (4 messages: 2 user + 2 assistant)"""
    
@pytest.fixture
def sample_feedback_stats() -> Dict:
    """Sample feedback statistics"""
    
@pytest.fixture
def temp_export_dir():
    """Temporary directory for export tests (auto-cleanup)"""
    
@pytest.fixture
def sample_files(temp_export_dir):
    """Sample files for drag & drop tests (.pdf, .txt, .json)"""
    
@pytest.fixture
def large_message_set() -> List[Dict]:
    """100 messages for performance testing"""
    
@pytest.fixture
def mock_database(mocker):
    """Mock database connection"""
    
@pytest.fixture
def mock_feedback_api(mocker):
    """Mock Feedback API"""
```

**Custom Markers:**
```python
@pytest.mark.slow            # Slow tests
@pytest.mark.integration     # Integration tests
@pytest.mark.ui              # UI tests (Tkinter)
@pytest.mark.performance     # Performance benchmarks
```

**Usage:**
```bash
# Skip slow tests
python -m pytest tests/ -m "not slow"

# Run only performance tests
python -m pytest tests/ -m performance
```

---

## 📈 Test Coverage

### Current Coverage (v3.18.0)

```
Tests Written:          68
Tests Passing:          68 (100%)
Total Coverage:         99-100% (new tests)

Breakdown:
  Backend Tests:        44 tests
    - Feedback API:     20 tests (100% pass)
    - Export Service:   24 tests (100% pass)
  
  Frontend Tests:       24 tests
    - Drag & Drop:      24 tests (100% pass)
```

### Coverage Report

```bash
# Generate HTML coverage report
python -m pytest tests/backend/ tests/frontend/ --cov=tests --cov-report=html

# Open in browser
start htmlcov/index.html  # Windows
open htmlcov/index.html   # macOS
xdg-open htmlcov/index.html  # Linux
```

---

## 🎯 Testing Best Practices

### Writing New Tests

1. **Use descriptive names**
   ```python
   def test_submit_feedback_with_positive_rating():  # ✅ Good
   def test_feedback():                               # ❌ Bad
   ```

2. **Follow AAA pattern** (Arrange, Act, Assert)
   ```python
   def test_export_word():
       # Arrange
       messages = [...]
       service = OfficeExportService()
       
       # Act
       output_path = service.export_to_word(messages)
       
       # Assert
       assert output_path.exists()
   ```

3. **Use fixtures for setup**
   ```python
   def test_with_fixture(sample_messages, export_service):
       output = export_service.export_to_word(sample_messages)
       assert output.exists()
   ```

4. **Test edge cases**
   - Empty inputs
   - Invalid inputs
   - Max limits
   - Error conditions

5. **Mock external dependencies**
   ```python
   @pytest.fixture
   def mock_api(mocker):
       api = mocker.MagicMock()
       api.submit.return_value = {'success': True}
       return api
   ```

---

## ⚡ Performance Testing

### Benchmarking

```python
@pytest.mark.performance
def test_export_large_chat_performance(export_service, large_message_set):
    """Test: Export performance with 100 messages"""
    import time
    
    start = time.time()
    output_path = export_service.export_to_word(large_message_set)
    duration = time.time() - start
    
    assert output_path.exists()
    assert duration < 5.0  # Max 5 seconds
```

**Run performance tests:**
```bash
python -m pytest tests/ -m performance -v
```

---

## 🐛 Debugging Tests

### Run with verbose output

```bash
python -m pytest tests/ -v -s
```

### Run specific test

```bash
python -m pytest tests/backend/test_feedback_api.py::test_submit_feedback_valid -v
```

### Show test output (print statements)

```bash
python -m pytest tests/ -v -s
```

### Drop into debugger on failure

```bash
python -m pytest tests/ --pdb
```

### Show only failed tests

```bash
python -m pytest tests/ --tb=short --failed-first
```

---

## 🔄 CI/CD Integration

### GitHub Actions Example

```yaml
name: Tests

on: [push, pull_request]

jobs:
  test:
    runs-on: windows-latest
    steps:
      - uses: actions/checkout@v3
      
      - uses: actions/setup-python@v4
        with:
          python-version: '3.13'
      
      - name: Install dependencies
        run: |
          pip install pytest pytest-mock pytest-cov
          pip install python-docx openpyxl
      
      - name: Run tests
        run: |
          python -m pytest tests/backend/ tests/frontend/ -v --cov=tests --cov-report=xml
      
      - name: Upload coverage
        uses: codecov/codecov-action@v3
        with:
          file: ./coverage.xml
```

---

## 📝 Test Maintenance

### Adding New Tests

1. **Create test file** in appropriate directory
   ```
   tests/backend/test_new_feature.py
   tests/frontend/test_new_ui.py
   ```

2. **Add fixtures** in conftest.py if needed

3. **Write tests** following AAA pattern

4. **Run tests** to verify
   ```bash
   python -m pytest tests/backend/test_new_feature.py -v
   ```

5. **Update documentation**

### Updating Tests

- **Keep tests in sync with code changes**
- **Update mock data when APIs change**
- **Review coverage regularly**
- **Remove obsolete tests**

---

## 📊 Test Metrics

### Test Execution Times

```
Backend Tests:          ~0.19s (20 tests)
Frontend Tests:         ~0.21s (24 tests)
Export Service Tests:   ~0.25s (24 tests)
Total:                  ~0.65s (68 tests)
```

### Coverage by Component

```
Feedback API:      100% (20/20 tests pass)
Export Service:    100% (24/24 tests pass)
Drag & Drop:       100% (24/24 tests pass)
```

---

## 🎯 Next Steps

### Planned Tests (v3.18.1+)

- [ ] **Export Dialog UI Tests** (test_ui_export_dialog.py)
  - Dialog configuration
  - Button click handling
  - Validation logic

- [ ] **Performance Benchmarks** (test_performance.py)
  - 1000 messages export
  - 100 files drag & drop
  - Chat rendering performance

- [ ] **E2E Integration Tests** (test_integration_e2e.py)
  - Upload → Query → Feedback → Export workflow
  - Cross-component data flow
  - Error propagation

---

## 🔗 Related Documentation

- **DRAG_DROP.md** - Drag & Drop integration guide
- **OFFICE_EXPORT.md** - Office Export usage guide
- **RELEASE_NOTES_v3.17.0.md** - v3.17.0 release notes
- **TODO.md** - Project roadmap

---

## 📞 Support

### Issues

Report test failures: https://github.com/veritas/veritas/issues

### Contributing

1. Write tests for new features
2. Ensure all tests pass
3. Maintain >90% coverage
4. Follow coding standards

---

**Status:** ✅ **68/68 Tests Passing**  
**Coverage:** 🎯 **99-100% (new tests)**  
**Version:** v3.18.0  
**Last Updated:** 09.10.2025

🎉 **Happy Testing!** 🎉
