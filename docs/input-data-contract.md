# Contrat des données d'entrée

Ce document décrit le contrat attendu par GenPatientProfile 0.1.x. Les types indiqués sont des types logiques : `string`, `integer`, `float`, `boolean` et `list[string]`. Les codes CIM-10, CCAM et GHM doivent être stockés comme chaînes afin de préserver les zéros et caractères significatifs.

Les données et référentiels décrits ici ne sont pas distribués avec le dépôt ni avec le paquet PyPI.

## Règles communes

- Les noms de colonnes sont sensibles à la casse.
- Les CSV du pipeline `pmsi_sampling` sont séparés par `;` et lus en `latin-1`.
- Les CSV du pipeline `profile_generation` sont séparés par `;`, sauf mention contraire, et lus en UTF-8.
- Les valeurs numériques utilisées comme poids doivent être positives ou nulles ; un jeu de poids dont la somme est nulle ne permet pas l'échantillonnage.
- Les fichiers Parquet doivent conserver les types indiqués ci-dessous.
- Les valeurs manquantes sont représentées par une valeur nulle. Dans les listes de diagnostics, `NA`, `nan` et la chaîne vide sont ignorés.

## Pipeline `pmsi_sampling`

Le répertoire `pipelines.pmsi_sampling.data.input` doit contenir les sept CSV ci-dessous, ou les fichiers Parquet déjà convertis. Lorsqu'un Parquet manque, GenPatientProfile lit le CSV correspondant et crée le Parquet attendu.

| CSV source | Parquet utilisé | Colonnes obligatoires et types logiques |
|---|---|---|
| `PMSI_DP.csv` | `dp.parquet` | `AGE: string`, `SEXE: string`, `GHM5: string`, `DP: string`, `P_DP: float` |
| `PMSI_CCAM_DP.csv` | `ccam.parquet` | `GHM5: string`, `DP: string`, `CCAM: string`, `P_CCAM: float` |
| `PMSI_DAS.csv` | `das.parquet` | `GHM5: string`, `AGE: string`, `SEXE: string`, `DP: string`, `DAS: string`, `P_DAS: float` |
| `PMSI_DMS.csv` | `dms.parquet` | `GHM5: string`, `DMS_P25: float`, `DMS_P50: float`, `DMS_P75: float` |
| `ALL_CLASSIF_PMSI.csv` | `rghm.parquet` | `champ: string`, `version: string`, `type_code: string`, `code: string`, `lib: string` |
| `ALL_CIM10.csv` | `cim10.parquet` | `en_cours: integer`, `code: string`, `liblong: string` |
| `ALL_CCAM.csv` | `ccam_ref.parquet` | `en_cours: integer`, `code: string`, `liblong: string` |

Contraintes supplémentaires :

- `P_DP`, `P_CCAM` et `P_DAS` sont des poids d'échantillonnage ;
- `DMS_P25 <= DMS_P50 <= DMS_P75` est attendu ;
- `en_cours = 1` identifie les libellés actifs ;
- le référentiel GHM utilisé par le code correspond aux lignes `champ = "mco"`, `version = "v2024"` et `type_code = "racine"`.

Exemple minimal pour `PMSI_DP.csv` :

```csv
AGE;SEXE;GHM5;DP;P_DP
[40-50[;2;06C04;K35.8;0.0125
```

## Pipeline `profile_generation` : données PMSI

Le répertoire `pipelines.profile_generation.data.input` contient trois familles de fichiers. Si plusieurs fichiers correspondent à un motif, le plus récemment modifié est sélectionné.

| Rôle | Motifs acceptés | Format |
|---|---|---|
| Profils | `scenarios_*.parquet`, `scenarios_*.pq` | Parquet |
| Table statistique de relations DP–DAS | `bn_pmsi_related_diag_*.csv` | CSV `;`, UTF-8 |
| Actes | `bn_pmsi_procedures_*.csv` | CSV `;`, UTF-8 |

### Profils

Les noms canoniques sont recommandés. Les alias historiques sont encore normalisés au chargement.

