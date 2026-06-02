# app/mock_generator.py
# Utility to generate synthetic datasets for testing the Archeologist platform.

import csv
import random
from datetime import datetime, timedelta

def generate_dataset():
    domains = ["Marketing", "Sales", "Finance", "Transportation"]
    users = {
        "Marketing": ["alice_mkt", "bob_growth", "carol_ops"],
        "Sales": ["david_crm", "eva_deal", "frank_rev"],
        "Finance": ["grace_tax", "henry_ledger", "aniruddha_p"],
        "Transportation": ["iris_fleet", "jack_routes", "kyle_tms"]
    }
    channels = {"Marketing": "mkt-campaigns", "Sales": "sales-funnel", "Finance": "finance-recon", "Transportation": "logistics-supply"}
    start_date = datetime(2026, 1, 1)
    
    # 1. SLACK MESSAGES
    print("Writing 5000 records to slack_messages.csv...")
    with open('slack_messages.csv', mode='w', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        writer.writerow(['timestamp', 'user', 'channel', 'text'])
        vocab = {
            "Marketing": ["HubSpot API change", "AdWords tracking pixel", "Leads mismatch", "ROAS calculation drop"],
            "Sales": ["Salesforce opportunity sync", "Pipeline velocity pipeline", "Deal closing block", "ARR calculation mismatch"],
            "Finance": ["Stripe gateway latency", "NetSuite ledger variance", "Reconciliation error", "Invoice double-billing match"],
            "Transportation": ["EDI 214 webhook command dropped", "Fleet telematics latency", "TMS route failure", "Logistics capacity constraint"]
        }
        for i in range(5000):
            domain = random.choice(domains)
            user = random.choice(users[domain])
            timestamp = start_date + timedelta(minutes=i * 4)
            text = f"Hey team, monitoring the {random.choice(vocab[domain])}. Needs review before the migration push."
            channel = channels[domain]
            if i == 2500:
                text = "CRITICAL ALERT: rotated the Stripe gateway credential token but forgot to update the finance-recon environment config variable sync."
                user = "aniruddha_p"
                channel = "finance-recon"
            writer.writerow([timestamp.strftime('%Y-%m-%d %H:%M:%S'), user, channel, text])

    # 2. JIRA TICKETS
    print("Writing 5000 records to jira_tickets.csv...")
    with open('jira_tickets.csv', mode='w', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        writer.writerow(['ticket_id', 'summary', 'status', 'assignee', 'reporter', 'description', 'updated_at'])
        for i in range(1, 5001):
            domain = random.choice(domains)
            ticket_id = f"{domain[:3].upper()}-{1000 + i}"
            updated_at = start_date + timedelta(minutes=i * 4)
            row = [ticket_id, f"Optimize {domain} pipeline storage", "OPEN", random.choice(users[domain]), random.choice(users[domain]), "Refactoring configurations to support open cloud lakehouse schemas.", updated_at.strftime('%Y-%m-%d %H:%M:%S')]
            if i == 3200:
                row = ["FIN-4200", "Investigate Stripe ledger sync discrepancy", "IN_PROGRESS", "henry_ledger", "grace_tax", "Automated recon jobs throwing auth exceptions. Stripe data missing via Fivetran due to token failure.", updated_at.strftime('%Y-%m-%d %H:%M:%S')]
            writer.writerow(row)

    # 3. GITHUB COMMITS
    print("Writing 5000 records to github_commits.csv...")
    with open('github_commits.csv', mode='w', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        writer.writerow(['commit_id', 'author', 'repository', 'commit_message', 'code_diff', 'committed_at'])
        repos = {"Marketing": "mktg-attribution", "Sales": "salesforce-pipeline", "Finance": "finance-ledger-recon", "Transportation": "tms-routing-engine"}
        for i in range(5000):
            domain = random.choice(domains)
            committed_at = start_date + timedelta(minutes=i * 4)
            row = [f"c{random.randint(1000000, 9999999)}", random.choice(users[domain]), repos[domain], f"Clean up inside {domain.lower()} transformation logic", "- version: 1.0.1\n+ version: 1.0.2", committed_at.strftime('%Y-%m-%d %H:%M:%S')]
            if i == 4100:
                row = ["c998124f", "aniruddha_p", "finance-ledger-recon", "Hotfix for transaction web-hook authentication string format", "- auth_token = os.getenv('STRIPE_TOKEN')\n+ auth_token = 'STATIC_EXPIRED_FALLBACK_VAL'", committed_at.strftime('%Y-%m-%d %H:%M:%S')]
            writer.writerow(row)

    print("Success! Dataset synthesis complete.")

if __name__ == "__main__":
    generate_dataset()
