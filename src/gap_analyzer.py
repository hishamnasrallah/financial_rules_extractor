"""
Gap analysis engine for identifying missing or incomplete rule coverage.
"""
from typing import List, Dict, Any
from loguru import logger

from src.models import ExtractedRule, GapAnalysis
from src.tracks import TracksRepository, TrackRule


class GapAnalyzer:
    """Analyzes gaps between extracted rules and existing track rules."""
    
    def __init__(self):
        self.tracks = TracksRepository.get_all_tracks()
    
    def analyze_gaps(self, extracted_rules: List[ExtractedRule]) -> List[GapAnalysis]:
        """
        Identify gaps in rule coverage.
        
        Args:
            extracted_rules: Rules extracted from documents
            
        Returns:
            List of identified gaps
        """
        logger.info(f"Analyzing gaps for {len(extracted_rules)} extracted rules")
        
        gaps = []
        
        # Group extracted rules by track
        rules_by_track = self._group_rules_by_track(extracted_rules)
        
        # Analyze each track
        for track_id, track in self.tracks.items():
            track_extracted_rules = rules_by_track.get(track_id, [])
            
            logger.info(f"Analyzing track '{track.name_en}': {len(track_extracted_rules)} extracted rules")
            
            # Check each extracted rule against existing rules
            for extracted_rule in track_extracted_rules:
                gap = self._check_rule_coverage(extracted_rule, track)
                if gap:
                    gaps.append(gap)
        
        logger.info(f"Identified {len(gaps)} gaps")
        return gaps
    
    def _group_rules_by_track(
        self, 
        rules: List[ExtractedRule]
    ) -> Dict[str, List[ExtractedRule]]:
        """Group rules by their track ID."""
        
        grouped = {}
        
        for rule in rules:
            if rule.track_id:
                if rule.track_id not in grouped:
                    grouped[rule.track_id] = []
                grouped[rule.track_id].append(rule)
        
        return grouped
    
    def _check_rule_coverage(
        self, 
        extracted_rule: ExtractedRule,
        track
    ) -> GapAnalysis:
        """
        Check if an extracted rule is covered by existing rules.
        
        Returns:
            GapAnalysis object if gap exists, None otherwise
        """
        # Get existing rules for the track
        existing_rules = track.current_rules
        
        # Calculate similarity with each existing rule
        similarities = []
        for existing_rule in existing_rules:
            similarity = self._calculate_similarity(
                extracted_rule.text_ar,
                existing_rule.description
            )
            similarities.append((existing_rule.rule_id, similarity))
        
        # Sort by similarity
        similarities.sort(key=lambda x: x[1], reverse=True)
        
        # Determine gap type
        if not similarities:
            gap_type = "missing"
            severity = "high"
            recommendation = f"تنفيذ قاعدة جديدة: {extracted_rule.text_ar}"
        else:
            max_similarity = similarities[0][1]
            
            if max_similarity < 0.3:
                gap_type = "missing"
                severity = "high"
                recommendation = f"تنفيذ قاعدة جديدة: {extracted_rule.text_ar}"
            
            elif max_similarity < 0.7:
                gap_type = "partial"
                severity = "medium"
                similar_rule_id = similarities[0][0]
                recommendation = f"تحديث القاعدة {similar_rule_id} لتشمل: {extracted_rule.text_ar}"
            
            else:
                # High similarity - likely already covered
                return None
        
        # Create gap analysis
        gap = GapAnalysis(
            gap_id=f"gap_{extracted_rule.rule_id}",
            track_id=track.track_id,
            extracted_rule=extracted_rule,
            similar_existing_rules=[s[0] for s in similarities[:3]],
            gap_type=gap_type,
            severity=severity,
            recommendation=recommendation
        )
        
        return gap
    
    def _calculate_similarity(self, text1: str, text2: str) -> float:
        """
        Calculate similarity between two texts.
        Uses simple token-based similarity (can be improved with embeddings).
        
        Returns:
            Similarity score (0-1)
        """
        # Tokenize (simple word-based)
        tokens1 = set(text1.lower().split())
        tokens2 = set(text2.lower().split())
        
        if not tokens1 or not tokens2:
            return 0.0
        
        # Jaccard similarity
        intersection = tokens1.intersection(tokens2)
        union = tokens1.union(tokens2)
        
        similarity = len(intersection) / len(union) if union else 0.0
        
        return similarity
    
    def generate_gap_report(self, gaps: List[GapAnalysis]) -> Dict[str, Any]:
        """
        Generate a comprehensive gap analysis report.
        
        Args:
            gaps: List of identified gaps
            
        Returns:
            Gap report dictionary
        """
        # Group by track
        gaps_by_track = {}
        for gap in gaps:
            if gap.track_id not in gaps_by_track:
                gaps_by_track[gap.track_id] = []
            gaps_by_track[gap.track_id].append(gap)
        
        # Group by severity
        gaps_by_severity = {
            'critical': [],
            'high': [],
            'medium': [],
            'low': []
        }
        for gap in gaps:
            gaps_by_severity[gap.severity].append(gap)
        
        # Group by type
        gaps_by_type = {
            'missing': [],
            'partial': [],
            'conflicting': []
        }
        for gap in gaps:
            gaps_by_type[gap.gap_type].append(gap)
        
        report = {
            'summary': {
                'total_gaps': len(gaps),
                'by_severity': {k: len(v) for k, v in gaps_by_severity.items()},
                'by_type': {k: len(v) for k, v in gaps_by_type.items()},
                'by_track': {k: len(v) for k, v in gaps_by_track.items()}
            },
            'gaps_by_track': {
                track_id: [
                    {
                        'gap_id': gap.gap_id,
                        'extracted_rule': gap.extracted_rule.text_ar,
                        'gap_type': gap.gap_type,
                        'severity': gap.severity,
                        'recommendation': gap.recommendation,
                        'similar_existing_rules': gap.similar_existing_rules
                    }
                    for gap in track_gaps
                ]
                for track_id, track_gaps in gaps_by_track.items()
            },
            'critical_gaps': [
                {
                    'gap_id': gap.gap_id,
                    'track': gap.track_id,
                    'rule': gap.extracted_rule.text_ar,
                    'recommendation': gap.recommendation
                }
                for gap in gaps_by_severity['critical']
            ]
        }
        
        return report


