"""Core business logic for The Autonomous FinTech Team demo.

All records are synthetic, all payments are simulated, and no external payment
provider or financial institution is contacted by this application.
"""
from __future__ import annotations

from collections import Counter
from dataclasses import asdict, dataclass
from datetime import datetime, timedelta
from typing import Any
from uuid import uuid4
from zoneinfo import ZoneInfo
import re

TZ = ZoneInfo("Africa/Tunis")
PRODUCT_NAME = "Formation IA professionnelle"
PRODUCT_PRICE_TND = 590.0


class UnsafeInputError(ValueError):
    """Raised when customer input appears to contain sensitive payment data."""


def now_iso() -> str:
    return datetime.now(TZ).isoformat(timespec="seconds")


def parse_time(value: str) -> datetime:
    return datetime.fromisoformat(value)


def money(value: float) -> float:
    return round(float(value), 2)


@dataclass
class AgentMessage:
    timestamp: str
    sender: str
    recipient: str
    message_type: str
    summary: str
    correlation_id: str


class VoiceSalesAgent:
    """Text-first sales agent; voice transcripts can be pasted into the same input."""
    name = "Voice Sales Agent"

    def respond(self, customer_name: str, customer_text: str) -> dict[str, Any]:
        lower = customer_text.lower()
        if any(x in lower for x in ("prix", "cher", "expensive", "price", "coût", "cost")):
            response = (
                f"Merci pour votre question, {customer_name}. {PRODUCT_NAME} coûte "
                f"{PRODUCT_PRICE_TND:.0f} TND dans cette démonstration. "
                "Je peux vous présenter le programme et les modalités avant toute décision."
            )
        elif any(x in lower for x in ("programme", "contenu", "course", "curriculum", "modules")):
            response = (
                f"Avec plaisir, {customer_name}. Le programme de {PRODUCT_NAME} couvre "
                "les fondamentaux de l'IA, les cas d'usage et un projet pratique. "
                "Souhaitez-vous recevoir le détail des modules ?"
            )
        else:
            response = (
                f"Bonjour {customer_name} ! Merci de votre intérêt pour {PRODUCT_NAME}. "
                f"Le tarif fictif de cette démonstration est de {PRODUCT_PRICE_TND:.0f} TND. "
                "Dites-moi votre objectif ou votre principale question pour que je puisse vous orienter."
            )
        return {
            "agent": self.name,
            "offer": PRODUCT_NAME,
            "price_tnd": PRODUCT_PRICE_TND,
            "response": response,
            "channel": "text_or_simulated_voice_transcript",
            "next_action": "qualify_customer",
        }


