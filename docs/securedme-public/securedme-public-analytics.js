/* SecuredMe public analytics v1. Explicit consent, public enums, no learner payloads. */
(function () {
  'use strict';
  if (window.SecuredMePublicAnalytics) return;
  const script = document.currentScript;
  const assets = new URL('.', script.src);
  const CONSENT = 'securedme.public-analytics-consent.v1';
  const VERSION = '2026-09-30';
  const TOKEN = 'phc_kXRL4FyfQ4W3XqbuCGnYfxMRbPanSnSfnfWxuZqELeZR'; // Public project token, not an authentication key.
  const tools = {
    'algoquest.securedme.ca': 'algoquest-qbit',
    'algorithm-builder.securedme.ca': 'algorithm-builder',
    'ffed-qlc.securedme.ca': 'ffed-qlc',
    'fnp-qnn.securedme.ca': 'fnp-qnn',
    'fnpqnn.securedme.ca': 'fnp-qnn',
    'gateway.securedme.ca': 'fnpqnn-gateway',
    'retailguard.securedme.ca': 'retailguard',
    'market-guardian.securedme.ca': 'retailguard',
    'quanthor.securedme.ca': 'quanthor',
    'www.scholarium.securedme.ca': 'scholarium',
    'scholarium.securedme.ca': 'scholarium',
    'synthia.securedme.ca': 'synthia',
    'tesla-workbench.securedme.ca': 'tesla-workbench',
    'tesla-recovery.securedme.ca': 'tesla-workbench',
    'vot-guardian.securedme.ca': 'vot-guardian',
    'vad.securedme.ca': 'visual-algorithm-designer',
    'visual-algorithm.securedme.ca': 'visual-algorithm-designer'
  };
  const slugs = new Set(Object.values(tools));
  const docsRepositories = {
    'algoquest-ams-discovry-labs-module-': 'algoquest-qbit',
    'algorithm-builder-app': 'algorithm-builder',
    'ffed-qlc-mvp': 'ffed-qlc', 'fnp-qnn-mvp': 'fnp-qnn',
    'fnpqnn_gateway_mvp': 'fnpqnn-gateway',
    'market-guardian-retailguard': 'retailguard', 'quanthor': 'quanthor',
    'securedme-scholarium': 'suite', 'synthia': 'synthia',
    'tesla-resonance-recovery-workbench': 'tesla-workbench',
    'v.o.t-guardian': 'vot-guardian', 'visualalgorithmdesigner': 'visual-algorithm-designer'
  };
  const rootPages = new Set(['/', '/product/education/', '/product/free/', '/product/pro/', '/product/premium/', '/product/enterprise/', '/portfolio/', '/services/', '/pricing/', '/contact/', '/docs/', '/privacy/', '/terms/', '/white-papers/', '/neutrosophic-ai-systems/', '/marketplace/']);
  const events = new Set(['public_page_view', 'education_tool_opened', 'education_docs_opened', 'public_service_cta_clicked', 'companion_public_opened', 'public_case_study_opened']);
  const privateRoute = /(?:^|\/)(?:api|auth|account|login|callback|students?|learners?|sessions?|workspace|professor-cockpit|teach|safety|evidence|private)(?:\/|\.|$)/i;
  const dnt = () => navigator.doNotTrack === '1' || navigator.globalPrivacyControl === true;
  const normalPath = (url) => url.pathname.replace(/index\.html$/, '').replace(/\/{2,}/g, '/');
  function publicContext(url) {
    let decodedPath;
    try { decodedPath = decodeURIComponent(url.pathname); } catch (_) { return null; }
    if (privateRoute.test(decodedPath)) return null;
    if ([...url.searchParams.keys()].some(key => /^(?:code|token|access_token|id_token|email|learner_id|student_id)$/i.test(key))) return null;
    const path = normalPath(url);
    if (url.hostname === 'securedme.ca' && rootPages.has(path)) {
      return {surface: 'website', page_key: path, tool_slug: 'suite'};
    }
    if (tools[url.hostname] && (path === '/' || path === '/landing/')) {
      return {surface: 'tool', page_key: '/', tool_slug: tools[url.hostname]};
    }
    const docsRepository = path.split('/')[1].toLowerCase();
    if (url.hostname === 'securedme-main-dev.github.io' && Object.prototype.hasOwnProperty.call(docsRepositories, docsRepository)) {
      const match = path.match(/\/tools\/([a-z0-9-]+)(?:\/|\.html|$)/);
      return {surface: 'documentation', page_key: 'documentation', tool_slug: match && slugs.has(match[1]) ? match[1] : docsRepositories[docsRepository]};
    }
    return null;
  }
  let forcedPrivate = false;
  let consent = null;
  let client = null;
  let loading = false;
  let generation = 0;
  let lastPage = null;
  let visitorId = window.crypto.randomUUID();
  let region;
  let settings;
  const context = () => forcedPrivate ? null : publicContext(new URL(window.location.href));
  function permitted() { return consent === 'granted' && !dnt() && !!context(); }
  try {
    const stored = JSON.parse(localStorage.getItem(CONSENT) || 'null');
    if (stored && stored.version === VERSION && ['granted', 'denied'].includes(stored.choice)) consent = stored.choice;
  } catch (_) { /* Storage unavailable: remain opt-in for this page only. */ }

  // Rebuild properties after the SDK adds defaults. URLs, referrers, titles,
  // identifiers, form values, prompts and learning results never pass this boundary.
  function sanitize(event) {
    if (!permitted() || !event || !events.has(event.event)) return null;
    const current = context();
    const p = event.properties || {};
    const safe = {
      token: TOKEN,
      distinct_id: visitorId,
      $process_person_profile: false,
      $geoip_disable: true,
      schema_version: 'securedme.public-analytics.v1',
      consent_version: VERSION,
      surface: current.surface,
      page_key: current.page_key,
      tool_slug: current.tool_slug
    };
    if (slugs.has(p.target_tool)) safe.target_tool = p.target_tool;
    if (['contact', 'diagnostic', 'services', 'pricing'].includes(p.cta_kind)) safe.cta_kind = p.cta_kind;
    if (['portfolio', 'white-papers'].includes(p.case_kind)) safe.case_kind = p.case_kind;
    return {event: event.event, properties: safe, timestamp: new Date()};
  }
  function capture(name, properties) {
    if (!client || !permitted() || !events.has(name)) return false;
    client.capture(name, properties || {});
    return true;
  }
  function pageView() {
    const current = context();
    if (!current || !permitted()) return;
    const key = JSON.stringify(current);
    if (lastPage !== key && capture('public_page_view')) lastPage = key;
  }
  function start() {
    if (!permitted() || loading || client) return;
    loading = true;
    const requestedGeneration = ++generation;
    const sdk = document.createElement('script');
    sdk.src = new URL('posthog-1.435.3.js', assets).href;
    sdk.async = true;
    sdk.dataset.securedmeAnalyticsSdk = 'true';
    sdk.onload = () => {
      loading = false;
      if (requestedGeneration !== generation || !permitted() || !window.posthog) return;
      client = window.posthog.init(TOKEN, {
        api_host: 'https://us.i.posthog.com', ui_host: 'https://us.posthog.com',
        autocapture: false, rageclick: false, capture_dead_clicks: false,
        capture_pageview: false, capture_pageleave: false,
        disable_session_recording: true, enable_recording_console_log: false,
        capture_performance: false, capture_web_vitals: false, capture_exceptions: false,
        capture_heatmaps: false, disable_surveys: true, disable_conversations: true,
        disable_external_dependency_loading: true, advanced_disable_flags: true,
        person_profiles: 'never', persistence: 'memory', disable_persistence: true,
        ip: false, respect_dnt: true, cross_subdomain_cookie: false,
        request_batching: false, before_send: sanitize,
        loaded: (instance) => { client = instance; }
      });
      // Re-consenting must also clear the SDK's opt-out state after withdrawal.
      client?.opt_in_capturing({enable_persistence: false});
      pageView();
    };
    sdk.onerror = () => { loading = false; };
    document.head.appendChild(sdk);
  }
  function choose(choice) {
    consent = choice;
    try { localStorage.setItem(CONSENT, JSON.stringify({version: VERSION, choice})); } catch (_) {}
    if (choice !== 'granted') {
      generation++;
      loading = false;
      client?.opt_out_capturing({clear_persistence: true});
      client = null;
      lastPage = null;
      visitorId = window.crypto.randomUUID();
      document.querySelectorAll('script[data-securedme-analytics-sdk]').forEach(node => node.remove());
    }
    render();
    if (choice === 'granted') start();
    settings?.focus();
  }
  const copy = {
    en: ['Optional public analytics', 'Allow PostHog to measure public page visits and navigation? No lesson content, forms or recordings are sent. Your choice applies to this site.', 'Allow analytics', 'Decline', 'Analytics preferences', 'https://securedme.ca/privacy/', 'Privacy details'],
    fr: ['Statistiques publiques facultatives', 'Autoriser PostHog à mesurer les visites et la navigation publiques ? Aucun contenu de cours, formulaire ou enregistrement n’est envoyé. Votre choix s’applique à ce site.', 'Autoriser les statistiques', 'Refuser', 'Préférences de statistiques', 'https://securedme.ca/privacy/', 'Détails de confidentialité'],
    es: ['Estadísticas públicas opcionales', '¿Permitir que PostHog mida las visitas y la navegación públicas? No se envían contenidos de clases, formularios ni grabaciones. Su elección se aplica a este sitio.', 'Permitir estadísticas', 'Rechazar', 'Preferencias de estadísticas', 'https://securedme.ca/privacy/', 'Detalles de privacidad']
  };
  function render() {
    if (!region) return;
    const text = copy[(document.documentElement.lang || 'en').slice(0, 2)] || copy.en;
    settings.textContent = text[4];
    region.replaceChildren();
    settings.hidden = forcedPrivate || !context();
    region.hidden = consent !== null || forcedPrivate || dnt() || !context();
    region.setAttribute('aria-label', text[0]);
    const heading = document.createElement('strong'); heading.textContent = text[0];
    const description = document.createElement('p'); description.textContent = text[1];
    const actions = document.createElement('div'); actions.className = 'sm-analytics-actions';
    for (const [choice, label] of [['granted', text[2]], ['denied', text[3]]]) {
      const button = document.createElement('button'); button.type = 'button'; button.textContent = label;
      button.dataset.analyticsConsent = choice; button.addEventListener('click', () => choose(choice)); actions.appendChild(button);
    }
    const privacy = document.createElement('a'); privacy.href = text[5]; privacy.textContent = text[6];
    actions.appendChild(privacy);
    region.append(heading, description, actions);
  }
  function install() {
    // The in-flow region cannot cover the shared Theme/Language/Access/Support dock.
    if (!context()) return;
    const style = document.createElement('link'); style.rel = 'stylesheet';
    style.href = new URL('securedme-public-analytics.css', assets).href; document.head.appendChild(style);
    region = document.createElement('section'); region.className = 'sm-analytics-consent';
    region.setAttribute('role', 'region'); region.dataset.noTranslate = '';
    document.body.prepend(region);
    settings = document.createElement('button'); settings.type = 'button'; settings.className = 'sm-analytics-settings'; settings.dataset.noTranslate = '';
    settings.addEventListener('click', () => { consent = null; render(); region.hidden = false; region.querySelector('button')?.focus(); });
    (document.querySelector('footer') || document.body).appendChild(settings);
    document.addEventListener('click', event => {
      const link = event.target.closest?.('a[href]');
      if (!link || !permitted()) return;
      const url = new URL(link.href, location.href);
      if (url.protocol === 'mailto:') capture('public_service_cta_clicked', {cta_kind: 'contact'});
      else if (tools[url.hostname]) capture('education_tool_opened', {target_tool: tools[url.hostname]});
      else if (url.hostname === 'securedme-main-dev.github.io') {
        const target = publicContext(url); if (target?.surface === 'documentation') capture('education_docs_opened', {target_tool: target.tool_slug});
      } else if (url.hostname === 'securedme.ca') {
        const path = normalPath(url);
        if (['/contact/', '/services/', '/pricing/'].includes(path)) capture('public_service_cta_clicked', {cta_kind: path.split('/')[1]});
        if (['/portfolio/', '/white-papers/'].includes(path)) capture('public_case_study_opened', {case_kind: path.split('/')[1]});
      }
    });
    document.addEventListener('securedme:companion-public-opened', () => capture('companion_public_opened'));
    window.addEventListener('popstate', pageView);
    new MutationObserver(() => render()).observe(document.documentElement, {attributes: true, attributeFilter: ['lang']});
    render(); start();
  }
  window.SecuredMePublicAnalytics = Object.freeze({
    capture,
    setPrivate: value => { forcedPrivate = value !== false; if (forcedPrivate) { client?.opt_out_capturing({clear_persistence: true}); client = null; generation++; loading = false; lastPage = null; visitorId = window.crypto.randomUUID(); document.querySelectorAll('script[data-securedme-analytics-sdk]').forEach(node => node.remove()); } render(); if (!forcedPrivate) start(); },
    state: () => ({consent, enabled: permitted() && !!client, publicSurface: !!context(), policyVersion: VERSION})
  });
  // Framework adapters emit this event after a client-side route transition.
  // No URL or learner identifier is carried in the event.
  window.addEventListener('securedme:public-route-change', () => {
    if (!region && context()) install();
    else { render(); start(); pageView(); }
  });
  if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded', install, {once: true});
  else install();
})();