class CoverageAnalyzer:
    """Analyzes overall rule coverage across tracks."""
    
    def __init__(self):
        self.tracks = TracksRepository.get_all_tracks()
    
    def analyze_coverage(
        self, 
        extracted_rules: List[ExtractedRule],
        gaps: List[GapAnalysis]
    ) -> Dict[str, Any]:
        """
        Analyze overall coverage of extracted rules.
        
        Args:
            extracted_rules: Extracted rules
            gaps: Identified gaps
            
        Returns:
            Coverage analysis report
        """
        logger.info("Analyzing coverage")
        
        # Group rules by track
        rules_by_track = {}
        for rule in extracted_rules:
            if rule.track_id:
                if rule.track_id not in rules_by_track:
                    rules_by_track[rule.track_id] = []
                rules_by_track[rule.track_id].append(rule)
        
        # Calculate coverage per track
        coverage_by_track = {}
        for track_id, track in self.tracks.items():
            existing_count = len(track.current_rules)
            extracted_count = len(rules_by_track.get(track_id, []))
            track_gaps = [g for g in gaps if g.track_id == track_id]
            gap_count = len(track_gaps)
            
            # Coverage percentage (simplified)
            # This is a rough estimate: existing rules / (existing + missing gaps)
            total_needed = existing_count + gap_count
            coverage_pct = (existing_count / total_needed * 100) if total_needed > 0 else 100.0
            
            coverage_by_track[track_id] = {
                'track_name': track.name_ar,
                'existing_rules': existing_count,
                'extracted_rules': extracted_count,
                'identified_gaps': gap_count,
                'coverage_percentage': round(coverage_pct, 2)
            }
        
        # Overall statistics
        total_existing = sum(len(t.current_rules) for t in self.tracks.values())
        total_extracted = len(extracted_rules)
        total_gaps = len(gaps)
        
        report = {
            'overall': {
                'total_existing_rules': total_existing,
                'total_extracted_rules': total_extracted,
                'total_gaps': total_gaps,
                'average_coverage': round(
                    sum(c['coverage_percentage'] for c in coverage_by_track.values()) / len(coverage_by_track),
                    2
                ) if coverage_by_track else 0.0
            },
            'by_track': coverage_by_track
        }
        
        return report
