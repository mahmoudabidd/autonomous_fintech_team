# Pitch de démonstration — 90 secondes

## Problème

Dans un parcours FinTech classique, la relation client, le paiement, l'analyse commerciale et la sécurité sont souvent séparés. Les informations circulent mal et une action financière peut être difficile à contrôler ou à expliquer.

## Solution

**The Autonomous FinTech Team** coordonne six agents spécialisés dans un workflow unique. Le Sales Agent répond au prospect ; Customer Intelligence structure ses intentions, motivations, objections et signaux de satisfaction ; Security vérifie les risques ; Payment crée une intention simulée ; Financial Data Analyst actualise les indicateurs ; Business Strategy transforme les résultats en recommandations.

## Démonstration

1. Un prospect pose une question sur une formation fictive.
2. Les agents Sales et Customer Intelligence répondent et qualifient son intérêt.
3. Security inspecte le message, le montant et les tentatives récentes.
4. Payment crée une intention, mais ne l'exécute pas : le statut reste « Approbation requise ».
5. Un opérateur humain approuve ou rejette la simulation.
6. Le dashboard met à jour les statuts, le revenu simulé, la conversion et les recommandations.
7. Une tentative de prompt injection déclenche un blocage et une alerte traçable.

## Choix techniques

- Python et Streamlit pour un prototype local rapidement démontrable.
- Agents séparés par responsabilité, avec des entrées/sorties structurées.
- Orchestration séquentielle et identifiant de corrélation pour suivre chaque parcours.
- Données synthétiques préchargées et exports CSV pour l'analyse.
- Règles de sécurité déterministes pour que les contrôles critiques restent explicables et ne dépendent pas d'une réponse générée.

## Valeur ajoutée

Le système relie le parcours client, le suivi de paiement, le pilotage commercial et la sécurité dans une même démonstration. Chaque décision importante est consultable, et les recommandations s'appuient sur les objections et résultats observés.

## Sécurité et limites

Aucun paiement réel n'est possible. Les intentions attendent une validation humaine ; les instructions de contournement sont bloquées ; les données de paiement sensibles sont rejetées ; les actions et échanges sont journalisés. La version actuelle utilise une analyse textuelle heuristique et un traitement de transcription collée plutôt qu'une reconnaissance vocale en direct. Elle constitue un MVP de démonstration, pas un système bancaire de production.

## Perspectives

Ajouter un LLM avec sorties JSON contraintes pour améliorer la compréhension du langage, une API de paiement Sandbox autorisée, une authentification réelle des validateurs, une base de données persistante avec contrôle d'accès, une capture vocale avec consentement, et des modèles supervisés pour améliorer la détection d'anomalies — tout en conservant la validation humaine et les journaux d'audit.
