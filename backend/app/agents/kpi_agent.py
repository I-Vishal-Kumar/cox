"""KPI Monitoring and Root Cause Analysis Agent."""

from typing import Dict, Any, List, Optional
from langchain_core.prompts import ChatPromptTemplate
from app.agents.base_agent import BaseAgent
from datetime import datetime


class KPIAgent(BaseAgent):
    """Agent for KPI monitoring, anomaly detection, and root cause analysis."""

    def get_system_prompt(self) -> str:
        return """You are an expert automotive industry analyst specializing in KPI monitoring and root cause analysis.

Your role is to:
1. Analyze KPI data and identify anomalies
2. Provide clear, actionable root cause analysis
3. Generate recommendations based on data patterns
4. Explain complex data insights in plain language

When analyzing data:
- Compare current vs previous periods
- Break down by dealer, region, product, or time
- Identify the main drivers of change
- Quantify impacts with specific numbers
- Provide specific, actionable recommendations

Format your responses with:
- A brief summary of the finding
- Bullet points for key data points
- Clear attribution of causes
- Actionable recommendations

Be specific with numbers and percentages. Always include context."""

    async def process(self, query: str, context: Dict[str, Any] = None) -> Dict[str, Any]:
        """Analyze KPIs and provide insights."""
        data = context.get("data", []) if context else []
        query_type = context.get("query_type", "general") if context else "general"

        prompt = ChatPromptTemplate.from_messages([
            ("system", self.get_system_prompt()),
            ("human", """Analyze this data and provide insights:

Question: {query}

Query Type: {query_type}

Data:
{data}

Provide a comprehensive analysis with:
1. Summary of the situation
2. Key findings with specific numbers
3. Root cause analysis
4. Actionable recommendations

Analysis:""")
        ])

        analysis = await self.generate_response(
            prompt,
            query=query,
            query_type=query_type,
            data=self._format_data(data)
        )

        # Extract recommendations from analysis
        recommendations = self._extract_recommendations(analysis)

        return {
            "analysis": analysis,
            "recommendations": recommendations,
            "timestamp": datetime.now().isoformat()
        }

    def _format_data(self, data: List[Dict]) -> str:
        """Format data for the prompt."""
        if not data:
            return "No data available"

        # Format as a readable table
        if len(data) == 0:
            return "Empty dataset"

        headers = list(data[0].keys())
        lines = [" | ".join(headers)]
        lines.append("-" * len(lines[0]))

        for row in data[:20]:  # Limit to 20 rows
            lines.append(" | ".join(str(row.get(h, "")) for h in headers))

        return "\n".join(lines)

    def _extract_recommendations(self, analysis: str) -> List[str]:
        """Extract recommendations from the analysis text."""
        recommendations = []
        lines = analysis.split("\n")

        in_recommendations = False
        for line in lines:
            line = line.strip()
            if "recommendation" in line.lower():
                in_recommendations = True
                continue

            if in_recommendations and line.startswith(("-", "•", "*", "1", "2", "3")):
                # Clean up the line
                rec = line.lstrip("-•* 0123456789.)")
                if rec and len(rec) > 10:
                    recommendations.append(rec.strip())

        return recommendations[:5]  # Return top 5 recommendations


class RootCauseAnalyzer:
    """Specialized analyzer for root cause analysis."""

    def __init__(self, kpi_agent: KPIAgent):
        self.kpi_agent = kpi_agent

    async def analyze_fni_drop(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze F&I revenue drop scenario."""
        context = {
            "data": data.get("comparison_data", []),
            "query_type": "fni_revenue_analysis"
        }

        # Add specific F&I context
        prompt_additions = """
        Focus on:
        - Service contract penetration rates
        - Gap insurance attachment
        - Finance manager performance
        - Regional patterns
        - Week-over-week changes
        """

        return await self.kpi_agent.process(
            "Why did F&I revenue drop? Identify the main drivers and affected dealers.",
            context
        )

    async def analyze_logistics_delays(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze logistics delay scenario."""
        context = {
            "data": data.get("delay_data", []),
            "query_type": "logistics_delay_analysis"
        }

        return await self.kpi_agent.process(
            "Who delayed — carrier, route, or weather? Analyze the shipment delays.",
            context
        )

    async def analyze_plant_downtime(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze plant downtime scenario."""
        context = {
            "data": data.get("downtime_data", []),
            "query_type": "plant_downtime_analysis"
        }

        return await self.kpi_agent.process(
            "Which plants showed downtime and why? Provide root cause analysis.",
            context
        )


# Pre-built analysis templates for demo scenarios
DEMO_ANALYSIS_TEMPLATES = {
    "fni_midwest": """F&I revenue in the Midwest region declined {change_pct}% vs last week.

• {pct_from_top_dealers}% of the decline came from three dealers: {top_dealers}.
• The main driver was lower service contract penetration (down from {prev_penetration}% to {curr_penetration}%), not unit volume.
• Finance manager {problem_manager} at {problem_dealer} accounted for a {manager_drop}-point drop in attachment rate.

**Recommendation:** Focus coaching on service contract sales at these three dealers and review any recent promo or pricing changes.""",

    "logistics_delays": """Over the past 7 days, {delay_rate}% of shipments arrived late.

• {carrier_pct}% of delays are concentrated on {problem_carrier} on two routes: {problem_routes}.
• Weather was a minor factor (only {weather_count} delays tagged to storms).
• Average dwell time at the origin yard for {problem_carrier} increased from {prev_dwell} to {curr_dwell} hours.

**Recommendation:** Escalate with {problem_carrier} on those two routes and re-route high-priority shipments to {alt_carrier} where capacity is available.""",

    "plant_downtime": """Three plants recorded significant downtime this week:

**{plant_a}** — {plant_a_hours} hours of downtime, mostly on {plant_a_line}. Root causes: {plant_a_cause1} ({plant_a_cause1_hours}h) and {plant_a_cause2} ({plant_a_cause2_hours}h).

**{plant_b}** — {plant_b_hours} hours, primarily due to {plant_b_cause} from {plant_b_supplier}.

**{plant_c}** — {plant_c_hours} hours from {plant_c_cause}.

**Recommendations:**
• {plant_a}: fast-track root cause on {plant_a_issue}; defect rate is {defect_rate}x normal.
• {plant_b}: review purchase order lead times and safety stock for components from {plant_b_supplier}."""
}