class CustomerIntelligenceAgent:
    name = "Customer Intelligence Agent"

    OBJECTION_TERMS = {
        "Prix": ("prix", "cher", "chère", "coût", "tarif", "expensive", "cost", "price", "afford"),
        "Disponibilité": ("temps", "horaire", "emploi", "disponible", "schedule", "time", "busy"),
        "Contenu": ("programme", "contenu", "module", "niveau", "course", "curriculum", "content"),
        "Confiance": ("fiable", "arnaque", "sécurité", "confiance", "trust", "legit", "scam"),
        "Paiement": ("payer", "paiement", "échéance", "carte", "payment", "installment", "pay"),
    }
    POSITIVE = ("intéress", "interesse", "oui", "inscrire", "inscription", "partant", "interested", "sign up", "buy")
    NEGATIVE = ("pas intéress", "pas interesse", "non merci", "déçu", "decu", "trop cher", "not interested", "no thanks")

    def analyze(self, text: str) -> dict[str, Any]:
        lower = text.lower()
        objections = [name for name, terms in self.OBJECTION_TERMS.items() if any(t in lower for t in terms)]
        positive_hits = sum(term in lower for term in self.POSITIVE)
        negative_hits = sum(term in lower for term in self.NEGATIVE)
        if negative_hits > 0 and negative_hits >= positive_hits:
            sentiment = "Négatif"
        elif positive_hits > 0:
            sentiment = "Positif"
        else:
            sentiment = "Neutre"

        intents: list[str] = []
        if any(x in lower for x in ("programme", "contenu", "module", "curriculum", "course")):
            intents.append("Demande d'information")
        if any(x in lower for x in ("payer", "paiement", "inscrire", "inscription", "buy", "pay")):
            intents.append("Intention d'achat / paiement")
        if any(x in lower for x in ("rappel", "appeler", "contact", "call back", "follow up")):
            intents.append("Demande de suivi")
        if not intents:
            intents.append("Découverte de l'offre")

        motivations: list[str] = []
        if any(x in lower for x in ("emploi", "carrière", "carriere", "job", "career", "recrut")):
            motivations.append("Évolution professionnelle")
        if any(x in lower for x in ("compétence", "competence", "apprendre", "formation", "learn", "skill")):
            motivations.append("Développement des compétences")
        if any(x in lower for x in ("projet", "entreprise", "business", "startup", "automatis")):
            motivations.append("Application pratique / projet")
        if not motivations:
            motivations.append("Motivation à préciser")

        score = 0.25 + 0.25 * positive_hits - 0.25 * negative_hits
        if "Confiance" in objections:
            score -= 0.1
        interest_score = max(0.0, min(1.0, score))
        interested = interest_score >= 0.4 and sentiment != "Négatif"
        return {
            "agent": self.name,
            "sentiment": sentiment,
            "intents": intents,
            "motivations": motivations,
            "objections": objections,
            "interest_score": round(interest_score, 2),
            "interested": interested,
            "summary": (
                f"Sentiment {sentiment.lower()} ; "
                f"intentions : {', '.join(intents)} ; "
                f"motivations : {', '.join(motivations)} ; "
                f"objections : {', '.join(objections) if objections else 'aucune'} ; "
                f"intérêt estimé à {round(interest_score * 100)} %."
            ),
        }


class SecurityFraudAgent:
    name = "Security & Fraud Detection Agent"
    INJECTION_PATTERNS = (
        r"ignore (all )?(previous|prior) instructions",
        r"ignore les instructions",
        r"reveal (the )?(system|hidden) prompt",
        r"affiche le prompt système",
        r"bypass (the )?(security|approval)",
        r"contourne(r)? (la )?(sécurité|validation)",
        r"admin(istrator)? override",
        r"act as (the )?system",
    )
    OVERRIDE_TERMS = ("bypass approval", "skip approval", "admin override", "sans validation", "ignore security")

    def inspect(self, customer_text: str, amount_tnd: float, recent_attempts: int) -> dict[str, Any]:
        lower = customer_text.lower()
        flags: list[str] = []
        severity = "LOW"
        blocked = False
        if any(re.search(pattern, lower) for pattern in self.INJECTION_PATTERNS):
            flags.append("Tentative de prompt injection détectée")
            severity = "CRITICAL"
            blocked = True
        if any(term in lower for term in self.OVERRIDE_TERMS):
            if "Demande de contournement des validations" not in flags:
                flags.append("Demande de contournement des validations")
            severity = "CRITICAL"
            blocked = True
        if amount_tnd > 1000:
            flags.append("Montant supérieur au seuil de revue (1 000 TND)")
            if severity != "CRITICAL":
                severity = "HIGH"
        if recent_attempts >= 3:
            flags.append("Plusieurs tentatives de paiement en moins de 10 minutes")
            if severity != "CRITICAL":
                severity = "HIGH"
        action = "BLOCK" if blocked else ("REVIEW" if severity == "HIGH" else "ALLOW_WITH_HUMAN_APPROVAL")
        return {
            "agent": self.name,
            "severity": severity,
            "action": action,
            "flags": flags,
            "recent_attempts": recent_attempts,
            "human_review_required": True,
        }


