from __future__ import annotations

import json
from datetime import datetime

import pandas as pd
import streamlit as st

from engine import FinTechEngine, PRODUCT_NAME, PRODUCT_PRICE_TND, UnsafeInputError

st.set_page_config(
    page_title="The Autonomous FinTech Team",
    page_icon="⚡",
    layout="wide",
    initial_sidebar_state="expanded",
)

CUSTOM_CSS = """
<style>
:root { --navy: #0c2340; --orange: #f59e0b; }
.block-container { padding-top: 1.5rem; padding-bottom: 2.2rem; max-width: 1500px; }
[data-testid="stSidebar"] { background: #0c2340; }
[data-testid="stSidebar"] * { color: #f8fafc !important; }
[data-testid="stSidebar"] .stButton button { background: #f59e0b; color: #111827 !important; border: 0; font-weight: 700; }
.hero { background: linear-gradient(120deg,#0c2340 0%,#183b63 100%); color: #fff; border-radius: 18px; padding: 1.5rem 1.8rem; margin-bottom: 1rem; border-left: 6px solid #f59e0b; }
.hero h1 { color: #fff; font-size: 2rem; margin: 0 0 .35rem 0; }
.hero p { color: #dbeafe; margin: 0; font-size: .96rem; }
.kpi { background: #f6f8fc; border: 1px solid #e0e7f0; border-radius: 14px; padding: 1rem 1.1rem; min-height: 104px; }
.kpi-label { color: #52627a; font-size: .82rem; font-weight: 600; }
.kpi-value { color: #0c2340; font-size: 1.75rem; font-weight: 800; margin-top: .15rem; }
.kpi-help { color: #6b7280; font-size: .74rem; }
.section-title { color: #0c2340; font-weight: 800; font-size: 1.15rem; margin: .35rem 0 .65rem; }
.agent-card { border: 1px solid #dbe4ef; border-radius: 12px; padding: .9rem; background: #fff; min-height: 124px; }
.agent-card strong { color: #0c2340; }
.agent-card small { color: #64748b; }
.pill { display:inline-block; border-radius:999px; padding:.18rem .55rem; font-size:.72rem; font-weight:700; background:#eaf1fa; color:#17365d; margin:.15rem .15rem .15rem 0; }
.footer-note { color: #64748b; font-size: .78rem; border-top: 1px solid #e5e7eb; padding-top: .8rem; margin-top: 1.4rem; }
div[data-testid="stMetric"] { background:#f6f8fc; border:1px solid #e0e7f0; padding: .8rem 1rem; border-radius: 12px; }
.stButton button[kind="primary"] { background: #f59e0b; border-color: #f59e0b; color:#172033; font-weight:800; }
</style>
"""
st.markdown(CUSTOM_CSS, unsafe_allow_html=True)

if "engine" not in st.session_state:
    st.session_state.engine = FinTechEngine()
engine: FinTechEngine = st.session_state.engine

STATUS_FR = {
    "SUCCESS": "Réussi",
    "REFUSED": "Refusé",
    "PENDING": "En attente",
    "AWAITING_APPROVAL": "Approbation requise",
    "DECLINED_BY_HUMAN": "Rejeté par le valideur",
    "BLOCKED": "Bloqué par la sécurité",
}
SEVERITY_FR = {"LOW": "Faible", "MEDIUM": "Moyenne", "HIGH": "Élevée", "CRITICAL": "Critique"}


def money_tnd(value: float) -> str:
    return f"{value:,.2f} TND".replace(",", " ")


def render_kpi(label: str, value: str, help_text: str = "") -> None:
    st.markdown(
        f'<div class="kpi"><div class="kpi-label">{label}</div>'
        f'<div class="kpi-value">{value}</div><div class="kpi-help">{help_text}</div></div>',
        unsafe_allow_html=True,
    )


def transactions_frame() -> pd.DataFrame:
    rows = []
    for tx in reversed(engine.transactions):
        rows.append({
            "ID": tx["id"],
            "Client": tx.get("customer_name", tx["customer_id"]),
            "Montant": money_tnd(tx["amount_tnd"]),
            "Statut": STATUS_FR.get(tx["status"], tx["status"]),
            "Sécurité": SEVERITY_FR.get(tx.get("security_severity", "LOW"), tx.get("security_severity", "LOW")),
            "Créée le": tx["created_at"].replace("T", " ")[:19],
        })
    return pd.DataFrame(rows)


