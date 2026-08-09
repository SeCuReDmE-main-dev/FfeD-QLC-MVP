# FfeD-QLC: parcours professionnel et preparation Azure

**Statut:** recherche et design pedagogique. Aucun compte, identite, secret, donnee d'etudiant ou ressource Azure n'est cree par ce document.

## Intention

FfeD-QLC est un capstone de fin de parcours. L'etudiant arrive avec des acquis de 5e secondaire, les consolide au college, puis produit au niveau universitaire une preuve portable de sa capacite a concevoir, tester, expliquer et proteger une petite frontiere de systeme.

Google peut rester une surface utile d'apprentissage, de collaboration ou de brouillon. Il ne doit pas devenir le depot unique de la competence ni un verrou technique. Le chemin de sortie est un ensemble d'artefacts versionnes, lisibles et transportables.

## Deux trajectoires, une meme preuve

| Parcours | Surface de travail | Resultat exige |
| --- | --- | --- |
| OpenAI | Codex, GitHub, tests locaux, revue humaine | Code, contrats, tests, journal de decisions et portfolio exportable. |
| Microsoft | Copilot, Azure, exploitation gouvernee | Les memes artefacts, plus une evaluation de disponibilite cloud, d'identite, de cout et d'operations. |

Le programme ne donne pas une note a un fournisseur. Il demande a l'etudiant de montrer ce qu'il sait expliquer, reproduire et verifier.

## Progression scolaire

| Palier | Travail de l'etudiant | Role du professeur |
| --- | --- | --- |
| **5e secondaire** | Logique, Python, securite de base, versionnage et premieres preuves de travail. | Installe les fondations, autorise les environnements, protege le rythme d'apprentissage et valide que l'IA explique plutot qu'elle remplace le raisonnement. |
| **College** | Graphes, reseaux, cryptographie appliquee, tests, modelisation de menaces et missions red/blue synthetiques. | Evalue la rigueur: choix de methode, experience reproductible, journal de preuves, limites et qualite de l'explication technique. |
| **Universite / capstone** | Orbe de laboratoire, contrats de donnees, analyse d'attaque, portfolio et dossier de migration professionnel. | Supervise une revue de systeme: architecture, gouvernance, reproductibilite, risque/ethique, portefeuille de preuves et readiness professionnel. |

Chaque palier ajoute un artefact selectionne au portfolio. Rien ne copie automatiquement l'historique complet d'un compte ou d'un depot.

## Portable Evidence Bundle

`portable_evidence_bundle.v1` est le pont entre apprentissage et emploi. Il contient seulement les references approuvees:

- URL du depot, branche/ref et commit SHA;
- source selectionnee et lockfiles;
- resultats de tests, fixtures synthetiques et hashes;
- SBOM si le contexte le justifie;
- schema, contrats d'API et guide de reproduction;
- decision log, threat model et limites connues;
- proprietaire, consentement, visibilite et date d'expiration.

Il exclut toujours les secrets, `.env`, cookies, tokens, donnees personnelles, telemetrie cachee et contenu de depot non selectionne.

## Readiness Azure, sans deploiement implicite

Un `cloud_migration_readiness.v1` documente une eventualite de migration. Avant une mise en production, il exige:

1. une evaluation de portabilite et de compatibilite;
2. une architecture dev/test/prod isolee;
3. un modele d'identite et de roles a privileges minimaux;
4. une decision explicite sur stockage, journalisation, sauvegarde et reprise;
5. une estimation de cout, un responsable, un plan de retour et une approbation professorale ou organisationnelle.

Microsoft Entra ID, RBAC, managed identities, GitHub Actions avec federation OIDC, Key Vault, Blob Storage, Container Apps/App Service et Azure Monitor sont des options de TDR a comparer. Ils ne sont ni requis aujourd'hui ni configures par FfeD-QLC.

## Contrat pedagogique

L'IA aide l'etudiant a observer, expliquer, proposer un test et signaler une limite. Codex et Copilot doivent rester encadres par les memes preuves: fixtures synthetiques, sortie structuree, tests rejouables, citation de la decision humaine. Un professeur peut accepter, suspendre ou rejeter une preuve. L'outil ne certifie jamais la competence seul.

`teacher_pathway_governance.v1` doit rendre visibles les droits de configuration, artefacts a approuver, rubriques, formation enseignant, charge prevue et voies d'escalade de chaque palier. Le professeur ne devient jamais un administrateur opaque du compte de l'etudiant, et aucune IA ne prend une decision d'evaluation a sa place.

## Criteres d'acceptation futurs

- un etudiant peut exporter un dossier sans dependance Google obligatoire;
- le dossier se reproduit depuis un commit et des fixtures;
- une revue explique ce qui est confirme, infere et encore hypothetique;
- une migration Azure reste une option planifiee et budgetee, jamais un clic opaque;
- les donnees reelles et les secrets demeurent hors du portfolio et hors des invites IA.

## Sources a utiliser dans la phase Deep Research

- [Azure Well-Architected Framework](https://learn.microsoft.com/en-us/azure/well-architected/what-is-well-architected-framework)
- [Azure Cloud Adoption Framework: prepare workloads for cloud](https://learn.microsoft.com/en-us/azure/cloud-adoption-framework/migrate/prepare-workloads-cloud)
- [Azure Cloud Adoption Framework: plan migration](https://learn.microsoft.com/en-us/azure/cloud-adoption-framework/migrate/plan-migration)
- [Azure security design principles](https://learn.microsoft.com/en-au/azure/well-architected/security/principles)
- [Azure IAM architecture strategies](https://learn.microsoft.com/en-us/azure/well-architected/security/identity-access)