class PaymentAgent:
    name = "Payment Agent"
    ALLOWED_OUTCOMES = {"SUCCESS", "REFUSED", "PENDING"}

    def create_intent(self, customer_id: str, amount_tnd: float, security: dict[str, Any], simulated_outcome: str) -> dict[str, Any]:
        if simulated_outcome not in self.ALLOWED_OUTCOMES:
            raise ValueError("Résultat de simulation invalide.")
        if amount_tnd <= 0 or amount_tnd > 100000:
            raise ValueError("Le montant doit être compris entre 0 et 100 000 TND.")
        status = "BLOCKED" if security["action"] == "BLOCK" else "AWAITING_APPROVAL"
        return {
            "id": f"TX-{uuid4().hex[:8].upper()}",
            "customer_id": customer_id,
            "amount_tnd": money(amount_tnd),
            "currency": "TND",
            "status": status,
            "simulated_outcome": simulated_outcome,
            "security_severity": security["severity"],
            "created_at": now_iso(),
            "approved_at": None,
            "note": "Simulation locale uniquement ; aucun paiement réel ni appel API.",
        }

    def apply_human_decision(self, transaction: dict[str, Any], approve: bool) -> dict[str, Any]:
        if transaction["status"] != "AWAITING_APPROVAL":
            raise ValueError("Cette intention n'est pas en attente d'approbation.")
        transaction["status"] = transaction["simulated_outcome"] if approve else "DECLINED_BY_HUMAN"
        transaction["approved_at"] = now_iso()
        return transaction


class FinancialDataAnalystAgent:
    name = "Financial Data Analyst"

    def analyze(self, interactions: list[dict[str, Any]], transactions: list[dict[str, Any]]) -> dict[str, Any]:
        successful = [tx for tx in transactions if tx["status"] == "SUCCESS"]
        revenue = money(sum(tx["amount_tnd"] for tx in successful))
        interested = sum(1 for item in interactions if item.get("interested"))
        conversion = (len(successful) / len(interactions) * 100) if interactions else 0.0
        statuses = Counter(tx["status"] for tx in transactions)
        objections = Counter(o for item in interactions for o in item.get("objections", []))
        sentiments = Counter(item.get("sentiment", "Neutre") for item in interactions)
        return {
            "agent": self.name,
            "interactions": len(interactions),
            "interested_customers": interested,
            "conversion_rate": round(conversion, 1),
            "simulated_revenue_tnd": revenue,
            "payment_statuses": dict(statuses),
            "top_objections": objections.most_common(5),
            "sentiments": dict(sentiments),
        }


class BusinessStrategyAgent:
    name = "Business Strategy Agent"

    def recommend(self, analytics: dict[str, Any]) -> list[str]:
        recommendations: list[str] = []
        objections = dict(analytics["top_objections"])
        if objections.get("Prix", 0):
            recommendations.append("Tester une option de paiement échelonné ou mieux détailler la valeur apportée pour répondre à l'objection prix.")
        if objections.get("Disponibilité", 0):
            recommendations.append("Proposer plusieurs créneaux ou un parcours flexible pour les prospects contraints par leur emploi du temps.")
        if objections.get("Contenu", 0):
            recommendations.append("Afficher le programme détaillé, les prérequis et un exemple de projet avant l'inscription.")
        if objections.get("Confiance", 0):
            recommendations.append("Renforcer la réassurance avec des informations vérifiables sur le programme, l'équipe et les conditions.")
        if analytics["conversion_rate"] < 20 and analytics["interactions"] >= 3:
            recommendations.append("Analyser les conversations non converties et tester un suivi commercial après consentement.")
        if analytics["interactions"] == 0:
            recommendations.append("Lancer quelques interactions de test pour alimenter l'analyse et le tableau de bord.")
        if not recommendations:
            recommendations.append("Conserver le script actuel et suivre l'évolution du taux de conversion sur un échantillon plus large.")
        return recommendations[:5]