def audit_frame() -> pd.DataFrame:
    return pd.DataFrame([
        {"Horodatage": e["timestamp"].replace("T", " ")[:19], "Acteur": e["actor"], "Action": e["action"], "Détail": e["detail"], "Flux": e["correlation_id"]}
        for e in reversed(engine.audit)
    ])


def csv_download(label: str, df: pd.DataFrame, filename: str, key: str) -> None:
    st.download_button(label, df.to_csv(index=False).encode("utf-8-sig"), file_name=filename, mime="text/csv", key=key)


# Sidebar controls
with st.sidebar:
    st.markdown("## ⚡ TECHX · 2026–2027")
    st.markdown("### Autonomous FinTech Team")
    st.caption("Prototype multi-agents · Démo locale")
    st.divider()
    st.markdown("**Environnement**")
    st.success("Simulation uniquement")
    st.caption("Aucun paiement réel, aucune API bancaire et aucune donnée bancaire requise.")
    st.divider()
    st.markdown("**Données de démonstration**")
    if st.button("Recharger les données démo", use_container_width=True):
        engine.reset(load_demo=True)
        st.session_state.pop("last_result", None)
        st.rerun()
    if st.button("Vider toutes les données", use_container_width=True):
        engine.reset(load_demo=False)
        st.session_state.pop("last_result", None)
        st.rerun()
    st.caption("Les données sont conservées uniquement dans la session Streamlit en cours.")

st.markdown(
    '<div class="hero"><h1>THE AUTONOMOUS FINTECH TEAM</h1>'
    '<p>Une équipe d’agents spécialisés qui collabore pour qualifier un client, simuler un paiement, analyser la performance et sécuriser chaque décision.</p></div>',
    unsafe_allow_html=True,
)

metrics = engine.metrics()
alerts_critical = sum(1 for a in engine.alerts if a["severity"] in ("HIGH", "CRITICAL"))

# Overview metrics
kpi_cols = st.columns(5)
with kpi_cols[0]: render_kpi("Interactions", str(metrics["interactions"]), "Interactions client enregistrées")
with kpi_cols[1]: render_kpi("Clients intéressés", str(metrics["interested_customers"]), "Qualification par Customer Intelligence")
with kpi_cols[2]: render_kpi("Conversion", f'{metrics["conversion_rate"]:.1f} %', "Paiements réussis / interactions")
with kpi_cols[3]: render_kpi("Revenu simulé", money_tnd(metrics["simulated_revenue_tnd"]), "Transactions au statut réussi uniquement")
with kpi_cols[4]: render_kpi("Alertes sécurité", str(len(engine.alerts)), f"{alerts_critical} de sévérité élevée / critique")

st.write("")
tabs = st.tabs(["Vue d'ensemble", "Parcours client", "Paiements & validations", "Sécurité & traçabilité", "Architecture multi-agents"])

# TAB 1 — Dashboard
with tabs[0]:
    left, right = st.columns([1.1, 1])
    with left:
        st.markdown('<div class="section-title">Statuts des paiements simulés</div>', unsafe_allow_html=True)
        status_order = ["SUCCESS", "REFUSED", "PENDING", "AWAITING_APPROVAL", "DECLINED_BY_HUMAN", "BLOCKED"]
        status_counts = {STATUS_FR[s]: sum(1 for t in engine.transactions if t["status"] == s) for s in status_order}
        status_df = pd.DataFrame({"Statut": list(status_counts.keys()), "Nombre": list(status_counts.values())})
        st.bar_chart(status_df.set_index("Statut"), height=260)
    with right:
        st.markdown('<div class="section-title">Sentiment client</div>', unsafe_allow_html=True)
        sentiment_order = ["Positif", "Neutre", "Négatif"]
        sentiment_counts = {s: sum(1 for i in engine.interactions if i["sentiment"] == s) for s in sentiment_order}
        sentiment_df = pd.DataFrame({"Sentiment": list(sentiment_counts.keys()), "Interactions": list(sentiment_counts.values())})
        st.bar_chart(sentiment_df.set_index("Sentiment"), height=260)
    c1, c2 = st.columns([1, 1])
    with c1:
        st.markdown('<div class="section-title">Objections principales</div>', unsafe_allow_html=True)
        objections = dict(metrics["top_objections"])
        if objections:
            st.bar_chart(pd.DataFrame({"Objection": list(objections.keys()), "Occurrences": list(objections.values())}).set_index("Objection"), height=230)
        else:
            st.info("Aucune objection détectée pour le moment.")
    with c2:
        st.markdown('<div class="section-title">Recommandations stratégiques</div>', unsafe_allow_html=True)
        for idx, recommendation in enumerate(engine.recommendations, start=1):
            st.markdown(f"**{idx}.** {recommendation}")
        st.caption("Les recommandations sont générées à partir des indicateurs et objections observés.")
    st.markdown('<div class="section-title">Dernières interactions</div>', unsafe_allow_html=True)
    if engine.interactions:
        recent = [{
            "Client": x["customer_name"],
            "Sentiment": x["sentiment"],
            "Intéressé": "Oui" if x["interested"] else "Non",
            "Objections": ", ".join(x["objections"]) or "—",
            "Score d'intérêt": f'{x["interest_score"]:.0%}',
            "Date": x["timestamp"].replace("T", " ")[:19],
        } for x in reversed(engine.interactions[:8])]
        st.dataframe(pd.DataFrame(recent), use_container_width=True, hide_index=True)
    else:
        st.info("Lancez un parcours client pour commencer à alimenter le dashboard.")

