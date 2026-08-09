import type { Language } from "./types";

const copy = {
  en: {
    title: "Vigil Orb Laboratory", subtitle: "Supervised cryptography, geometry, and defensive evidence",
    prerequisites: "Prerequisites", orb: "Orb Studio", mission: "Mission", defense: "Defense", evidence: "Evidence", professor: "Professor",
    gateway: "Gateway", connected: "Ready", disconnected: "Unavailable", start: "Open supervised session",
    fingerprint: "Pseudonymous fingerprint", provider: "AI route", role: "Role", project: "Orb project", create: "Create project",
    noHistory: "No previous metrics are required. Vigil starts with a local baseline.", labs: "Nine-laboratory route",
    run: "Start lab", execute: "Run allowed action", report: "Build Vigil report", decision: "Professor decision",
    proof: "Evidence ledger", limitation: "Limits remain part of the result.", download: "Build portfolio view",
    boundary: "Tenebris boundary", synthetic: "Synthetic fixtures only", noShell: "No shell or external target",
    teacherOwns: "The professor owns the final decision", geometryClaim: "Geometry is not presented as key material",
    adult: "Student 18+", minor: "Student minor", createFirst: "Create a supervised project before starting a mission.",
    allowed: "Allowed action", fixture: "Fixture", review: "Review", teacherRequired: "Professor required", evidenceGate: "Evidence gate",
    portfolioSummary: "SHA-256 references, review decisions, claim boundaries, and Azure readiness remain explicit.",
    noReport: "No Vigil report yet", finishFirst: "Complete an allowlisted mission action first.",
    vigilDecides: "Vigil recommends. The professor decides.", openTeacher: "Open teacher session", note: "Evidence-based review note",
    limits: "Tenebris limits", limitsHelp: "Limits can be reduced for this project. Alpha maximums cannot be exceeded.",
    retries: "Mission retries", trace: "Geometry trace steps", apply: "Apply bounded profile", enforced: "Profile enforced",
  },
  fr: {
    title: "Laboratoire d'orbe Vigil", subtitle: "Cryptographie, geometrie et preuves defensives supervisees",
    prerequisites: "Prerequis", orb: "Studio d'orbe", mission: "Mission", defense: "Defense", evidence: "Preuves", professor: "Professeur",
    gateway: "Gateway", connected: "Pret", disconnected: "Indisponible", start: "Ouvrir la session supervisee",
    fingerprint: "Empreinte pseudonyme", provider: "Route IA", role: "Role", project: "Projet d'orbe", create: "Creer le projet",
    noHistory: "Aucune metrique anterieure n'est requise. Vigil commence par une base locale.", labs: "Parcours de neuf laboratoires",
    run: "Demarrer", execute: "Executer l'action autorisee", report: "Produire le rapport Vigil", decision: "Decision professorale",
    proof: "Registre des preuves", limitation: "Les limites font partie du resultat.", download: "Construire la vue portfolio",
    boundary: "Limites Tenebris", synthetic: "Fixtures synthetiques uniquement", noShell: "Aucun shell ni cible externe",
    teacherOwns: "Le professeur conserve la decision finale", geometryClaim: "La geometrie n'est pas presentee comme materiau de cle",
    adult: "Etudiant adulte", minor: "Etudiant mineur", createFirst: "Creez un projet supervise avant de lancer une mission.",
    allowed: "Action autorisee", fixture: "Fixture", review: "Revision", teacherRequired: "Professeur requis", evidenceGate: "Porte de preuve",
    portfolioSummary: "Les references SHA-256, decisions, limites d'affirmation et la preparation Azure restent explicites.",
    noReport: "Aucun rapport Vigil", finishFirst: "Completez d'abord une action de mission autorisee.",
    vigilDecides: "Vigil recommande. Le professeur decide.", openTeacher: "Ouvrir une session professeur", note: "Note de revision fondee sur les preuves",
    limits: "Limites Tenebris", limitsHelp: "Ces limites peuvent etre reduites pour le projet. Les maximums alpha restent fixes.",
    retries: "Reprises de mission", trace: "Etapes de trace geometrique", apply: "Appliquer le profil borne", enforced: "Profil applique",
  },
  es: {
    title: "Laboratorio de orbe Vigil", subtitle: "Criptografia, geometria y evidencia defensiva supervisadas",
    prerequisites: "Requisitos", orb: "Estudio de orbe", mission: "Mision", defense: "Defensa", evidence: "Evidencia", professor: "Profesor",
    gateway: "Gateway", connected: "Listo", disconnected: "No disponible", start: "Abrir sesion supervisada",
    fingerprint: "Huella seudonima", provider: "Ruta IA", role: "Rol", project: "Proyecto de orbe", create: "Crear proyecto",
    noHistory: "No se requieren metricas previas. Vigil comienza con una linea base local.", labs: "Ruta de nueve laboratorios",
    run: "Iniciar", execute: "Ejecutar accion permitida", report: "Crear informe Vigil", decision: "Decision docente",
    proof: "Registro de evidencia", limitation: "Los limites forman parte del resultado.", download: "Construir vista de portafolio",
    boundary: "Limites Tenebris", synthetic: "Solo fixtures sinteticas", noShell: "Sin shell ni objetivo externo",
    teacherOwns: "El profesor conserva la decision final", geometryClaim: "La geometria no se presenta como material de clave",
    adult: "Estudiante adulto", minor: "Estudiante menor", createFirst: "Cree un proyecto supervisado antes de iniciar una mision.",
    allowed: "Accion permitida", fixture: "Fixture", review: "Revision", teacherRequired: "Profesor requerido", evidenceGate: "Puerta de evidencia",
    portfolioSummary: "Las referencias SHA-256, decisiones, limites de afirmacion y preparacion Azure siguen explicitas.",
    noReport: "Aun no hay informe Vigil", finishFirst: "Complete primero una accion de mision permitida.",
    vigilDecides: "Vigil recomienda. El profesor decide.", openTeacher: "Abrir sesion docente", note: "Nota de revision basada en evidencia",
    limits: "Limites Tenebris", limitsHelp: "Los limites pueden reducirse para este proyecto. No se pueden superar los maximos alfa.",
    retries: "Reintentos de mision", trace: "Pasos de traza geometrica", apply: "Aplicar perfil limitado", enforced: "Perfil aplicado",
  },
} as const;

export function t(language: Language) {
  return copy[language];
}

const labs = {
  en: ["Primitive boundaries", "Inspect FQLC1", "Metadata pressure", "Geometric permutation", "Apollonian trace", "Bounded red mission", "Blue correction", "Suite handoff", "Capstone orb"],
  fr: ["Frontieres des primitives", "Inspecter FQLC1", "Pression des metadonnees", "Permutation geometrique", "Trace apollonienne", "Mission rouge bornee", "Correction bleue", "Handoff de la suite", "Orbe finale"],
  es: ["Limites de las primitivas", "Inspeccionar FQLC1", "Presion de metadatos", "Permutacion geometrica", "Traza apoloniana", "Mision roja limitada", "Correccion azul", "Handoff de la suite", "Orbe final"],
} as const;

export function labTitle(language: Language, labId: string, fallback: string) {
  const index = Number(labId.slice(-2)) - 1;
  return labs[language][index] ?? fallback;
}
