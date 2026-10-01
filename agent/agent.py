"""
Local2Farm AI Agent
Coordinates data collection, tool execution, decision support reasoning,
and farmer-friendly explanations.
"""

import os
import json
import requests
from config import Config
from agent.tools import (
    search_buyers,
    search_markets,
    get_crop_price,
    calculate_transport_cost,
    estimate_waste_risk,
    calculate_net_amount,
    compare_selling_options
)

class Local2FarmAgent:
    """
    Decision Support AI Agent for Farmers.
    Assists farmers by evaluating buyers and markets, calculating transport
    and waste risks, and explaining trade-offs.
    """

    def __init__(self, demo_mode=None, api_key=None, model=None):
        self.demo_mode = Config.DEMO_MODE if demo_mode is None else demo_mode
        self.api_key = Config.LLM_API_KEY if api_key is None else api_key
        self.model = Config.LLM_MODEL if model is None else model

    def analyze(self, crop_name, location, quantity, harvest_date, selling_date, storage_available=False, max_distance=100.0):
        """
        Executes the AI Agent workflow:
        1. Tool execution to gather buyers, markets, prices, freight & waste risks.
        2. Financial & logistics comparison of all viable options.
        3. Explainable recommendation generation (via LLM API or smart rule engine).
        """
        trace = []

        # Tool 1 & 2: Search Buyers and Markets
        trace.append({
            'step': 'Search Buyers & Markets',
            'action': 'search_buyers & search_markets',
            'details': f"Searching verified buyers and markets accepting '{crop_name}' near '{location}' for {quantity} kg."
        })

        # Tool 7: Compare selling options (coordinates tools 3, 4, 5, 6)
        options = compare_selling_options(
            crop_name=crop_name,
            location=location,
            quantity=quantity,
            harvest_date=harvest_date,
            selling_date=selling_date,
            storage_available=storage_available,
            max_distance=max_distance
        )

        trace.append({
            'step': 'Cost & Risk Calculation',
            'action': 'calculate_transport_cost & estimate_waste_risk',
            'details': f"Calculated road freight costs and perishability waste risks for {len(options)} potential destination(s)."
        })

        trace.append({
            'step': 'Financial Net Evaluation',
            'action': 'calculate_net_amount & compare_selling_options',
            'details': f"Ranked options based on estimated net returns after transportation costs."
        })

        if not options:
            return {
                'options': [],
                'best_option': None,
                'explanation': f"No buyers or markets currently found for {crop_name} within {max_distance} km. Consider expanding the search distance.",
                'why_this_option': {},
                'trace': trace
            }

        best_option = options[0]

        # Generate Explanation
        explanation = None
        if not self.demo_mode and self.api_key:
            explanation = self._generate_llm_explanation(
                crop_name, location, quantity, harvest_date, selling_date, storage_available, options, best_option
            )

        # Fallback to intelligent rule-based explanation if LLM not configured or failed
        if not explanation:
            explanation = self._generate_rule_based_explanation(
                crop_name, location, quantity, harvest_date, selling_date, storage_available, options, best_option
            )

        why_this_option = self._generate_why_breakdown(best_option, options)

        trace.append({
            'step': 'Generate Advisory Explanation',
            'action': 'generate_explanation',
            'details': "Synthesized simple, student-friendly explanation highlighting price vs distance trade-offs."
        })

        return {
            'options': options,
            'best_option': best_option,
            'explanation': explanation,
            'why_this_option': why_this_option,
            'trace': trace,
            'disclaimer': (
                "IMPORTANT: This AI Agent output is for decision-support and informational purposes only. "
                "The farmer always retains full control and makes the final decision."
            )
        }

    def _generate_rule_based_explanation(self, crop, location, quantity, harvest_date, selling_date, storage, options, best):
        """
        Creates a clear, transparent, student-friendly explanation comparing options.
        """
        def get_price(o):
            return float(o.get('price_per_kg', o.get('estimated_price', 0.0)))

        best_price = get_price(best)

        if len(options) == 1:
            return (
                f"Based on current market listings, {best['option_name']} is currently the primary viable "
                f"option for {crop} in your region. It offers ₹{best_price:.2f}/kg with an estimated "
                f"net take-home amount of ₹{best['net_amount']:,.2f} after deducting ₹{best['transport_cost']:,.2f} for transport. "
                f"Estimated waste risk is {best['waste_risk']}. We advise confirming prices before dispatch."
            )

        second = options[1]
        second_price = get_price(second)
        best_name = best['option_name']
        second_name = second['option_name']

        # Comparison points
        net_diff = best['net_amount'] - second['net_amount']

        paras = []

        if best['option_type'] == 'Buyer' and second['option_type'] == 'Market':
            if second_price > best_price:
                paras.append(
                    f"{second_name} offers a higher gross price of ₹{second_price:.2f}/kg, "
                    f"but its distance ({second['distance']} km) results in higher transportation cost of ₹{second['transport_cost']:,.2f}. "
                    f"In contrast, nearby buyer {best_name} offers ₹{best_price:.2f}/kg with lower freight of ₹{best['transport_cost']:,.2f} "
                    f"and lower waste risk ({best['waste_risk']})."
                )
            else:
                paras.append(
                    f"Direct buyer {best_name} offers an attractive rate of ₹{best_price:.2f}/kg "
                    f"compared to ₹{second_price:.2f}/kg at {second_name}. Lower transportation expense "
                    f"(₹{best['transport_cost']:,.2f}) also helps secure a higher net return."
                )
        elif best['option_type'] == 'Market' and second['option_type'] == 'Buyer':
            paras.append(
                f"{best_name} offers a favorable market rate of ₹{best_price:.2f}/kg. Even after "
                f"accounting for ₹{best['transport_cost']:,.2f} in transportation, it delivers an estimated net return of "
                f"₹{best['net_amount']:,.2f}, which is ₹{abs(net_diff):,.2f} higher than selling to {second_name}."
            )
        else:
            paras.append(
                f"Comparing available options, {best_name} yields the highest estimated net amount of "
                f"₹{best['net_amount']:,.2f} (offering ₹{best_price:.2f}/kg at {best['distance']} km distance). "
                f"The alternative {second_name} yields ₹{second['net_amount']:,.2f}."
            )

        # Risk commentary
        if best['waste_risk'] == 'Low':
            paras.append(
                f"Because the estimated waste risk is Low, your crop quality is expected to remain fresh "
                f"by the expected selling date."
            )
        elif best['waste_risk'] == 'Medium':
            paras.append(
                f"Notice: The estimated waste risk is Medium. If possible, consider harvesting closer to sale or selling promptly."
            )
        else:
            paras.append(
                f"Caution: Spoilage risk is High due to time between harvest and sale. Quick local sale or cold storage is recommended."
            )

        paras.append(
            f"Conclusion: Based on the available data, {best_name} appears to be a practical and profitable option. "
            f"However, the final decision always rests with you."
        )

        return " ".join(paras)

    def _generate_why_breakdown(self, best, options):
        """
        Structured bullet-point explanation answering 'Why this option?'
        """
        def get_price(o):
            return float(o.get('price_per_kg', o.get('estimated_price', 0.0)))

        best_price = get_price(best)
        avg_price = sum(get_price(o) for o in options) / len(options) if options else best_price

        return {
            'price': (
                f"₹{best_price:.2f}/kg "
                f"({'Above' if best_price >= avg_price else 'Competitive with'} "
                f"regional average of ₹{avg_price:.2f}/kg)"
            ),
            'transport_cost': (
                f"₹{best['transport_cost']:,.2f} "
                f"for approximately {best['distance']} km transport"
            ),
            'waste_risk': (
                f"{best['waste_risk']} Risk - {best.get('waste_risk_details', 'Managed transit')}"
            ),
            'net_amount': (
                f"₹{best['net_amount']:,.2f} expected net earnings after freight deduction"
            )
        }

    def _generate_llm_explanation(self, crop, location, quantity, harvest_date, selling_date, storage, options, best):
        """
        Optional external LLM call. Gracefully handles errors and returns None on failure.
        """
        try:
            prompt = (
                f"You are the Local2Farm AI Advisor helping an Indian farmer.\n"
                f"Farmer Details:\n"
                f"- Crop: {crop}\n"
                f"- Quantity: {quantity} kg\n"
                f"- Location: {location}\n"
                f"- Harvest Date: {harvest_date}\n"
                f"- Expected Selling Date: {selling_date}\n"
                f"- Storage Available: {'Yes' if storage else 'No'}\n\n"
                f"Top Evaluated Options:\n"
                f"{json.dumps(options[:3], indent=2)}\n\n"
                f"Top Recommended Option: {best['option_name']}\n\n"
                f"Instructions:\n"
                f"1. Explain in 3 to 4 simple, warm sentences why the top option is recommended compared to others.\n"
                f"2. Mention price, transport cost, and waste risk.\n"
                f"3. Do NOT claim absolute certainty.\n"
                f"4. Remind the farmer that they make the final decision."
            )

            # Generic OpenAI-compatible chat completion endpoint
            headers = {
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json"
            }
            payload = {
                "model": self.model,
                "messages": [
                    {"role": "system", "content": "You are a helpful, respectful agricultural AI decision-support assistant for farmers."},
                    {"role": "user", "content": prompt}
                ],
                "temperature": 0.4,
                "max_tokens": 250
            }

            resp = requests.post("https://api.openai.com/v1/chat/completions", headers=headers, json=payload, timeout=8)
            if resp.status_code == 200:
                data = resp.json()
                return data['choices'][0]['message']['content'].strip()
        except Exception:
            # On any network or API error, seamlessly fallback to rule-based engine
            return None

        return None