# TAB 2 — Journey
with tabs[1]:
    st.markdown('<div class="section-title">Lancer un parcours client de bout en bout</div>', unsafe_allow_html=True)
    st.write("Saisissez un message client. Une transcription issue d'un appel vocal peut également être collée ici ; cette version du prototype traite le texte et ne prétend pas enregistrer d'appel audio.")
    with st.form("journey_form", clear_on_submit=False):
        c1, c2 = st.columns(2)
        with c1:
            customer_name = st.text_input("Nom fictif du client", value="Client Démo", max_chars=60)
            amount = st.number_input("Montant de l'intention (TND)", min_value=1.0, max_value=100000.0, value=float(PRODUCT_PRICE_TND), step=10.0)
        with c2:
            create_payment = st.checkbox("Créer une intention de paiement simulée", value=True)
            simulated_outcome_label = st.selectbox("Résultat simulé après approbation humaine", ["Réussi", "Refusé", "En attente"], index=0)
            outcome_map = {"Réussi": "SUCCESS", "Refusé": "REFUSED", "En attente": "PENDING"}
        customer_message = st.text_area(
            "Message du client",
            value="Je suis intéressé par la formation, mais le prix est un peu élevé. Pouvez-vous m'expliquer le programme et les modalités de paiement ?",
            height=125,
            max_chars=2000,
            help="Données fictives uniquement. Ne saisissez jamais de numéro de carte, CVV, mot de passe ou identifiant bancaire.",
        )
        submitted = st.form_submit_button("Exécuter le workflow multi-agents", type="primary", use_container_width=True)
    if submitted:
        try:
            result = engine.run_journey(
                customer_name=customer_name,
                customer_message=customer_message,
                amount_tnd=amount,
                create_payment=create_payment,
                simulated_outcome=outcome_map[simulated_outcome_label],
            )
            st.session_state.last_result = result
            st.success(f"Workflow exécuté · {result['correlation_id']}")
        except UnsafeInputError as exc:
            engine._add_alert("CRITICAL", "Entrée bloquée : donnée bancaire potentielle", "Le texte a été rejeté et n'a pas été enregistré.", "INPUT-GUARD")
            engine._log("UNSAFE_INPUT_REJECTED", "Input Guard", "Une séquence ressemblant à un numéro de carte a été rejetée ; contenu non conservé.", "INPUT-GUARD")
            st.error(str(exc))
        except (ValueError, TypeError) as exc:
            st.error(str(exc))

    if "last_result" in st.session_state:
        result = st.session_state.last_result
        st.divider()
        st.markdown("#### Résultats du dernier workflow")
        a, b = st.columns(2)
        with a:
            st.markdown("**1 · Voice Sales Agent**")
            st.info(result["sales"]["response"])
            st.caption(f"Offre : {result['sales']['offer']} · {money_tnd(result['sales']['price_tnd'])}")
            st.markdown("**2 · Customer Intelligence Agent**")
            ci = result["intelligence"]
            st.write(f"Sentiment : **{ci['sentiment']}** · Score d'intérêt : **{ci['interest_score']:.0%}**")
            st.write("Intentions : " + ", ".join(ci["intents"]))
            st.write("Motivations : " + ", ".join(ci["motivations"]))
            st.write("Objections : " + (", ".join(ci["objections"]) or "Aucune"))
        with b:
            st.markdown("**3 · Security & Fraud Detection Agent**")
            sec = result["security"]
            level = "error" if sec["severity"] == "CRITICAL" else ("warning" if sec["severity"] == "HIGH" else "success")
            getattr(st, level)(f"Décision : {sec['action']} · Sévérité : {SEVERITY_FR.get(sec['severity'], sec['severity'])}")
            if sec["flags"]:
                for flag in sec["flags"]: st.write(f"- {flag}")
            else:
                st.write("Aucun signal suspect détecté.")
            st.markdown("**4 · Payment Agent**")
            tx = result["transaction"]
            if tx:
                st.write(f"Intention : `{tx['id']}` · Statut : **{STATUS_FR[tx['status']]}**")
                st.caption(tx["note"])
            else:
                st.write("Aucun paiement demandé pour ce parcours.")
        st.markdown("**5 · Financial Data Analyst**")
        an = result["analytics"]
        st.write(f"{an['interactions']} interactions · {an['interested_customers']} clients intéressés · {an['conversion_rate']:.1f} % de conversion · {money_tnd(an['simulated_revenue_tnd'])} de revenu simulé")
        st.markdown("**6 · Business Strategy Agent**")
        for rec in result["recommendations"]: st.markdown(f"- {rec}")

