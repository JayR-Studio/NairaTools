from flask import Flask, render_template, request
import json
import os


app = Flask(__name__)


@app.route("/")
def home():
    return render_template("index.html")


@app.route("/dollar-to-naira", methods=["GET", "POST"])
def dollar_to_naira():
    rate = 1500
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


if __name__ == "__main__":
    app.run(debug=True)
