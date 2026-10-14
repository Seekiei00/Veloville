# VéloVille — Plateforme de valorisation des données

À compléter : présentation du projet, prérequis, installation, lancement de
l'API et du front, exécution des tests, liens vers la documentation
(docs/), auteur et version.


## Choix écoresponsables

- **Pagination côté serveur** : l'API ne renvoie qu'une page (20 lignes par
  défaut, 100 au maximum). On ne transfère jamais toute une table.
- **Pas de rafraîchissement automatique** : le front n'appelle l'API que
  lorsque l'utilisateur agit. Sur l'écran Indicateurs, les calculs ne sont
  relancés qu'au clic sur « Actualiser ».
- **Cache** : la liste des communes (qui change rarement) est gardée une
  heure avec `st.cache_data(ttl=3600)`.
- **Calculs en SQL** : les indicateurs sont calculés par PostgreSQL
  (`GROUP BY`, `count`, `avg`) ; seul le résultat est envoyé.
- **Index** sur les colonnes utilisées dans les filtres.
- **Peu de dépendances** : j'ai retiré de `requirements.txt` les paquets
  inutiles (mypy, black, ruff, psycopg2…).
- **Purge** des vieux trajets avec `scripts/purger_trajets.py` (RGPD,
  13 mois), ce qui limite aussi la taille de la base.