| Colonne canonique | Alias historique | Type logique | Statut | Rôle |
|---|---|---|---|---|
| `drg_parent_code` | `racine` | string | obligatoire | Racine de GHM. |
| `icd_primary_code` | `diag2` | string | obligatoire | Diagnostic principal CIM-10. |
| `sexe` | — | integer ou string convertible | obligatoire | `1` masculin, `2` féminin dans les référentiels de noms. |
| `age2` | `agean` | integer | conditionnel | Âge exact. Obligatoire si `cage` est absente. |
| `cage` | `age` dans l'ancien format | string | conditionnel | Classe d'âge, par exemple `[40-50[`. Utilisée si `age2` est absente. |
| `los` | `duree` | integer | recommandé | Durée du séjour. Si elle est nulle, les statistiques de racine sont utilisées. |
| `admission_type` | `mode_hospit` | string | obligatoire | Type d'hospitalisation, notamment `HC` ou `HP`. |
| `admission_mode` | `mode_entree` | string | obligatoire | Mode d'entrée, par exemple `URGENCES`. |
| `discharge_disposition` | `mode_sortie` | string | obligatoire | Mode de sortie. |
| `case_management_type` | `mdp` | string | recommandé | Motif ou diagnostic relié utilisé par les règles de prise en charge. |
| `icd_secondary_code` | `diagnostic_associes` | list[string] ou string | facultatif | Codes DAS. Une chaîne peut contenir des codes séparés par des espaces ou `;`. |
| `nb` | `n` | integer ou float | facultatif | Poids d'échantillonnage du profil ; poids uniforme si absent. |
| `nb_associated` | `nbda` | integer | facultatif | Nombre de diagnostics associés, conservé comme métadonnée. |
| `specialty` | — | string | facultatif | Service ; dérivé du référentiel de spécialités si absent. |
| `drg_parent_description` | — | string | facultatif | Libellé de racine ; joint depuis le référentiel si absent. |
| `los_mean`, `los_sd` | — | float | facultatif | Statistiques de durée ; jointes depuis le référentiel si absentes. |
| `taille_cm` / `height_cm` | — | float | facultatif | Taille clinique ajoutée au prompt si présente. |
| `poids_kg` / `weight_kg` | — | float | facultatif | Poids clinique ajouté au prompt. La colonne technique `poids` n'est jamais utilisée comme poids clinique. |
| `imc` / `bmi` | — | float | facultatif | IMC ajouté au prompt. |
| `tabac` / `tobacco_status` | — | string | facultatif | Statut tabagique ajouté au prompt. |
| `alcool` / `alcohol_status` | — | string | facultatif | Consommation d'alcool ajoutée au prompt. |

Les autres colonnes sont conservées lorsqu'elles traversent la construction du scénario, mais ne font pas partie du contrat minimal.

### Table statistique de relations DP–DAS

Cette table ne décrit pas directement les DAS déjà attachés à chaque ligne du fichier de profils. Elle contient des relations statistiques entre profils et diagnostics secondaires, conditionnées notamment par le diagnostic principal et la racine de GHM. Elle est actuellement chargée et classée par le pipeline, mais le tirage de DAS supplémentaires est désactivé (`add_secondary=False`). Les DAS utilisés dans les scénarios restent donc ceux portés par `icd_secondary_code` (alias `diagnostic_associes`) dans `scenarios_*`.


| Colonne canonique | Alias historique | Type logique | Statut |
|---|---|---|---|
| `icd_primary_code` | `diag` | string | obligatoire |
| `drg_parent_code` | `racine` | string | obligatoire |
| `icd_secondary_code` | `das` | string | obligatoire |
| `cage2` | — | string | recommandé |
| `sexe` | — | integer | recommandé |
| `nb` | `nb_situations` | integer ou float | recommandé ; poids d'échantillonnage |
| `icd_primary_parent_code` | `categ_cim` | string | facultatif |
| `case_management_type` | `mdp` | string | facultatif |
| `admission_type` | `mode_hospit` | string | facultatif |
| `admission_mode` | `mode_entree` | string | facultatif |
| `discharge_disposition` | `mode_sortie` | string | facultatif |

### Actes

| Colonne canonique | Alias historique | Type logique | Statut |
|---|---|---|---|
| `procedure` | `acte` | string | obligatoire |
| `drg_parent_code` | `racine` | string | obligatoire |
| `icd_primary_code` | `diag` | string | obligatoire |
| `cage2` | — | string | recommandé |
| `sexe` | — | integer | recommandé |
| `nb` | `nb_situations` | integer ou float | recommandé ; poids d'échantillonnage |
| `icr` | — | integer ou float | facultatif |
| `admission_type` | `mode_hospit` | string | facultatif |

