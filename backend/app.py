"""
returnX AI — Flask Backend Server
API endpoints for the agentic pipeline.

Endpoints:
    POST /api/analyse             - Run the full agentic pipeline
    POST /api/parse-notifications - Parse notification text into job offers
    POST /api/compare-jobs        - Real-time job comparison & suggestion
    GET  /api/state               - Get accumulated state
    POST /api/clear               - Clear all data
    GET  /api/health              - Health check
"""

from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
import os
import sys
import time
import json as json_lib
import re

# Add backend to path
sys.path.insert(0, os.path.dirname(__file__))

from agents.orchestrator import AgentOrchestrator
from agents.job_advisor import JobAdvisorAgent
from memory.state import AgentMemory
from langchain_groq import ChatGroq
from langchain_core.messages import SystemMessage, HumanMessage

app = Flask(__name__, static_folder="../", static_url_path="")
CORS(app)

# Persistent memory
memory = AgentMemory()


@app.route("/")
def index():
    """Serve the frontend."""
    return send_from_directory("../", "index.html")


@app.route("/<path:path>")
def static_files(path):
    """Serve static files (CSS, JS)."""
    return send_from_directory("../", path)


@app.route("/api/health", methods=["GET"])
def health():
    """Health check endpoint."""
    return jsonify({
        "status": "ok",
        "service": "returnX AI",
        "agents": ["SmsParserAgent", "TaxAdvisorAgent", "InsightsAgent", "JobAdvisorAgent"],
        "sessions": memory.state.get("session_count", 0),
    })


@app.route("/api/analyse", methods=["POST"])
def analyse():
    """Run the full agentic pipeline."""
    data = request.get_json()

    api_key = data.get("api_key", "").strip()
    sms_text = data.get("sms_text", "").strip()

    if not api_key:
        return jsonify({"error": "API key is required"}), 400
    if not sms_text:
        return jsonify({"error": "SMS text is required"}), 400

    try:
        accumulated = memory.get_accumulated()
        orchestrator = AgentOrchestrator(api_key=api_key)
        result = orchestrator.run(sms_text=sms_text, accumulated=accumulated)
        memory.add_results(result)
        return jsonify(result)

    except Exception as e:
        print(f"[ERROR] Pipeline failed: {e}")
        return jsonify({"error": str(e)}), 500


@app.route("/api/parse-notifications", methods=["POST"])
def parse_notifications():
    """
    Parse raw notification text into structured job offers using LLM.
    The rider pastes notification text, and AI extracts platform, pay, distance, etc.
    """
    data = request.get_json()
    api_key = data.get("api_key", "").strip()
    notif_text = data.get("notification_text", "").strip()

    if not api_key:
        return jsonify({"error": "API key is required"}), 400
    if not notif_text:
        return jsonify({"error": "Notification text is required"}), 400

    try:
        llm = ChatGroq(
            api_key=api_key,
            model="llama-3.3-70b-versatile",
            temperature=0,
            max_tokens=2048,
        )

        system_prompt = """You are a notification parser for Indian gig delivery apps.

TASK: Extract structured job offers from raw push notification text.
The notifications come from apps like Swiggy, Zomato, Zepto, Blinkit, Dunzo, Rapido, Uber, Ola, BigBasket, Porter, etc.

For EACH job notification found, extract:
1. platform: The app name (Swiggy, Zomato, Zepto, etc.)
2. pay: The payment amount in INR (number only)
3. distance_km: Distance in km (number only)
4. items: Type of delivery (Food delivery, Grocery delivery, Ride, Parcel, etc.)

IMPORTANT:
- If distance is not mentioned, estimate based on typical delivery distances (1-8 km)
- If pay is not mentioned, estimate based on platform averages (30-80)
- Extract ALL job offers found in the text
- Return at least 2 jobs if the text mentions multiple platforms

OUTPUT FORMAT - Return ONLY this JSON:
{
  "jobs": [
    {"platform": "...", "pay": <number>, "distance_km": <number>, "items": "..."}
  ]
}"""

        messages = [
            SystemMessage(content=system_prompt),
            HumanMessage(content=notif_text),
        ]

        response = llm.invoke(messages, response_format={"type": "json_object"})
        raw = response.content

        try:
            parsed = json_lib.loads(raw)
        except Exception:
            match = re.search(r"\{[\s\S]*\}", raw)
            parsed = json_lib.loads(match.group()) if match else {"jobs": []}

        jobs = parsed.get("jobs", [])
        print(f"[NotifParser] Extracted {len(jobs)} jobs from notifications")

        return jsonify({"jobs": jobs})

    except Exception as e:
        print(f"[ERROR] Notification parsing failed: {e}")
        return jsonify({"error": str(e)}), 500


@app.route("/api/compare-jobs", methods=["POST"])
def compare_jobs():
    """Real-time job comparison endpoint."""
    data = request.get_json()

    api_key = data.get("api_key", "").strip()
    jobs = data.get("jobs", [])

    if not api_key:
        return jsonify({"error": "API key is required"}), 400
    if len(jobs) < 2:
        return jsonify({"error": "At least 2 job offers are required for comparison"}), 400

    try:
        start = time.time()

        llm = ChatGroq(
            api_key=api_key,
            model="llama-3.3-70b-versatile",
            temperature=0,
            max_tokens=2048,
        )

        advisor = JobAdvisorAgent(llm=llm)
        result = advisor.run({"jobs": jobs})

        elapsed = round(time.time() - start, 1)

        print(f"\n[JobAdvisor] Compared {len(jobs)} jobs in {elapsed}s")
        print(f"[JobAdvisor] Winner: {result.get('recommendation', {}).get('best_platform', 'N/A')}")

        result["duration"] = elapsed
        return jsonify(result)

    except Exception as e:
        print(f"[ERROR] Job comparison failed: {e}")
        return jsonify({"error": str(e)}), 500


@app.route("/api/state", methods=["GET"])
def get_state():
    """Return the full accumulated state."""
    return jsonify(memory.get_full_state())


@app.route("/api/clear", methods=["POST"])
def clear_state():
    """Clear all accumulated data."""
    memory.clear()
    return jsonify({"status": "cleared"})


if __name__ == "__main__":
    print("\n" + "=" * 60)
    print("  returnX AI — Agentic Backend Server")
    print("  Agents: SmsParser | TaxAdvisor | Insights | JobAdvisor")
    print("  Server: http://localhost:5000")
    print("=" * 60 + "\n")
    app.run(debug=True, port=5000)
