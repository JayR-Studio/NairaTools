from flask import Flask, render_template, request
import json
import os
import requests
from datetime import datetime, timedelta

app = Flask(__name__)

USD_NGN_RATE = None
RATE_LAST_UPDATED = None


def get_usd_to_ngn_rate():
    global USD_NGN_RATE, RATE_LAST_UPDATED

    # If rate exists and is less than 6 hours old, reuse it
    if USD_NGN_RATE and RATE_LAST_UPDATED:
        if datetime.now() - RATE_LAST_UPDATED < timedelta(hours=6):
            return USD_NGN_RATE

    try:
        url = "https://open.er-api.com/v6/latest/USD"
        response = requests.get(url, timeout=10)
        data = response.json()

        USD_NGN_RATE = data["rates"]["NGN"]
        RATE_LAST_UPDATED = datetime.now()

        return USD_NGN_RATE

    except Exception:
        # fallback rate if API fails
        return USD_NGN_RATE or 1376


@app.route("/")
def home():
    rate = get_usd_to_ngn_rate()
    return render_template("index.html", rate=rate)


@app.route("/about")
def about():
    return render_template("about.html")


@app.route("/privacy")
def privacy():
    return render_template("privacy.html")


@app.route("/contact")
def contact():
    return render_template("contact.html")


@app.context_processor
def inject_current_year():
    return {
        "current_year": datetime.now().year
    }


@app.route("/dollar-to-naira", methods=["GET", "POST"])
def dollar_to_naira():
    rate = get_usd_to_ngn_rate()
    result = None

    if request.method == "POST":
        amount = float(request.form.get("amount"))
        direction = request.form.get("direction")

        if direction == "usd-to-ngn":
            converted = amount * rate
            result = f"${amount:,.2f} = ₦{converted:,.2f}"
        else:
            converted = amount / rate
            result = f"₦{amount:,.2f} = ${converted:,.2f}"

    return render_template(
        "dollar_to_naira.html",
        rate=rate,
        result=result
    )


@app.route("/loan-calculator", methods=["GET", "POST"])
def loan_calculator():
    result = None

    if request.method == "POST":
        principal = float(request.form.get("principal"))
        repayment = float(request.form.get("repayment"))

        interest_paid = repayment - principal
        interest_rate = (interest_paid / principal) * 100

        if interest_rate <= 10:
            verdict = "This looks like a relatively low-interest loan. "
        elif interest_rate <= 25:
            verdict = "This is a moderate-interest loan. Review carefully before accepting."
        else:
            verdict = "This is a high-interest loan. Be very careful before accepting."

        result = {
            "principal": principal,
            "repayment": repayment,
            "interest_paid": interest_paid,
            "interest_rate": interest_rate,
            "verdict": verdict
        }

    return render_template("loan_calculator.html", result=result)


@app.route("/data-plans")
def data_plans():
    selected_network = request.args.get("network", "all")
    selected_type = request.args.get("type", "all")
    selected_validity = request.args.get("validity", "all")

    advice_result = None

    file_path = os.path.join(app.root_path, "data", "data_plans_clean.json")

    with open(file_path, "r", encoding="utf-8") as file:
        plans = json.load(file)

    networks = ["all", "MTN", "AIRTEL", "GLO", "9MOBILE"]

    # Extract unique types from data
    types = sorted(list(set(plan["plan_type"] for plan in plans if plan["plan_type"])))

    # Extract unique Validity from data
    validity = sorted(list(set(plan["validity_label"] for plan in plans if plan["validity_label"])))

    filtered_plans = plans

    budget = request.args.get("budget")
    usage = request.args.get("usage")
    preferred_network = request.args.get("preferred_network", "all")
    adviser_validity = request.args.get("adviser_validity", "all")

    if budget and usage:
        budget = float(budget)

        adviser_plans = plans

        if preferred_network != "all":
            adviser_plans = [
                p for p in adviser_plans
                if p["network"].upper() == preferred_network.upper()
            ]

        if adviser_validity != "all":
            adviser_plans = [
                p for p in adviser_plans
                if p["validity_label"] == adviser_validity
            ]

        adviser_plans = [
            p for p in adviser_plans
            if p["price"] <= budget and p.get("data_mb")
        ]

        if usage == "social":
            adviser_plans = [
                p for p in adviser_plans
                if p["data_mb"] <= 2048
            ]
        elif usage == "streaming":
            adviser_plans = [
                p for p in adviser_plans
                if p["data_mb"] >= 2048
            ]
        elif usage == "heavy":
            adviser_plans = [
                p for p in adviser_plans
                if p["data_mb"] >= 5120
            ]

        if adviser_plans:
            best_plan = max(adviser_plans, key=lambda p: p["data_mb"])

            advice_result = {
                "plan": best_plan,
                "reason": f"This plan gives you the highest data within your ₦{budget:,.0f} budget."
            }

    if selected_network != "all":
        filtered_plans = [
            p for p in filtered_plans
            if p["network"].upper() == selected_network.upper()
        ]

    if selected_type != "all":
        filtered_plans = [
            p for p in filtered_plans
            if p["plan_type"] == selected_type
        ]

    if selected_validity != "all":
        filtered_plans = [
            p for p in filtered_plans
            if p["validity_label"] == selected_validity
        ]

    return render_template(
        "data_plans.html",
        plans=filtered_plans,
        networks=networks,
        types=types,
        validity=validity,
        selected_network=selected_network,
        selected_type=selected_type,
        selected_validity=selected_validity,
        advice_result=advice_result
    )


