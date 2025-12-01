"""Export functionality for debate sessions."""
import csv
import json
from pathlib import Path
from typing import Optional
from app.product_debate.models import DebateSession
import structlog

logger = structlog.get_logger(__name__)


class SessionExporter:
    """Exports debate session results."""
    
    def __init__(self, output_dir: str = "out"):
        """Initialize exporter.
        
        Args:
            output_dir: Output directory for exports
        """
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
    
    def export_session(
        self,
        session: DebateSession,
        session_storage_path: Path
    ) -> dict[str, Path]:
        """Export all session artifacts.
        
        Args:
            session: Debate session
            session_storage_path: Path to session storage directory
            
        Returns:
            Dictionary mapping export type to file path
        """
        exports = {}
        
        # Export taxonomy
        if session.taxonomy:
            taxonomy_path = self._export_taxonomy(session)
            exports["taxonomy"] = taxonomy_path
        
        # Export one-pager
        if session.final_concept:
            one_pager_path = self._export_one_pager(session)
            exports["one_pager"] = one_pager_path
        
        # Export BOM CSV
        if session.final_concept:
            bom_path = self._export_bom(session)
            exports["bom"] = bom_path
        
        # Export debate log
        debate_log_path = self._export_debate_log(session, session_storage_path)
        exports["debate_log"] = debate_log_path
        
        logger.info("Session exported", session_id=session.session_id, exports=list(exports.keys()))
        
        return exports
    
    def _export_taxonomy(self, session: DebateSession) -> Path:
        """Export taxonomy to taxonomy.txt.
        
        Args:
            session: Debate session
            
        Returns:
            Path to taxonomy file
        """
        taxonomy_path = self.output_dir / "taxonomy.txt"
        
        if not session.taxonomy:
            return taxonomy_path
        
        with open(taxonomy_path, "w") as f:
            # Write taxonomy structure in the required format
            for level, items in session.taxonomy.items():
                if items:
                    f.write(f"• {level}\n")
                    for item in items:
                        f.write(f"  • {item}\n")
        
        logger.info("Taxonomy exported", path=str(taxonomy_path))
        return taxonomy_path
    
    def _export_one_pager(self, session: DebateSession) -> Path:
        """Export concept one-pager to markdown.
        
        Args:
            session: Debate session
            
        Returns:
            Path to one-pager file
        """
        if not session.final_concept:
            return self.output_dir / "concept_onepager.md"
        
        one_pager_path = self.output_dir / "concept_onepager.md"
        
        concept = session.final_concept
        
        with open(one_pager_path, "w") as f:
            f.write(f"# {concept.name}\n\n")
            f.write(f"## User Story\n\n{concept.user_story}\n\n")
            f.write(f"## Top Features\n\n")
            for feature in concept.top_features:
                f.write(f"- {feature}\n")
            f.write(f"\n## Financials\n\n")
            f.write(f"- **Unit Cost**: ${concept.unit_cost:.2f}\n")
            f.write(f"- **Target MSRP**: ${concept.target_msrp:.2f}\n")
            f.write(f"- **Gross Margin**: {concept.gross_margin:.1f}%\n\n")
            f.write(f"## BOM (Bill of Materials)\n\n")
            for component, cost in concept.bom.items():
                f.write(f"- {component}: ${cost:.2f}\n")
            f.write(f"\n## Supply Notes\n\n{concept.supply_notes}\n\n")
            f.write(f"## Compliance Path\n\n{concept.compliance_path}\n\n")
            f.write(f"## Pilot Channel\n\n{concept.pilot_channel}\n\n")
            f.write(f"## First Run MOQs\n\n")
            for component, moq in concept.first_run_moqs.items():
                f.write(f"- {component}: {moq}\n")
            f.write(f"\n## Risks & Mitigations\n\n")
            for risk_data in concept.risks:
                f.write(f"### {risk_data.get('risk', 'Risk')}\n\n")
                f.write(f"{risk_data.get('mitigation', 'Mitigation')}\n\n")
        
        logger.info("One-pager exported", path=str(one_pager_path))
        return one_pager_path
    
    def _export_bom(self, session: DebateSession) -> Path:
        """Export BOM to CSV.
        
        Args:
            session: Debate session
            
        Returns:
            Path to BOM CSV file
        """
        bom_path = self.output_dir / "bom.csv"
        
        if not session.final_concept:
            return bom_path
        
        concept = session.final_concept
        
        with open(bom_path, "w", newline="") as f:
            writer = csv.writer(f)
            writer.writerow(["Component", "Unit Cost", "MOQ"])
            for component, cost in concept.bom.items():
                moq = concept.first_run_moqs.get(component, 0)
                writer.writerow([component, f"${cost:.2f}", moq])
        
        logger.info("BOM exported", path=str(bom_path))
        return bom_path
    
    def _export_debate_log(self, session: DebateSession, session_storage_path: Path) -> Path:
        """Export debate log JSON.
        
        Args:
            session: Debate session
            session_storage_path: Path to session storage directory
            
        Returns:
            Path to debate log file
        """
        debate_log_path = self.output_dir / "debate_log.json"
        
        # Copy session.json to debate_log.json
        session_file = session_storage_path / "session.json"
        if session_file.exists():
            import shutil
            shutil.copy(session_file, debate_log_path)
        
        logger.info("Debate log exported", path=str(debate_log_path))
        return debate_log_path


