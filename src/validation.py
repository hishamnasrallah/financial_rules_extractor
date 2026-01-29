"""
HITL (Human-in-the-Loop) validation module for manual review and approval.
"""
from typing import List, Optional, Dict, Any
from datetime import datetime
from pathlib import Path
import json

from loguru import logger

from src.models import ExtractedRule, ValidationResult, RuleStatus


class ValidationManager:
    """Manager for HITL validation workflow."""
    
    def __init__(self, storage_path: Optional[Path] = None):
        """
        Initialize validation manager.
        
        Args:
            storage_path: Path to store validation records
        """
        self.storage_path = storage_path or Path("data/validation")
        self.storage_path.mkdir(parents=True, exist_ok=True)
        
        self.pending_validations = {}
        self.validation_history = []
        
        self._load_history()
    
    def submit_for_review(
        self, 
        rules: List[ExtractedRule],
        reason: str = "Standard review"
    ) -> Dict[str, Any]:
        """
        Submit rules for human review.
        
        Args:
            rules: List of rules to review
            reason: Reason for review
            
        Returns:
            Submission details
        """
        logger.info(f"Submitting {len(rules)} rules for review")
        
        submission_id = f"submission_{int(datetime.now().timestamp())}"
        
        submission = {
            'submission_id': submission_id,
            'submitted_at': datetime.now().isoformat(),
            'reason': reason,
            'rules': [
                {
                    'rule_id': rule.rule_id,
                    'text_ar': rule.text_ar,
                    'track_id': rule.track_id,
                    'mapping_confidence': rule.mapping_confidence,
                    'status': rule.status.value,
                    'source': rule.source_reference.document_name
                }
                for rule in rules
            ],
            'status': 'pending'
        }
        
        # Store submission
        self.pending_validations[submission_id] = submission
        self._save_submission(submission)
        
        logger.info(f"Submission created: {submission_id}")
        
        return {
            'submission_id': submission_id,
            'num_rules': len(rules),
            'status': 'pending'
        }
    
    def validate_rule(
        self,
        rule_id: str,
        decision: str,
        validator_name: Optional[str] = None,
        comments: Optional[str] = None,
        modified_text: Optional[str] = None,
        modified_track: Optional[str] = None
    ) -> ValidationResult:
        """
        Validate a single rule.
        
        Args:
            rule_id: Rule ID to validate
            decision: approve, reject, or modify
            validator_name: Name of the validator
            comments: Validation comments
            modified_text: Modified rule text (if decision is 'modify')
            modified_track: Modified track mapping (if decision is 'modify')
            
        Returns:
            ValidationResult object
        """
        logger.info(f"Validating rule {rule_id}: {decision}")
        
        validation = ValidationResult(
            rule_id=rule_id,
            validator_name=validator_name,
            validated_at=datetime.now(),
            decision=decision,
            comments=comments,
            modified_text=modified_text,
            modified_track=modified_track
        )
        
        # Store validation
        self.validation_history.append(validation)
        self._save_validation(validation)
        
        return validation
    
    def batch_validate(
        self,
        validations: List[Dict[str, Any]],
        validator_name: Optional[str] = None
    ) -> List[ValidationResult]:
        """
        Validate multiple rules in batch.
        
        Args:
            validations: List of validation dictionaries
            validator_name: Name of the validator
            
        Returns:
            List of validation results
        """
        logger.info(f"Batch validating {len(validations)} rules")
        
        results = []
        for val_data in validations:
            result = self.validate_rule(
                rule_id=val_data['rule_id'],
                decision=val_data['decision'],
                validator_name=validator_name,
                comments=val_data.get('comments'),
                modified_text=val_data.get('modified_text'),
                modified_track=val_data.get('modified_track')
            )
            results.append(result)
        
        return results
    
    def apply_validations(
        self,
        rules: List[ExtractedRule],
        validations: List[ValidationResult]
    ) -> List[ExtractedRule]:
        """
        Apply validation results to rules.
        
        Args:
            rules: List of rules
            validations: List of validation results
            
        Returns:
            Updated rules
        """
        logger.info(f"Applying {len(validations)} validations")
        
        # Create validation map
        validation_map = {v.rule_id: v for v in validations}
        
        for rule in rules:
            if rule.rule_id in validation_map:
                validation = validation_map[rule.rule_id]
                
                if validation.decision == 'approve':
                    rule.status = RuleStatus.APPROVED
                
                elif validation.decision == 'reject':
                    rule.status = RuleStatus.REJECTED
                
                elif validation.decision == 'modify':
                    if validation.modified_text:
                        rule.text_ar = validation.modified_text
                    if validation.modified_track:
                        rule.track_id = validation.modified_track
                    rule.status = RuleStatus.APPROVED
                    rule.notes = f"Modified by {validation.validator_name or 'validator'}"
        
        return rules
    
    def get_pending_submissions(self) -> List[Dict[str, Any]]:
        """Get all pending validation submissions."""
        return [
            sub for sub in self.pending_validations.values()
            if sub['status'] == 'pending'
        ]
    
    def get_validation_history(
        self,
        rule_id: Optional[str] = None
    ) -> List[ValidationResult]:
        """
        Get validation history.
        
        Args:
            rule_id: Filter by rule ID (optional)
            
        Returns:
            List of validation results
        """
        if rule_id:
            return [v for v in self.validation_history if v.rule_id == rule_id]
        return self.validation_history
    
    def generate_validation_report(self) -> Dict[str, Any]:
        """Generate validation statistics report."""
        
        total_validations = len(self.validation_history)
        
        if total_validations == 0:
            return {
                'total_validations': 0,
                'by_decision': {},
                'by_validator': {}
            }
        
        # Count by decision
        by_decision = {}
        by_validator = {}
        
        for validation in self.validation_history:
            # By decision
            decision = validation.decision
            by_decision[decision] = by_decision.get(decision, 0) + 1
            
            # By validator
            validator = validation.validator_name or 'Unknown'
            by_validator[validator] = by_validator.get(validator, 0) + 1
        
        return {
            'total_validations': total_validations,
            'by_decision': by_decision,
            'by_validator': by_validator,
            'approval_rate': round(
                by_decision.get('approve', 0) / total_validations * 100, 2
            ) if total_validations > 0 else 0.0
        }
    
    def _save_submission(self, submission: Dict[str, Any]):
        """Save submission to file."""
        file_path = self.storage_path / f"{submission['submission_id']}.json"
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(submission, f, ensure_ascii=False, indent=2)
    
    def _save_validation(self, validation: ValidationResult):
        """Save validation to file."""
        file_path = self.storage_path / "validations.jsonl"
        
        validation_dict = {
            'rule_id': validation.rule_id,
            'validator_name': validation.validator_name,
            'validated_at': validation.validated_at.isoformat(),
            'decision': validation.decision,
            'comments': validation.comments,
            'modified_text': validation.modified_text,
            'modified_track': validation.modified_track
        }
        
        with open(file_path, 'a', encoding='utf-8') as f:
            f.write(json.dumps(validation_dict, ensure_ascii=False) + '\n')
    
    def _load_history(self):
        """Load validation history from file."""
        file_path = self.storage_path / "validations.jsonl"
        
        if not file_path.exists():
            return
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                for line in f:
                    if line.strip():
                        data = json.loads(line)
                        validation = ValidationResult(
                            rule_id=data['rule_id'],
                            validator_name=data['validator_name'],
                            validated_at=datetime.fromisoformat(data['validated_at']),
                            decision=data['decision'],
                            comments=data.get('comments'),
                            modified_text=data.get('modified_text'),
                            modified_track=data.get('modified_track')
                        )
                        self.validation_history.append(validation)
        
        except Exception as e:
            logger.error(f"Failed to load validation history: {e}")