# TAB 3 — Payments
with tabs[2]:
    st.markdown('<div class="section-title">File de validation humaine</div>', unsafe_allow_html=True)
    pending = [tx for tx in reversed(engine.transactions) if tx["status"] == "AWAITING_APPROVAL"]
    if pending:
        st.warning("Aucune intention en attente ne sera simulée avant une décision humaine explicite.")
        for tx in pending:
            with st.container(border=True):
                c1, c2, c3 = st.columns([2, 1, 2])
                with c1:
                    st.markdown(f"**{tx.get('customer_name', tx['customer_id'])}**")
                    st.caption(tx["id"] + " · " + tx["created_at"].replace("T", " ")[:19])
                with c2:
                    st.markdown(f"### {money_tnd(tx['amount_tnd'])}")
                    st.caption("Montant fictif")
                with c3:
                    st.markdown(f"Sécurité : **{SEVERITY_FR.get(tx.get('security_severity', 'LOW'))}**")
                    ap, de = st.columns(2)
                    with ap:
                        if st.button("Approuver la simulation", key=f"approve_{tx['id']}", type="primary", use_container_width=True):
                            try:
                                engine.decide_transaction(tx["id"], True)
                                st.success("Décision enregistrée. Seul le résultat de simulation a été appliqué.")
                                st.rerun()
                            except ValueError as exc: st.error(str(exc))
                    with de:
                        if st.button("Rejeter", key=f"reject_{tx['id']}", use_container_width=True):
                            try:
                                engine.decide_transaction(tx["id"], False)
                                st.success("Intention rejetée par le valideur humain.")
                                st.rerun()
                            except ValueError as exc: st.error(str(exc))
    else:
        st.success("Aucune intention en attente d'approbation.")
    st.divider()
    st.markdown('<div class="section-title">Historique des paiements</div>', unsafe_allow_html=True)
    tx_df = transactions_frame()
    if not tx_df.empty:
        st.dataframe(tx_df, use_container_width=True, hide_index=True)
        csv_download("Exporter les transactions (CSV)", tx_df, "transactions_demo.csv", "dl_tx")
    else:
        st.info("Aucune transaction enregistrée.")
    st.caption("Le Payment Agent ne collecte aucune carte bancaire et n'appelle aucun prestataire de paiement.")

