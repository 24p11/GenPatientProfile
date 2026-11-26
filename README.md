# GenPatientProfile

Bibliothèque Python de génération de profils patients fictifs et de scénarios cliniques structurés à partir de données PMSI.

![Python](https://img.shields.io/badge/python-3.12+-blue)
[![PyPI](https://img.shields.io/pypi/v/GenPatientProfile)](https://pypi.org/project/GenPatientProfile/)
[![License: CC BY-NC-SA 4.0](https://img.shields.io/badge/License-CC%20BY--NC--SA%204.0-green.svg)](https://creativecommons.org/licenses/by-nc-sa/4.0/)

## Rôle du projet

GenPatientProfile prend en charge la préparation des données nécessaires à une génération de comptes rendus :

1. chargement et contrôle des données PMSI et des référentiels locaux ;
2. échantillonnage ou sélection de profils patients ;
3. construction des scénarios cliniques ;
4. préparation des prompts et préfixes destinés aux modèles de langage ;
5. écriture des scénarios dans un fichier Parquet.

Les appels aux modèles de langage et la production des comptes rendus sont gérés par le projet [GenReports](https://github.com/24p11/GenReports).

## Installation

Depuis PyPI :

```bash
python -m pip install GenPatientProfile
```

Avec `uv` :

```bash
uv add GenPatientProfile
```

Depuis les sources :

```bash
git clone https://github.com/24p11/GenPatientProfile.git
cd GenPatientProfile
uv sync --group dev
```

La distribution se nomme `GenPatientProfile` et le module Python s'importe sous le nom `genpatientprofile`.

## Pipelines disponibles

| Pipeline | Origine fonctionnelle | Fonction |
|---|---|---|
| `pmsi_sampling` | CHU de Brest | Tirage pondéré de séjours à partir d'extractions PMSI/SNDS, puis construction de scénarios. |
| `profile_generation` | AP-HP | Sélection de profils PMSI, enrichissement clinique, règles ATIH, fiches de codes et préparation de prompts. |

Les anciens noms `brest` et `aphp` restent temporairement acceptés comme alias dépréciés.

## Configuration

Les chemins sont fournis dans un fichier YAML local, par exemple `config/servers.yaml` :

```yaml
pipelines:
  pmsi_sampling:
    data:
      input: "data/pmsi_sampling"
      output: "scenarios/pmsi_sampling"

  profile_generation:
    data:
      input: "data/profile_generation"
      output: "scenarios/profile_generation"
      referentials: "data/profile_generation/referentials"
```

Un exemple est disponible dans [`genpatientprofile/config/servers.example.yaml`](genpatientprofile/config/servers.example.yaml).

## Utilisation

### PMSI sampling

```python
from genpatientprofile import generate

scenarios = generate(
    pipeline_name="pmsi_sampling",
    n_sejours=500,
    n_ccam=1,
    n_das=5,
    ghm5_pattern=None,
    config_file="config/servers.yaml",
)
```

### Profile generation en une étape

Le jeu de prompts `default` correspond au workflow en une étape :

```python
from genpatientprofile import generate

scenarios = generate(
    pipeline_name="profile_generation",
    n_sejours=500,
    config_file="config/servers.yaml",
    prompt_workflow="one_stage",
    prompt_set="default",
)
```

### Profile generation en deux étapes

Le jeu `old` contient les prompts historiques et prend en charge les workflows en une et deux étapes :

```python
scenarios = generate(
    pipeline_name="profile_generation",
    n_sejours=500,
    config_file="config/servers.yaml",
    prompt_workflow="two_stage",
    prompt_set="old",
)
```

### Jeu de prompts externe

Un jeu personnalisé peut être utilisé sans modifier le paquet :

```python
scenarios = generate(
    pipeline_name="profile_generation",
    n_sejours=500,
    config_file="config/servers.yaml",
    prompt_workflow="one_stage",
    prompt_dir="/chemin/vers/mes_prompts",
)
```

Structure minimale :

```text
mes_prompts/
├── manifest.yaml
├── prefix.txt
└── one_stage/
    ├── medical_inpatient.txt
    └── ...
```

Exemple de manifeste :

```yaml
name: mes_prompts
version: "1.0"
workflows:
  one_stage: true
  two_stage: false
```

Le nom, la version, la source et l'empreinte du jeu de prompts sont ajoutés aux scénarios. Lorsqu'un dossier externe est utilisé, une copie est conservée sous `prompts_snapshot/` dans le répertoire de sortie.

## Données et référentiels

Les données PMSI, les référentiels CIM-10/CCAM/GHM et les bibliothèques de fiches ne sont pas distribués dans ce dépôt ni dans le paquet PyPI. Ils doivent être obtenus auprès des sources autorisées et placés dans les répertoires indiqués par la configuration.

Les éléments suivis dans Git sont uniquement le code, les tests, les modèles de prompts et le fichier de règles `templates/regles_atih.yml`. Les dossiers `data/`, `scenarios/`, `reports/` et les configurations contenant des secrets sont ignorés par Git.

Pour `profile_generation`, les bibliothèques facultatives de fiches de codes peuvent être placées sous :

```text
<referentials>/cards_library/
<referentials>/cards_library_categories/
```

## Fichiers attendus et schémas

Les deux pipelines nécessitent des fichiers locaux :

- `pmsi_sampling` attend `PMSI_DP.csv`, `PMSI_CCAM_DP.csv`, `PMSI_DAS.csv`, `PMSI_DMS.csv`, `ALL_CLASSIF_PMSI.csv`, `ALL_CIM10.csv` et `ALL_CCAM.csv`, ou les Parquet convertis correspondants ;
- `profile_generation` attend un profil `scenarios_*.parquet` ou `scenarios_*.pq`, un fichier `bn_pmsi_related_diag_*.csv`, un fichier `bn_pmsi_procedures_*.csv` et le répertoire de référentiels configuré.

Le contrat détaillé — noms de colonnes, types, séparateurs, alias historiques et arborescence des référentiels — est disponible dans [la documentation des données d’entrée](https://github.com/24p11/GenPatientProfile/blob/main/docs/input-data-contract.md).

## Sorties

La fonction `generate()` renvoie un `polars.DataFrame`. Si un répertoire `data.output` est configuré, elle écrit également un fichier :

```text
<pipeline>_scenarios_<nombre>_<horodatage>.parquet
```

## Architecture

```text
genpatientprofile/
├── core.py                 # orchestration publique generate()
├── registry.py             # pipelines et alias
├── base.py                 # interface commune
├── fictive.py              # orchestration de l'échantillonnage
├── scenario.py             # orchestration du formatage
├── sites/
│   ├── brest/              # implémentation pmsi_sampling
│   └── aphp/               # implémentation profile_generation
└── config/
    └── servers.example.yaml
```

## Développement et tests

```bash
uv sync --group dev
uv run pytest
uv build
```

La CI exécute les tests sous Python 3.12 et 3.13. Les publications PyPI sont réalisées depuis les releases GitHub au moyen d'un trusted publisher.

## Contribuer

Pour ajouter un pipeline :

1. créer un module sous `genpatientprofile/sites/` ;
2. implémenter `BasePipeline` ;
3. enregistrer la classe dans `genpatientprofile/registry.py` ;
4. ajouter les tests et documenter les données attendues.

## Licence

Ce projet est distribué sous la licence [Creative Commons Attribution-NonCommercial-ShareAlike 4.0 International](LICENSE.md).