@app.route("/salary-survival", methods=["GET", "POST"])
def salary_survival():
    result = None

    if request.method == "POST":
        salary = float(request.form.get("salary"))
        essentials = float(request.form.get("essentials"))
        obligations = float(request.form.get("obligations"))
        lifestyle = float(request.form.get("lifestyle") or 0)

        total_expenses = essentials + obligations + lifestyle
        amount_left = salary - total_expenses
        safe_amount = salary * 0.3

        essentials_percent = (essentials / salary) * 100
        obligations_percent = (obligations / salary) * 100
        lifestyle_percent = (lifestyle / salary) * 100

        weeks = []

        if amount_left >= safe_amount:
            status = "Safe Zone"
            status_class = "safe"
            brutal_truth = "You have breathing room this month. Keep spending controlled and avoid unnecessary debt."
            way_out = "You are in a good position. Try to protect part of your leftover money and avoid lifestyle spending."

            weekly_amount = amount_left / 4

            for week in range(1, 5):
                weeks.append({
                    "week": week,
                    "balance": weekly_amount,
                    "status": "Safe"
                })

        elif amount_left > 0:
            status = "Tight Zone"
            status_class = "tight"
            brutal_truth = "You are one unexpected expense away from trouble."
            needed = safe_amount - amount_left
            way_out = f"To enter the Safe Zone, reduce expenses or increase income by about ₦{needed:,.0f}. Avoid reborrowing unless it is absolutely necessary."

            weekly_amount = amount_left / 4

            for week in range(1, 5):
                week_status = "Tight" if weekly_amount > 0 else "Danger"

                weeks.append({
                    "week": week,
                    "balance": weekly_amount,
                    "status": week_status
                })

        else:
            status = "Danger Zone"
            status_class = "danger"
            brutal_truth = "Your expenses are higher than your salary. You may run out of money before the month even begins."
            needed = abs(amount_left)
            way_out = f"You need to reduce expenses, increase income, or restructure repayments by at least ₦{needed:,.0f} just to break even. Do not take another loan unless it solves the root problem."
            weekly_amount = None

        leaks = []

        if amount_left < 0:
            leaks.append({
                "title": "Monthly Deficit",
                "severity": "critical",
                "message": f"You are spending ₦{abs(amount_left):,.0f} more than your salary this month."
            })

        if obligations_percent > 30:
            leaks.append({
                "title": "Obligation Pressure",
                "severity": "high" if obligations_percent > 40 else "moderate",
                "message": f"Your loans and fixed responsibilities are taking {obligations_percent:.0f}% of your salary."
            })

        if lifestyle_percent > 20:
            allowed_lifestyle = salary * 0.2
            reduce_lifestyle_by = lifestyle - allowed_lifestyle

            leaks.append({
                "title": "Lifestyle Leak",
                "severity": "moderate",
                "message": f"Your lifestyle spending is above the safe range. Try reducing it by about ₦{reduce_lifestyle_by:,.0f}."
            })

        result = {
            "salary": salary,
            "total_expenses": total_expenses,
            "amount_left": amount_left,
            "safe_amount": safe_amount,
            "status": status,
            "status_class": status_class,
            "brutal_truth": brutal_truth,
            "way_out": way_out,
            "weekly_amount": weekly_amount,
            "weeks": weeks,
            "essentials": essentials,
            "obligations": obligations,
            "lifestyle": lifestyle,
            "essentials_percent": essentials_percent,
            "obligations_percent": obligations_percent,
            "lifestyle_percent": lifestyle_percent,
            "leaks": leaks
        }

    return render_template("salary_survival.html", result=result)


if __name__ == "__main__":
    app.run(debug=True)