def export_conversation_text(session: DebateSession) -> str:
    """Export conversation as readable text.
    
    Args:
        session: Debate session
        
    Returns:
        Formatted conversation text
    """
    lines = []
    lines.append("=" * 80)
    lines.append(f"DEBATE SESSION: {session.session_id}")
    lines.append("=" * 80)
    lines.append(f"Core Market: {session.core_market}")
    lines.append(f"Category: {session.category}")
    lines.append(f"Rounds: {len(session.rounds)}/{session.max_rounds}")
    lines.append(f"Created: {session.created_at}")
    lines.append("")
    
    for round_data in session.rounds:
        lines.append("=" * 80)
        lines.append(f"ROUND {round_data.round_number}")
        lines.append("=" * 80)
        timestamp = round_data.timestamp
        if hasattr(timestamp, 'isoformat'):
            timestamp_str = timestamp.isoformat()
        else:
            timestamp_str = str(timestamp)
        lines.append(f"Timestamp: {timestamp_str}")
        lines.append("")
        
        # Agent A's message
        if round_data.agent_a_response:
            lines.append("🤖 AGENT A (Opportunity Seeker):")
            lines.append("-" * 80)
            lines.append(round_data.agent_a_response)
            lines.append("")
        
        # Agent B's message
        if round_data.agent_b_response:
            lines.append("🔍 AGENT B (Skeptical Builder):")
            lines.append("-" * 80)
            lines.append(round_data.agent_b_response)
            lines.append("")
        
        # Convergence summary
        if round_data.converged_proposals:
            lines.append("✅ CONVERGED PROPOSALS:")
            lines.append("-" * 80)
            for proposal in round_data.converged_proposals:
                score = proposal.composite_score if hasattr(proposal, 'composite_score') and proposal.composite_score else 0.0
                lines.append(f"  • {proposal.name} (Score: {score:.2f}/10)")
            lines.append("")
    
    # Final concept
    if session.final_concept:
        lines.append("=" * 80)
        lines.append("FINAL CONCEPT")
        lines.append("=" * 80)
        concept = session.final_concept
        lines.append(f"Name: {concept.name}")
        lines.append(f"User Story: {concept.user_story}")
        lines.append(f"Gross Margin: {concept.gross_margin:.1f}%")
        lines.append(f"Target MSRP: ${concept.target_msrp:.2f}")
        lines.append("")
    
    return "\n".join(lines)


def export_conversation_markdown(session: DebateSession) -> str:
    """Export conversation as Markdown.
    
    Args:
        session: Debate session
        
    Returns:
        Formatted conversation markdown
    """
    lines = []
    lines.append(f"# Debate Session: {session.session_id}")
    lines.append("")
    lines.append(f"- **Core Market:** {session.core_market}")
    lines.append(f"- **Category:** {session.category}")
    lines.append(f"- **Rounds:** {len(session.rounds)}/{session.max_rounds}")
    lines.append(f"- **Created:** {session.created_at}")
    lines.append("")
    
    for round_data in session.rounds:
        lines.append(f"## Round {round_data.round_number}")
        lines.append("")
        timestamp = round_data.timestamp
        if hasattr(timestamp, 'isoformat'):
            timestamp_str = timestamp.isoformat()
        else:
            timestamp_str = str(timestamp)
        lines.append(f"*Timestamp: {timestamp_str}*")
        lines.append("")
        
        # Agent A's message
        if round_data.agent_a_response:
            lines.append("### 🤖 Agent A (Opportunity Seeker)")
            lines.append("")
            # Format response with proper line breaks
            response = round_data.agent_a_response.replace('\n', '\n\n')
            lines.append(response)
            lines.append("")
        
        # Agent B's message
        if round_data.agent_b_response:
            lines.append("### 🔍 Agent B (Skeptical Builder)")
            lines.append("")
            # Format response with proper line breaks
            response = round_data.agent_b_response.replace('\n', '\n\n')
            lines.append(response)
            lines.append("")
        
        # Convergence summary
        if round_data.converged_proposals:
            lines.append("### ✅ Converged Proposals")
            lines.append("")
            for proposal in round_data.converged_proposals:
                score = proposal.composite_score if hasattr(proposal, 'composite_score') and proposal.composite_score else 0.0
                lines.append(f"- **{proposal.name}** (Score: {score:.2f}/10)")
            lines.append("")
    
    # Final concept
    if session.final_concept:
        lines.append("## Final Concept")
        lines.append("")
        concept = session.final_concept
        lines.append(f"**Name:** {concept.name}")
        lines.append("")
        lines.append(f"**User Story:** {concept.user_story}")
        lines.append("")
        lines.append(f"**Gross Margin:** {concept.gross_margin:.1f}%")
        lines.append(f"**Target MSRP:** ${concept.target_msrp:.2f}")
        lines.append("")
    
    return "\n".join(lines)

