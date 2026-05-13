"""
returnX AI — Job Advisor Agent
Analyses competing job requests from multiple gig platforms in real-time.
Uses distance, pay, fuel cost, traffic conditions, and time estimation
to recommend the most profitable job.
"""

import json
from datetime import datetime
from langchain_groq import ChatGroq
from agents.base_agent import BaseAgent


class JobAdvisorAgent(BaseAgent):
    """Agent that compares competing gig job offers and recommends the best one."""

    # Average fuel cost assumptions for gig riders in India
    FUEL_RATE_PER_KM = 3.5   # Rs per km (approx for a 2-wheeler ~45 km/l, Rs 105/l)
    BASE_SPEED_KMPH = 25     # Base city riding speed in km/h (no traffic)

    # Bangalore traffic patterns by zone
    ZONE_TRAFFIC = {
        "koramangala": {"base": 1.4, "peak_mult": 1.8},
        "btm": {"base": 1.3, "peak_mult": 1.6},
        "hsr": {"base": 1.2, "peak_mult": 1.5},
        "indiranagar": {"base": 1.5, "peak_mult": 2.0},
        "whitefield": {"base": 1.6, "peak_mult": 2.2},
        "electronic city": {"base": 1.3, "peak_mult": 1.9},
        "marathahalli": {"base": 1.5, "peak_mult": 2.1},
        "mg road": {"base": 1.6, "peak_mult": 2.0},
        "jp nagar": {"base": 1.2, "peak_mult": 1.5},
        "jayanagar": {"base": 1.3, "peak_mult": 1.6},
        "silk board": {"base": 1.9, "peak_mult": 2.5},
        "hebbal": {"base": 1.4, "peak_mult": 1.8},
        "default": {"base": 1.3, "peak_mult": 1.6},
    }

    def __init__(self, llm: ChatGroq = None):
        super().__init__(
            name="JobAdvisorAgent",
            role="Real-Time Job Comparison & Suggestion Engine",
            llm=llm,
        )

    def get_system_prompt(self) -> str:
        return """You are a real-time job advisor for Indian gig workers (delivery riders).

TASK: A rider has received multiple job requests simultaneously from different platforms.
Analyse each job and recommend which one is the MOST PROFITABLE in real-time.

FACTORS TO CONSIDER:
1. PAY: The amount offered for the delivery
2. DISTANCE: Total km to be covered (pickup + delivery)
3. TRAFFIC: Current traffic congestion level and its impact on delivery time
4. EFFECTIVE HOURLY RATE: Pay / estimated time (adjusted for traffic)
5. FUEL COST: Approximate fuel expense for the distance
6. NET PROFIT: Pay minus fuel cost
7. PROFIT PER KM: Net profit / distance
8. TIME EFFICIENCY: Money earned per minute (traffic-adjusted)
9. PLATFORM RELIABILITY: Surge pricing, tip likelihood, bonus potential
10. RISK FACTORS: Traffic zones, weather conditions, peak hours

OUTPUT FORMAT - Return ONLY this JSON:
{
  "agent": "JobAdvisorAgent",
  "recommendation": {
    "best_job_index": <0-based index of the best job>,
    "best_platform": "<platform name>",
    "confidence": <0-100>,
    "reason_short": "<1-line reason>",
    "reason_detailed": "<2-3 sentence detailed explanation including traffic impact>"
  },
  "analysis": [
    {
      "platform": "<name>",
      "pay": <number>,
      "distance_km": <number>,
      "estimated_time_mins": <number>,
      "fuel_cost": <number>,
      "net_profit": <number>,
      "effective_hourly_rate": <number>,
      "profit_per_km": <number>,
      "traffic_level": "<Low|Medium|High|Very High>",
      "traffic_delay_mins": <number>,
      "score": <0-100 overall score>,
      "pros": ["..."],
      "cons": ["..."]
    }
  ],
  "tip": "<Quick actionable tip for the rider>"
}

RULES:
- Always calculate net profit = pay - fuel cost
- Factor traffic heavily into time estimates and hourly rate
- Shorter distances with low traffic are usually better
- A high-pay job in heavy traffic may be WORSE than low-pay with no traffic
- Be decisive - always pick one winner clearly"""

    def _get_traffic_factor(self, job: dict) -> dict:
        """Estimate traffic conditions based on time-of-day and delivery zone."""
        now = datetime.now()
        hour = now.hour

        # Determine peak hours
        is_morning_peak = 8 <= hour <= 10
        is_lunch_peak = 12 <= hour <= 14
        is_evening_peak = 17 <= hour <= 20
        is_peak = is_morning_peak or is_lunch_peak or is_evening_peak
        is_night = hour >= 22 or hour <= 6

        # Try to detect zone from items/platform text
        items_text = str(job.get("items", "")).lower()
        platform = str(job.get("platform", "")).lower()
        full_text = f"{items_text} {platform}"

        zone_key = "default"
        for zone in self.ZONE_TRAFFIC:
            if zone in full_text:
                zone_key = zone
                break

        zone_data = self.ZONE_TRAFFIC[zone_key]

        # Calculate traffic multiplier
        if is_night:
            traffic_mult = 1.0  # No traffic at night
            level = "Low"
            congestion_pct = 15
        elif is_peak:
            traffic_mult = zone_data["peak_mult"]
            if traffic_mult >= 2.0:
                level = "Very High"
            elif traffic_mult >= 1.6:
                level = "High"
            else:
                level = "Medium"
            congestion_pct = min(95, int(traffic_mult * 40))
        else:
            traffic_mult = zone_data["base"]
            if traffic_mult >= 1.5:
                level = "Medium"
            else:
                level = "Low"
            congestion_pct = min(70, int(traffic_mult * 30))

        # Time period label
        if is_morning_peak:
            period = "Morning Rush"
        elif is_lunch_peak:
            period = "Lunch Hour"
        elif is_evening_peak:
            period = "Evening Rush"
        elif is_night:
            period = "Night (Clear Roads)"
        else:
            period = "Off-Peak"

        return {
            "traffic_multiplier": traffic_mult,
            "traffic_level": level,
            "congestion_pct": congestion_pct,
            "zone": zone_key.title(),
            "period": period,
            "is_peak": is_peak,
        }

    def _calculate_metrics(self, job: dict) -> dict:
        """Calculate profitability metrics including traffic impact."""
        pay = float(job.get("pay", 0))
        distance = float(job.get("distance_km", 0))

        # Traffic analysis
        traffic = self._get_traffic_factor(job)
        traffic_mult = traffic["traffic_multiplier"]

        # Fuel cost estimation (traffic increases fuel consumption ~10-20%)
        fuel_mult = 1 + (traffic_mult - 1) * 0.3  # Partial fuel increase from stop-go
        fuel_cost = round(distance * self.FUEL_RATE_PER_KM * fuel_mult, 2)

        # Time estimation (traffic-adjusted)
        effective_speed = self.BASE_SPEED_KMPH / traffic_mult
        base_time = (distance / self.BASE_SPEED_KMPH) * 60 if distance > 0 else 5
        actual_time = round((distance / effective_speed) * 60, 1) if distance > 0 else 5
        traffic_delay = round(actual_time - base_time, 1)

        # Net profit
        net_profit = round(pay - fuel_cost, 2)

        # Effective hourly rate (traffic-adjusted)
        hourly_rate = round((net_profit / actual_time) * 60, 2) if actual_time > 0 else 0

        # Profit per km
        profit_per_km = round(net_profit / distance, 2) if distance > 0 else 0

        return {
            "fuel_cost": fuel_cost,
            "estimated_time_mins": actual_time,
            "net_profit": net_profit,
            "effective_hourly_rate": hourly_rate,
            "profit_per_km": profit_per_km,
            "traffic_level": traffic["traffic_level"],
            "traffic_delay_mins": max(0, traffic_delay),
            "congestion_pct": traffic["congestion_pct"],
            "traffic_zone": traffic["zone"],
            "traffic_period": traffic["period"],
        }

    def run(self, input_data: dict) -> dict:
        """Compare multiple job offers and recommend the best one."""
        jobs = input_data.get("jobs", [])

        if len(jobs) < 2:
            return {"agent": self.name, "error": "Need at least 2 job offers to compare"}

        # ReAct: Think
        self.think(f"Received {len(jobs)} competing job offers to compare")

        # Pre-calculate metrics for each job
        enriched_jobs = []
        for i, job in enumerate(jobs):
            metrics = self._calculate_metrics(job)
            enriched = {**job, **metrics}
            enriched_jobs.append(enriched)
            self.think(
                f"Job {i+1} ({job.get('platform', 'Unknown')}): "
                f"Pay Rs{job.get('pay', 0)}, {job.get('distance_km', 0)} km, "
                f"Traffic: {metrics['traffic_level']}, "
                f"Net Rs{metrics['net_profit']}, Rs{metrics['effective_hourly_rate']}/hr"
            )

        # Build context for LLM
        now = datetime.now()
        context = f"""COMPETING JOB OFFERS FOR THE RIDER:
Current Time: {now.strftime('%I:%M %p')} ({enriched_jobs[0].get('traffic_period', 'N/A')})

"""
        for i, job in enumerate(enriched_jobs):
            context += f"""JOB {i+1}:
- Platform: {job.get('platform', 'Unknown')}
- Pay Offered: Rs {job.get('pay', 0)}
- Distance: {job.get('distance_km', 0)} km
- Items/Type: {job.get('items', 'Delivery')}
- TRAFFIC: {job['traffic_level']} ({job.get('traffic_zone', 'City')} zone)
- Traffic Delay: +{job['traffic_delay_mins']} mins added
- Estimated Fuel Cost: Rs {job['fuel_cost']}
- Net Profit: Rs {job['net_profit']}
- Estimated Time (with traffic): {job['estimated_time_mins']} mins
- Effective Hourly Rate: Rs {job['effective_hourly_rate']}/hr
- Profit per KM: Rs {job['profit_per_km']}/km

"""

        context += """Analyse all factors INCLUDING TRAFFIC CONDITIONS and recommend which job 
the rider should accept RIGHT NOW. Heavy traffic significantly reduces effective hourly earnings.
Be decisive and give a clear winner with score out of 100 for each job."""

        # ReAct: Act - Call LLM
        result = self.call_llm(context)

        # Enrich result with our pre-calculated metrics
        if "analysis" in result:
            for i, analysis in enumerate(result["analysis"]):
                if i < len(enriched_jobs):
                    analysis["fuel_cost"] = enriched_jobs[i]["fuel_cost"]
                    analysis["net_profit"] = enriched_jobs[i]["net_profit"]
                    analysis["effective_hourly_rate"] = enriched_jobs[i]["effective_hourly_rate"]
                    analysis["profit_per_km"] = enriched_jobs[i]["profit_per_km"]
                    analysis["traffic_level"] = enriched_jobs[i]["traffic_level"]
                    analysis["traffic_delay_mins"] = enriched_jobs[i]["traffic_delay_mins"]
                    analysis["congestion_pct"] = enriched_jobs[i].get("congestion_pct", 0)

        # Add traffic summary to result
        result["traffic_info"] = {
            "time": now.strftime("%I:%M %p"),
            "period": enriched_jobs[0].get("traffic_period", "N/A"),
            "zones": [
                {"name": j.get("traffic_zone", "City"), "level": j["traffic_level"], "congestion": j.get("congestion_pct", 0)}
                for j in enriched_jobs
            ]
        }

        self.observe(f"Recommendation: {result.get('recommendation', {}).get('best_platform', 'N/A')}")

        return result