class AuditTrail:
    """Maintain audit trail for all agent decisions."""
    
    def __init__(self, storage_path: Optional[Path] = None):
        """
        Initialize audit trail.
        
        Args:
            storage_path: Path to store audit logs
        """
        self.storage_path = storage_path or Path("data/audit")
        self.storage_path.mkdir(parents=True, exist_ok=True)
        
        self.log_file = self.storage_path / "audit_trail.jsonl"
    
    def log_event(
        self,
        event_type: str,
        details: Dict[str, Any],
        user: Optional[str] = None
    ):
        """
        Log an audit event.
        
        Args:
            event_type: Type of event (e.g., 'rule_extracted', 'rule_validated')
            details: Event details
            user: User or system that triggered the event
        """
        event = {
            'timestamp': datetime.now().isoformat(),
            'event_type': event_type,
            'user': user or 'system',
            'details': details
        }
        
        with open(self.log_file, 'a', encoding='utf-8') as f:
            f.write(json.dumps(event, ensure_ascii=False) + '\n')
        
        logger.debug(f"Audit event logged: {event_type}")
    
    def get_audit_log(
        self,
        event_type: Optional[str] = None,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None
    ) -> List[Dict[str, Any]]:
        """
        Retrieve audit log entries.
        
        Args:
            event_type: Filter by event type
            start_date: Filter by start date
            end_date: Filter by end date
            
        Returns:
            List of audit log entries
        """
        if not self.log_file.exists():
            return []
        
        entries = []
        
        with open(self.log_file, 'r', encoding='utf-8') as f:
            for line in f:
                if line.strip():
                    entry = json.loads(line)
                    
                    # Apply filters
                    if event_type and entry['event_type'] != event_type:
                        continue
                    
                    entry_date = datetime.fromisoformat(entry['timestamp'])
                    
                    if start_date and entry_date < start_date:
                        continue
                    
                    if end_date and entry_date > end_date:
                        continue
                    
                    entries.append(entry)
        
        return entries
    
    def generate_audit_report(self) -> Dict[str, Any]:
        """Generate audit statistics report."""
        entries = self.get_audit_log()
        
        if not entries:
            return {
                'total_events': 0,
                'by_type': {},
                'by_user': {}
            }
        
        by_type = {}
        by_user = {}
        
        for entry in entries:
            event_type = entry['event_type']
            user = entry['user']
            
            by_type[event_type] = by_type.get(event_type, 0) + 1
            by_user[user] = by_user.get(user, 0) + 1
        
        return {
            'total_events': len(entries),
            'by_type': by_type,
            'by_user': by_user,
            'first_event': entries[0]['timestamp'] if entries else None,
            'last_event': entries[-1]['timestamp'] if entries else None
        }