class FinTechEngine:
    """Orchestrates the six agents and keeps an auditable in-memory demo state."""

    def __init__(self) -> None:
        self.sales = VoiceSalesAgent()
        self.intelligence = CustomerIntelligenceAgent()
        self.security = SecurityFraudAgent()
        self.payment = PaymentAgent()
        self.analyst = FinancialDataAnalystAgent()
        self.strategy = BusinessStrategyAgent()
        self.reset(load_demo=True)

    def reset(self, load_demo: bool = False) -> None:
        self.interactions: list[dict[str, Any]] = []
        self.transactions: list[dict[str, Any]] = []
        self.alerts: list[dict[str, Any]] = []
        self.audit: list[dict[str, Any]] = []
        self.messages: list[dict[str, Any]] = []
        self.recommendations: list[str] = []
        if load_demo:
            self._load_demo()

    def _log(self, action: str, actor: str, detail: str, correlation_id: str | None = None) -> None:
        self.audit.append({
            "timestamp": now_iso(),
            "actor": actor,
            "action": action,
            "detail": detail,
            "correlation_id": correlation_id or "SYSTEM",
        })

    def _message(self, sender: str, recipient: str, message_type: str, summary: str, correlation_id: str) -> None:
        self.messages.append(asdict(AgentMessage(now_iso(), sender, recipient, message_type, summary, correlation_id)))

    def _add_alert(self, severity: str, title: str, detail: str, correlation_id: str) -> None:
        self.alerts.append({
            "id": f"AL-{uuid4().hex[:7].upper()}",
            "timestamp": now_iso(),
            "severity": severity,
            "title": title,
            "detail": detail,
            "correlation_id": correlation_id,
        })

    @staticmethod
    def _validate_text(text: str) -> str:
        if not isinstance(text, str) or not text.strip():
            raise ValueError("Veuillez saisir le message du client.")
        if len(text) > 2000:
            raise ValueError("Le message dépasse la limite de 2 000 caractères.")
        # Reject sensitive payment credentials; never store them in the demo logs.
        sensitive_patterns = (
            r"(?<!\d)(?:\d[ -]?){13,19}(?!\d)",  # card-like PAN
            r"\b[A-Z]{2}\d{2}[A-Z0-9]{11,30}\b",  # IBAN-like sequence
            r"\b(?:cvv|cvc|security code|code de sécurité)\s*[:=]?\s*\d{3,4}\b",
            r"\b(?:password|mot de passe|secret)\s*[:=]\s*\S+",
        )
        if any(re.search(pattern, text, flags=re.IGNORECASE) for pattern in sensitive_patterns):
            raise UnsafeInputError("Une donnée bancaire ou un secret potentiel a été détecté. L'entrée a été rejetée ; ne saisissez jamais de numéro de carte, CVV, IBAN, mot de passe ou identifiant bancaire.")
        return text.strip()

    def _recent_attempt_count(self, customer_id: str, minutes: int = 10) -> int:
        cutoff = datetime.now(TZ) - timedelta(minutes=minutes)
        count = 0
        for tx in self.transactions:
            if tx.get("customer_id") == customer_id and tx.get("created_at"):
                try:
                    if parse_time(tx["created_at"]) >= cutoff:
                        count += 1
                except (ValueError, TypeError):
                    continue
        return count

    @staticmethod
    def _analytics_projection(interactions: list[dict[str, Any]]) -> list[dict[str, Any]]:
        """Share only aggregated fields with the analyst, never raw customer messages."""
        return [{
            "interested": item.get("interested", False),
            "sentiment": item.get("sentiment", "Neutre"),
            "objections": list(item.get("objections", [])),
        } for item in interactions]

    def run_journey(
        self,
        customer_name: str,
        customer_message: str,
        amount_tnd: float = PRODUCT_PRICE_TND,
        create_payment: bool = True,
        simulated_outcome: str = "SUCCESS",
        customer_id: str | None = None,
    ) -> dict[str, Any]:
        text = self._validate_text(customer_message)
        name = (customer_name or "Client démo").strip()[:60] or "Client démo"
        try:
            amount = float(amount_tnd)
        except (TypeError, ValueError):
            raise ValueError("Montant invalide.")
        if amount <= 0 or amount > 100000:
            raise ValueError("Le montant doit être supérieur à 0 et inférieur ou égal à 100 000 TND.")
        cid = customer_id or f"CUST-{uuid4().hex[:6].upper()}"
        correlation_id = f"FLOW-{uuid4().hex[:8].upper()}"

        # 1. Sales agent
        sales_result = self.sales.respond(name, text)
        self._message(self.sales.name, self.intelligence.name, "CUSTOMER_CONTEXT", "Interaction client transmise pour qualification.", correlation_id)
        self._log("SALES_RESPONSE", self.sales.name, "Réponse commerciale générée à partir d'une offre fictive.", correlation_id)

        # 2. Customer intelligence
        intelligence_result = self.intelligence.analyze(text)
        self._message(self.intelligence.name, self.security.name, "CUSTOMER_SIGNALS", intelligence_result["summary"], correlation_id)
        self._log("CUSTOMER_ANALYSIS", self.intelligence.name, intelligence_result["summary"], correlation_id)

        interaction = {
            "id": f"INT-{uuid4().hex[:8].upper()}",
            "correlation_id": correlation_id,
            "customer_id": cid,
            "customer_name": name,
            "timestamp": now_iso(),
            "message": text,
            "sentiment": intelligence_result["sentiment"],
            "intents": intelligence_result["intents"],
            "motivations": intelligence_result["motivations"],
            "objections": intelligence_result["objections"],
            "interest_score": intelligence_result["interest_score"],
            "interested": intelligence_result["interested"],
        }
        self.interactions.append(interaction)

        # 3. Security agent evaluates before payment intent is created.
        security_result = self.security.inspect(text, amount, self._recent_attempt_count(cid))
        self._message(self.security.name, self.payment.name, "SECURITY_DECISION", f"Action={security_result['action']} ; sévérité={security_result['severity']}.", correlation_id)
        if security_result["flags"]:
            for flag in security_result["flags"]:
                self._add_alert(security_result["severity"], flag, f"Client {cid} ; montant demandé {amount:.2f} TND.", correlation_id)
        self._log("SECURITY_CHECK", self.security.name, f"Action={security_result['action']} ; flags={len(security_result['flags'])}.", correlation_id)

        transaction = None
        if create_payment:
            transaction = self.payment.create_intent(cid, amount, security_result, simulated_outcome)
            transaction["customer_name"] = name
            transaction["correlation_id"] = correlation_id
            self.transactions.append(transaction)
            self._message(self.payment.name, self.analyst.name, "PAYMENT_INTENT", f"Intention {transaction['id']} créée avec statut {transaction['status']}.", correlation_id)
            self._log("PAYMENT_INTENT_CREATED", self.payment.name, f"{transaction['id']} ; statut={transaction['status']}.", correlation_id)
            if transaction["status"] == "BLOCKED":
                self._add_alert("CRITICAL", "Intention de paiement bloquée", "Aucune approbation ne peut débloquer automatiquement une transaction bloquée par sécurité.", correlation_id)
        else:
            self._message(self.security.name, self.analyst.name, "NO_PAYMENT", "Aucune intention de paiement demandée.", correlation_id)

        analytics = self.analyst.analyze(self._analytics_projection(self.interactions), self.transactions)
        self._message(self.analyst.name, self.strategy.name, "FINANCIAL_INSIGHTS", f"{analytics['interactions']} interactions ; revenu simulé {analytics['simulated_revenue_tnd']:.2f} TND.", correlation_id)
        self.recommendations = self.strategy.recommend(analytics)
        self._message(self.strategy.name, "Dashboard", "RECOMMENDATIONS", f"{len(self.recommendations)} recommandation(s) disponibles.", correlation_id)
        self._log("STRATEGY_UPDATED", self.strategy.name, f"{len(self.recommendations)} recommandation(s) générée(s).", correlation_id)

        return {
            "correlation_id": correlation_id,
            "sales": sales_result,
            "intelligence": intelligence_result,
            "security": security_result,
            "transaction": transaction,
            "analytics": analytics,
            "recommendations": self.recommendations,
        }

    def decide_transaction(self, transaction_id: str, approve: bool) -> dict[str, Any]:
        tx = next((item for item in self.transactions if item["id"] == transaction_id), None)
        if tx is None:
            raise ValueError("Transaction introuvable.")
        self.payment.apply_human_decision(tx, approve)
        decision = "APPROVED" if approve else "DECLINED_BY_HUMAN"
        self._log("HUMAN_PAYMENT_DECISION", "Human Reviewer", f"{transaction_id} ; décision={decision} ; résultat simulé={tx['status']}.", tx.get("correlation_id"))
        self._message("Human Reviewer", self.payment.name, "HUMAN_DECISION", f"{decision} pour {transaction_id}.", tx.get("correlation_id", "SYSTEM"))
        return tx

    def metrics(self) -> dict[str, Any]:
        return self.analyst.analyze(self._analytics_projection(self.interactions), self.transactions)

    def _load_demo(self) -> None:
        """Seed clearly fictional data so the dashboard is useful on first launch."""
        demo_rows = [
            ("Lina Démo", "Je suis intéressée par la formation, pouvez-vous m'envoyer le programme ?", "Positif", ["Contenu"], 0.75, True),
            ("Sami Démo", "Le prix est un peu cher. Est-il possible de payer en plusieurs fois ?", "Neutre", ["Prix", "Paiement"], 0.5, True),
            ("Nour Démo", "Je ne suis pas intéressée pour le moment, je manque de temps.", "Négatif", ["Disponibilité"], 0.0, False),
            ("Amine Démo", "Je souhaite m'inscrire, mais je voudrais connaître les prérequis.", "Positif", ["Contenu"], 0.75, True),
        ]
        for idx, row in enumerate(demo_rows, start=1):
            name, msg, sentiment, objections, score, interested = row
            flow = f"FLOW-DEMO-{idx:02d}"
            self.interactions.append({
                "id": f"INT-DEMO-{idx:02d}",
                "correlation_id": flow,
                "customer_id": f"CUST-DEMO-{idx:02d}",
                "customer_name": name,
                "timestamp": now_iso(),
                "message": msg,
                "sentiment": sentiment,
                "intents": ["Demande d'information"],
                "motivations": ["Motivation à préciser"],
                "objections": objections,
                "interest_score": score,
                "interested": interested,
            })
        tx_specs = [
            ("TX-DEMO-001", "CUST-DEMO-01", "Lina Démo", 590.0, "SUCCESS", "FLOW-DEMO-01"),
            ("TX-DEMO-002", "CUST-DEMO-02", "Sami Démo", 590.0, "REFUSED", "FLOW-DEMO-02"),
            ("TX-DEMO-003", "CUST-DEMO-04", "Amine Démo", 590.0, "AWAITING_APPROVAL", "FLOW-DEMO-04"),
        ]
        for txid, cid, name, amount, status, flow in tx_specs:
            self.transactions.append({
                "id": txid,
                "customer_id": cid,
                "customer_name": name,
                "amount_tnd": amount,
                "currency": "TND",
                "status": status,
                "simulated_outcome": "SUCCESS",
                "security_severity": "LOW",
                "created_at": now_iso(),
                "approved_at": now_iso() if status != "AWAITING_APPROVAL" else None,
                "correlation_id": flow,
                "note": "Donnée fictive préchargée pour la démonstration.",
            })
        self._add_alert("HIGH", "Montant inhabituel détecté (jeu de données démo)", "Événement synthétique destiné à illustrer la revue de sécurité.", "FLOW-DEMO-SEC-01")
        self._add_alert("MEDIUM", "Tentative suspecte simulée", "Événement synthétique ; aucune donnée bancaire réelle n'est utilisée.", "FLOW-DEMO-SEC-02")
        self._message("Voice Sales Agent", "Customer Intelligence Agent", "CUSTOMER_CONTEXT", "Interaction client démo transmise.", "FLOW-DEMO-01")
        self._message("Customer Intelligence Agent", "Security & Fraud Detection Agent", "CUSTOMER_SIGNALS", "Signaux client démo structurés.", "FLOW-DEMO-01")
        self._message("Security & Fraud Detection Agent", "Payment Agent", "SECURITY_DECISION", "Autorisation de créer une intention ; approbation humaine requise.", "FLOW-DEMO-01")
        self._message("Payment Agent", "Financial Data Analyst", "PAYMENT_RESULT", "Paiement simulé réussi ; données fictives.", "FLOW-DEMO-01")
        self._message("Financial Data Analyst", "Business Strategy Agent", "FINANCIAL_INSIGHTS", "Indicateurs initiaux calculés.", "FLOW-DEMO-01")
        self.recommendations = self.strategy.recommend(self.metrics())
        self._log("DEMO_DATA_LOADED", "System", "Jeu de données entièrement fictif chargé.", "SYSTEM")