## Pipeline `profile_generation` : référentiels

Le répertoire `pipelines.profile_generation.data.referentials` doit conserver les noms et l'arborescence suivants.

### Tables principales

| Chemin | Format | Colonnes minimales attendues |
|---|---|---|
| `CIM_ATIH_2025/LIBCIM10MULTI.parquet` | Parquet | `icd_code: string`, `icd_code_description: string` |
| `cim_synonymes.csv` | CSV `,` | `dictionary_keys: string`, `code: string` |
| `stat_racines.parquet` | Parquet | `racine: string`, `dms: float`, `dsd: float` |
| `ghm_rghm_regroupement_2024.parquet` | Parquet | `racine: string`, `libelle_racine: string` |
| `Affections chroniques.parquet` | Parquet | `code: string`, `chronic: integer`, `libelle: string` |
| `cma.csv` | CSV `,` | `icd_code: string` |
| `prenoms_nom_sexe.csv` | CSV `;` | `prenom: string`, `nom: string`, `sexe: integer` |
| `chu` | texte sans en-tête | une colonne contenant le nom de l'établissement |
| `dictionnaire_spe_racine.parquet` | Parquet | `racine: string`, `lib_spe_uma: string`, `ratio_spe_racine: float` |
| `ccam_actes_2024.parquet` | Parquet | `code: string`, `libelle_long: string` |
| `REFERENTIEL_METHODE_DIM_CANCER_20140411__CODES_CIM-10_CANCER.parquet` | Parquet | `CIM10: string` |
| `Tableau récapitulatif traitement cancer__Feuille_1.parquet` | Parquet | `Code CIM`, `Localisation`, `Type Histologique`, `Stade`, `TNM`, `Marqueurs Tumoraux`, `Traitement`, `Protocole de Chimiothérapie` : string |
| `ponderation_code_categ.csv` | CSV `;`, virgule décimale | `diag: string`, `ponderation: float` |
| `exclusions` | CSV `,` | `ga: string`, `lib_ga: string` |

Les colonnes supplémentaires de ces tables sont autorisées et conservées par Polars.

### Listes de codes

Chacun des fichiers suivants est un CSV séparé par `;` comportant au minimum une colonne `code: string`. Une colonne descriptive supplémentaire est autorisée.

```text
icd_codes_chronic_attack.csv
procedure_botulic_toxine.csv
icd_codes_prophylactic_intervention.csv
attention_artificial_openings_external_prosthetic_device.csv
icd_codes_iron_deficiency_anemia.csv
icd_codes_sessions.csv
icd_codes_diabetes_chronic.csv
icd_codes_spontaneous_vertex_delivery.csv
icd_codes_liveborn_infants.csv
icd_codes_medical_abortion.csv
icd_codes_legal_abortion.csv
icd_codes_supervision.csv
icd_codes_supervision_chronic_disease.csv
icd_codes_surgical_followup.csv
icd_codes_supervision_pregnancy.csv
icd_codes_supervision_post_partum.csv
icd_codes_cardic_vascular_implants.csv
icd_codes_overnight_study.csv
icd_codes_sensitization_tests.csv
icd_codes_preoperative_assessment.csv
icd_codes_family_history.csv
icd_codes_personnel_history.csv
```

### Fiches de codes facultatives

Les fiches de codes ne sont pas obligatoires. Lorsqu'elles existent, elles sont recherchées dans :

```text
<referentials>/cards_library/
<referentials>/cards_library_categories/
```

Chaque bibliothèque contient un fichier `index.csv` avec une colonne `code` et une colonne `fichier` (ou l’ancien nom `filepath`) qui associe les codes aux fichiers Markdown. En l'absence de ces répertoires, la génération continue sans enrichissement par fiches.

## Contrôles de reproductibilité recommandés

Avant une génération, conserver avec le run :

1. la version de GenPatientProfile ;
2. le fichier de configuration sans secrets ;
3. le nom, la taille, la date et une empreinte SHA-256 de chaque fichier d'entrée ;
4. le schéma Polars de chaque table ;
5. le jeu de prompts, sa version et son empreinte ;
6. la graine aléatoire lorsqu'elle est exposée par le workflow appelant.

Le chargeur choisissant le fichier le plus récent pour chaque motif `profile_generation`, il est recommandé de ne conserver qu'un fichier actif de chaque famille dans le répertoire d'entrée d'un run reproductible.

