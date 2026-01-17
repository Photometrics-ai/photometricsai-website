---
title: "Frequently Asked Questions"
subtitle: "Everything you need to know about Photometrics AI"
description: "Common questions about Photometrics AI street lighting optimization, including how it works, energy savings, implementation, and compatibility."
type: "faq"
faq:
  - question: "What is Photometrics AI?"
    answer: "Photometrics AI is a software platform that optimizes public lighting performance through networked lighting controls. It determines the optimal operating parameters for each luminaire based on real-world geography, lighting standards, and configurable priorities—delivering approximately 40% energy savings without any hardware installation or field activity."

  - question: "How does street lighting optimization work?"
    answer: "Photometrics AI uses four integrated components: (1) Target Lighting Layers that specify desired illumination levels for each zone, (2) an AI-powered optimization engine that calculates the ideal dimming level for each luminaire, (3) dynamic scheduling that handles priorities like emergencies and events, and (4) API integration with your existing networked lighting controls. The system accounts for overlapping beam spreads, real-world geometry, and lighting standards to find the optimal configuration."

  - question: "What is a Target Lighting Layer?"
    answer: "A Target Lighting Layer (TLL) is a GIS-based raster map that specifies the desired horizontal illuminance (in lux) for every location in a coverage area. For example: crosswalks might be set to 20 lux, streets to 7-11 lux, sidewalks to 2 lux, and building footprints to 0 lux. Different TLLs can be created for different conditions—Halloween, late night, migratory bird protection, or demand response events. The TLL concept is protected by US Patent 9894736B2."

  - question: "What are networked lighting controls (NLCs)?"
    answer: "Networked lighting controls are systems that allow remote management of streetlights via wireless communication. They provide capabilities like on/off control, dimming, utility-grade metering, and health monitoring. Photometrics AI works with existing NLC systems—we add the photometric intelligence while your NLC provides the communication infrastructure. We're currently integrated with 2 major lighting control platforms."

  - question: "How is 40% energy savings achieved?"
    answer: "The 40% savings comes from two sources: (1) 25% through precision design optimization, applied dusk-to-dawn—per-luminaire dimming based on actual geometry, overlapping beam spreads, and Target Lighting Layers; (2) 15% through early morning dimming (1AM-6AM) when traffic and pedestrian activity decline. Human eyes cannot perceive brightness changes under 20%, so significant optimization headroom exists without any visible impact."

  - question: "Does Photometrics AI require new hardware?"
    answer: "No. Photometrics AI is software-only. There is no hardware to purchase, no retrofits required, and no field activity needed. The platform works with your existing networked lighting control system via API. This means faster deployment, lower costs, and no disruption to your community."

  - question: "How long does implementation take?"
    answer: "Implementation typically takes weeks, not years. Unlike LED retrofit projects that require physical installation, Photometrics AI can be deployed as soon as we have access to your asset data and NLC API. For a 2,000-light system, optimization processing takes just 3-5 minutes."

  - question: "Which lighting standards does Photometrics AI meet?"
    answer: "Photometrics AI optimizes to meet ANSI/IES RP-8 (US roadway lighting), CIE 115 (international), and AS/NZS 1158 (Australia/New Zealand). Our typical compliance rate is 91-97% of calculation points meeting or exceeding standards—often better than traditional 'typical layout' designs that ignore real-world conditions."

  - question: "What is the ROI timeline?"
    answer: "ROI is typically under 12 months. Photometrics AI delivers approximately $61.81 per streetlight per year in quantifiable value to municipalities, plus an additional $15.48 for utilities. With pricing ranging from $3-12 per light per year, the payback is rapid compared to capital-intensive alternatives like LED retrofits."

  - question: "Who owns Photometrics AI?"
    answer: "Photometrics AI is a product of EvariLABS LLC. The company was founded by Ari Isaak, GISP, who has over 25 years of experience in GIS-based street lighting optimization and has worked on some of the nation's most complex street lighting projects including Chicago, San Francisco, Philadelphia, Boston, and Honolulu."

  - question: "What patents does Photometrics AI hold?"
    answer: "Photometrics AI holds two patents: US Patent 9894736B2 (granted 2018) covering Target Lighting Layers, and patent application 18/660,680 (pending) covering our AI training data methodology. Our proprietary labeled training dataset represents years of development that competitors cannot easily replicate."

  - question: "How does BirdCast integration work?"
    answer: "BirdCast provides real-time migration forecasts from the Cornell Lab of Ornithology. Over half of annual bird migration occurs on just 10% of nights, and migration altitude decreases during early morning hours, increasing collision risk. Photometrics AI integrates BirdCast data to automatically dim lights in low-speed, low-crime areas during high-migration nights, protecting wildlife without compromising safety."
---