# TAB 4 — Security & audit
with tabs[3]:
    s1, s2, s3 = st.columns(3)
    with s1: st.metric("Alertes", len(engine.alerts))
    with s2: st.metric("Élevées / critiques", alerts_critical)
    with s3: st.metric("Événements tracés", len(engine.audit))
    st.markdown('<div class="section-title">Alertes de sécurité</div>', unsafe_allow_html=True)
    if engine.alerts:
        alert_df = pd.DataFrame([
            {"Date": a["timestamp"].replace("T", " ")[:19], "Sévérité": SEVERITY_FR.get(a["severity"], a["severity"]), "Alerte": a["title"], "Détail": a["detail"], "Flux": a["correlation_id"]}
            for a in reversed(engine.alerts)
        ])
        st.dataframe(alert_df, use_container_width=True, hide_index=True)
        csv_download("Exporter les alertes (CSV)", alert_df, "security_alerts_demo.csv", "dl_alerts")
    else:
        st.info("Aucune alerte détectée.")
    st.markdown('<div class="section-title">Journal d’audit</div>', unsafe_allow_html=True)
    log_df = audit_frame()
    if not log_df.empty:
        st.dataframe(log_df, use_container_width=True, hide_index=True)
        csv_download("Exporter le journal d'audit (CSV)", log_df, "audit_log_demo.csv", "dl_audit")
    else:
        st.info("Aucun événement à afficher.")
    st.markdown('<div class="section-title">Flux de messages entre agents</div>', unsafe_allow_html=True)
    if engine.messages:
        msg_df = pd.DataFrame([
            {"Heure": m["timestamp"].replace("T", " ")[:19], "Émetteur": m["sender"], "Destinataire": m["recipient"], "Type": m["message_type"], "Résumé": m["summary"], "Flux": m["correlation_id"]}
            for m in reversed(engine.messages)
        ])
        st.dataframe(msg_df, use_container_width=True, hide_index=True)
    else:
        st.info("Aucun échange inter-agent pour le moment.")
    with st.expander("Contrôles de sécurité implémentés"):
        st.markdown("""
        - **Moindre privilège :** chaque agent reçoit les seuls champs nécessaires ; l'analyste reçoit des signaux structurés, pas le texte brut du client ; seul le valideur humain peut approuver une intention.
        - **Données sensibles :** les séquences ressemblant à des numéros de carte sont rejetées avant enregistrement.
        - **Prompt injection :** détection de formulations de contournement et blocage de l'intention associée.
        - **Anomalies :** montant supérieur à 1 000 TND et répétition de tentatives déclenchent une revue.
        - **Traçabilité :** décisions, messages inter-agents, alertes et actions importantes sont horodatés.
        - **Paiements :** simulation locale uniquement ; aucune transaction réelle n'est possible.
        """)

# TAB 5 — Architecture
with tabs[4]:
    st.markdown('<div class="section-title">Architecture et responsabilités</div>', unsafe_allow_html=True)
    st.markdown("""
    ```text
    Client (texte / transcription vocale collée)
                    |
                    v
           [Voice Sales Agent]
                    |
                    v
       [Customer Intelligence Agent]
                    |
                    v
     [Security & Fraud Detection Agent]
                    |
                    v
             [Payment Agent]
              /          \\
       [Human approval]  [Blocked]
              |
              v
      [Financial Data Analyst]
              |
              v
       [Business Strategy Agent]
              |
              v
        Dashboard + Audit Log
    ```
    """)
    agent_rows = [
        ("Voice Sales Agent", "Présente l'offre, répond aux questions et enregistre l'interaction."),
        ("Customer Intelligence Agent", "Extrait intentions, sentiment, objections et score d'intérêt."),
        ("Payment Agent", "Crée une intention de paiement fictive et applique uniquement une décision humaine."),
        ("Financial Data Analyst", "Calcule ventes, revenu simulé, statuts et taux de conversion."),
        ("Business Strategy Agent", "Produit des recommandations à partir des objections et indicateurs."),
        ("Security & Fraud Detection Agent", "Détecte injection, montants atypiques et tentatives répétées ; bloque ou demande une revue."),
    ]
    for start in range(0, len(agent_rows), 2):
        cols = st.columns(2)
        for col, (name, role) in zip(cols, agent_rows[start:start+2]):
            with col:
                st.markdown(f'<div class="agent-card"><strong>{name}</strong><br><small>{role}</small></div>', unsafe_allow_html=True)
    st.markdown("#### Contrats d'échange")
    st.markdown("Chaque agent reçoit un objet structuré et transmet un message typé (`CUSTOMER_CONTEXT`, `CUSTOMER_SIGNALS`, `SECURITY_DECISION`, `PAYMENT_INTENT`, `FINANCIAL_INSIGHTS`, `RECOMMENDATIONS`) avec un identifiant de corrélation. Les erreurs de validation interrompent le parcours avant la création de l'intention.")
    st.markdown("#### Limites connues du prototype")
    st.markdown("- L'analyse du langage est heuristique et locale ; elle ne remplace pas un modèle NLP/LLM en production.\n- L'interface accepte du texte ou une transcription vocale fournie par l'utilisateur, mais ne capture pas l'audio en direct.\n- Les données résident en mémoire de session et ne constituent pas une base de production.\n- Le module paiement ne se connecte à aucun Sandbox externe : le statut est une simulation contrôlée.")

st.markdown('<div class="footer-note">TECHX ENIT × ENICarthage · Prototype de hackathon · Données 100 % fictives · Aucun paiement réel · Version locale démontrable</div>', unsafe_allow_html=True)
