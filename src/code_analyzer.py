"""Code analysis module integrating various static analysis tools."""
import os
import subprocess
from dataclasses import dataclass
from typing import List, Dict, Any, Optional
from pathlib import Path
import json

from pylint.lint import Run as PylintRun
from pylint.reporters import JSONReporter
import radon.complexity as radon_cc
import radon.metrics as radon_metrics
from radon.visitors import ComplexityVisitor

@dataclass
class AnalysisResult:
    """Container for code analysis results."""
    linting_score: float
    linting_messages: List[Dict[str, Any]]
    complexity_score: float
    maintainability_index: float
    security_issues: List[Dict[str, Any]]
    style_issues: List[str]
    
class CodeAnalyzer:
    """Analyzes Python code using various static analysis tools."""
    
    def __init__(self, workspace_dir: str):
        """Initialize the analyzer with workspace directory."""
        self.workspace_dir = Path(workspace_dir)
        
    def analyze_file(self, file_path: str) -> AnalysisResult:
        """Analyze a single Python file using all available tools."""
        abs_path = str(self.workspace_dir / file_path)
        
        if not os.path.exists(abs_path):
            raise FileNotFoundError(f"File not found: {abs_path}")
        
        # Run pylint analysis
        linting_score, linting_messages = self._run_pylint(abs_path)
        
        # Calculate code complexity
        complexity_score = self._analyze_complexity(abs_path)
        
        # Calculate maintainability index
        maintainability_index = self._calculate_maintainability_index(abs_path)
        
        # Run security scan
        security_issues = self._run_security_scan(abs_path)
        
        # Check code style
        style_issues = self._check_code_style(abs_path)
        
        return AnalysisResult(
            linting_score=linting_score,
            linting_messages=linting_messages,
            complexity_score=complexity_score,
            maintainability_index=maintainability_index,
            security_issues=security_issues,
            style_issues=style_issues
        )
    
    def _run_pylint(self, file_path: str) -> tuple[float, List[Dict[str, Any]]]:
        """Run pylint on a file and return the score and messages."""
        reporter = JSONReporter()
        try:
            # Run pylint with exit=False to prevent sys.exit
            PylintRun([file_path], reporter=reporter, exit=False)
            
            # Calculate score based on message types
            score = 10.0
            deductions = {
                'error': 1.0,
                'warning': 0.5,
                'convention': 0.1,
                'refactor': 0.2
            }
            
            for msg in reporter.messages:
                msg_type = msg.get('type', '')
                if msg_type in deductions:
                    score -= deductions[msg_type]
            
            return max(0.0, score), reporter.messages
        except Exception as e:
            return 0.0, [{'type': 'error', 'message': str(e)}]
    
    def _analyze_complexity(self, file_path: str) -> float:
        """Analyze code complexity using radon."""
        with open(file_path, 'r', encoding='utf-8') as f:
            code = f.read()
            
        # Calculate average complexity
        blocks = ComplexityVisitor.from_code(code).blocks
        if not blocks:
            return 0.0
            
        total_complexity = sum(block.complexity for block in blocks)
        return total_complexity / len(blocks)
    
    def _calculate_maintainability_index(self, file_path: str) -> float:
        """Calculate maintainability index using radon."""
        with open(file_path, 'r', encoding='utf-8') as f:
            code = f.read()
            
        # Get raw maintainability index
        raw_mi = radon_metrics.mi_visit(code, multi=True)
        
        # Normalize to 0-100 scale and invert (lower is better)
        normalized_mi = max(0.0, min(100.0, raw_mi))
        return 100.0 - normalized_mi
    
    def _run_security_scan(self, file_path: str) -> List[Dict[str, Any]]:
        """Run bandit security scanner on the file."""
        cmd = ['bandit', '-f', 'json', file_path]
        try:
            result = subprocess.run(cmd, capture_output=True, text=True, check=True)
            data = json.loads(result.stdout)
            return data.get('results', [])
        except (subprocess.CalledProcessError, json.JSONDecodeError):
            return []
    
    def _check_code_style(self, file_path: str) -> List[str]:
        """Check code style using black."""
        cmd = ['black', '--check', '--diff', file_path]
        try:
            subprocess.run(cmd, capture_output=True, text=True, check=True)
            return []  # No style issues if black check passes
        except subprocess.CalledProcessError as e:
            # Return the diff as style issues
            return e.output.splitlines() if e.output else ['Style issues detected'] 