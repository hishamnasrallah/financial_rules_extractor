"""
Dynamic track management API for Financial Rules Extraction Agent.
Allows runtime updates to track definitions and rules.
"""
import json
import os
from datetime import datetime
from typing import List, Dict, Optional, Any
from pathlib import Path
from loguru import logger

from src.tracks import FinancialTrack, TrackRule, TracksRepository
from src.config import config


class TracksAPI:
    """API for managing financial tracks dynamically."""
    
    def __init__(self, storage_path: str = None):
        """
        Initialize tracks API.
        
        Args:
            storage_path: Path to tracks storage file (defaults to data/tracks.json)
        """
        self.storage_path = storage_path or str(config.app.data_dir / "tracks.json")
        self.tracks_repository = TracksRepository()
        self.version = "1.0.0"
        
        # Load custom tracks if file exists
        self._load_custom_tracks()
    
    def _load_custom_tracks(self):
        """Load custom tracks from storage."""
        if os.path.exists(self.storage_path):
            try:
                with open(self.storage_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                logger.info(f"Loaded custom tracks from {self.storage_path}")
                # Here you would merge with default tracks
            except Exception as e:
                logger.error(f"Failed to load custom tracks: {e}")
    
    def _save_tracks(self, tracks_data: Dict):
        """Save tracks to storage."""
        try:
            # Ensure directory exists
            Path(self.storage_path).parent.mkdir(parents=True, exist_ok=True)
            
            with open(self.storage_path, 'w', encoding='utf-8') as f:
                json.dump(tracks_data, f, ensure_ascii=False, indent=2)
            
            logger.info(f"Saved tracks to {self.storage_path}")
        except Exception as e:
            logger.error(f"Failed to save tracks: {e}")
            raise
    
    def get_all_tracks(self) -> List[FinancialTrack]:
        """
        Get all financial tracks.
        
        Returns:
            List of all tracks
        """
        return list(self.tracks_repository.get_all_tracks().values())
    
    def get_track(self, track_id: str) -> Optional[FinancialTrack]:
        """
        Get a specific track by ID.
        
        Args:
            track_id: Track identifier
            
        Returns:
            Track if found, None otherwise
        """
        return self.tracks_repository.get_track(track_id)
    
    def add_track_rule(
        self, 
        track_id: str, 
        rule_text_ar: str,
        rule_text_en: str = None
    ) -> bool:
        """
        Add a new rule to a track.
        
        Args:
            track_id: Track identifier
            rule_text_ar: Rule text in Arabic
            rule_text_en: Rule text in English (optional)
            
        Returns:
            True if successful, False otherwise
        """
        try:
            track = self.get_track(track_id)
            if not track:
                logger.error(f"Track not found: {track_id}")
                return False
            
            # Create new rule
            new_rule = TrackRule(
                rule_id=f"{track_id}_rule_{len(track.current_rules) + 1}",
                description=rule_text_ar,
                source="Dynamic"
            )
            
            # Add to track
            track.current_rules.append(new_rule)
            
            # Save to storage
            self._save_track_update(track)
            
            logger.info(f"Added rule to track {track_id}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to add rule to track: {e}")
            return False
    
    def update_track_rule(
        self,
        track_id: str,
        rule_id: str,
        new_text_ar: str,
        new_text_en: str = None
    ) -> bool:
        """
        Update an existing rule in a track.
        
        Args:
            track_id: Track identifier
            rule_id: Rule identifier
            new_text_ar: New rule text in Arabic
            new_text_en: New rule text in English (optional)
            
        Returns:
            True if successful, False otherwise
        """
        try:
            track = self.get_track(track_id)
            if not track:
                logger.error(f"Track not found: {track_id}")
                return False
            
            # Find and update rule
            for rule in track.current_rules:
                if rule.rule_id == rule_id:
                    rule.description = new_text_ar
                    
                    # Save to storage
                    self._save_track_update(track)
                    
                    logger.info(f"Updated rule {rule_id} in track {track_id}")
                    return True
            
            logger.error(f"Rule not found: {rule_id}")
            return False
            
        except Exception as e:
            logger.error(f"Failed to update rule: {e}")
            return False
    
    def remove_track_rule(self, track_id: str, rule_id: str) -> bool:
        """
        Remove a rule from a track.
        
        Args:
            track_id: Track identifier
            rule_id: Rule identifier
            
        Returns:
            True if successful, False otherwise
        """
        try:
            track = self.get_track(track_id)
            if not track:
                logger.error(f"Track not found: {track_id}")
                return False
            
            # Find and remove rule
            original_count = len(track.current_rules)
            track.current_rules = [r for r in track.current_rules if r.rule_id != rule_id]
            
            if len(track.current_rules) == original_count:
                logger.error(f"Rule not found: {rule_id}")
                return False
            
            # Save to storage
            self._save_track_update(track)
            
            logger.info(f"Removed rule {rule_id} from track {track_id}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to remove rule: {e}")
            return False
    
    def _save_track_update(self, track: FinancialTrack):
        """Save track update to storage."""
        try:
            # Load existing data
            tracks_data = {}
            if os.path.exists(self.storage_path):
                with open(self.storage_path, 'r', encoding='utf-8') as f:
                    tracks_data = json.load(f)
            
            # Update track data
            tracks_data[track.track_id] = {
                "name_ar": track.name_ar,
                "name_en": track.name_en,
                "definition_ar": track.definition_ar,
                "definition_en": track.definition_en,
                "rules": [
                    {
                        "rule_id": rule.rule_id,
                        "description": rule.description,
                        "source": rule.source
                    }
                    for rule in track.current_rules
                ],
                "version": self.version,
                "last_updated": datetime.utcnow().isoformat()
            }
            
            # Save
            self._save_tracks(tracks_data)
            
        except Exception as e:
            logger.error(f"Failed to save track update: {e}")
            raise
    
    def get_track_history(self, track_id: str) -> List[Dict]:
        """
        Get modification history for a track.
        
        Args:
            track_id: Track identifier
            
        Returns:
            List of track versions/modifications
        """
        # This would require a history storage mechanism
        # For now, return basic info
        track = self.get_track(track_id)
        if not track:
            return []
        
        return [
            {
                "version": self.version,
                "num_rules": len(track.current_rules),
                "last_updated": datetime.utcnow().isoformat()
            }
        ]
    
    def export_tracks(self, export_path: str = None) -> str:
        """
        Export all tracks to a JSON file.
        
        Args:
            export_path: Path to export file (optional)
            
        Returns:
            Path to exported file
        """
        if not export_path:
            export_path = str(config.app.output_dir / f"tracks_export_{int(datetime.now().timestamp())}.json")
        
        try:
            all_tracks = self.get_all_tracks()
            
            export_data = {
                "version": self.version,
                "exported_at": datetime.utcnow().isoformat(),
                "tracks": {
                    track.track_id: {
                        "name_ar": track.name_ar,
                        "name_en": track.name_en,
                        "definition_ar": track.definition_ar,
                        "definition_en": track.definition_en,
                        "rules": [
                            {
                                "rule_id": rule.rule_id,
                                "description": rule.description,
                                "source": rule.source
                            }
                            for rule in track.current_rules
                        ]
                    }
                    for track in all_tracks
                }
            }
            
            # Ensure directory exists
            Path(export_path).parent.mkdir(parents=True, exist_ok=True)
            
            with open(export_path, 'w', encoding='utf-8') as f:
                json.dump(export_data, f, ensure_ascii=False, indent=2)
            
            logger.info(f"Exported tracks to {export_path}")
            return export_path
            
        except Exception as e:
            logger.error(f"Failed to export tracks: {e}")
            raise
    
    def import_tracks(self, import_path: str) -> bool:
        """
        Import tracks from a JSON file.
        
        Args:
            import_path: Path to import file
            
        Returns:
            True if successful, False otherwise
        """
        try:
            with open(import_path, 'r', encoding='utf-8') as f:
                import_data = json.load(f)
            
            # Validate format
            if "tracks" not in import_data:
                logger.error("Invalid import file format")
                return False
            
            # Save to storage
            self._save_tracks(import_data["tracks"])
            
            # Reload
            self._load_custom_tracks()
            
            logger.info(f"Imported tracks from {import_path}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to import tracks: {e}")
            return False
    
    def get_statistics(self) -> Dict[str, Any]:
        """
        Get statistics about tracks.
        
        Returns:
            Dictionary with track statistics
        """
        all_tracks = self.get_all_tracks()
        
        return {
            "total_tracks": len(all_tracks),
            "total_rules": sum(len(track.current_rules) for track in all_tracks),
            "tracks_by_id": {
                track.track_id: {
                    "name": track.name_ar,
                    "num_rules": len(track.current_rules)
                }
                for track in all_tracks
            },
            "version": self.version
        }
