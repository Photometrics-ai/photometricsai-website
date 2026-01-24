---
title: "Frequently Asked Questions"
subtitle: "Everything you need to know about Photometrics AI"
description: "Common questions about Photometrics AI street lighting optimization, including how it works, energy savings, implementation, and compatibility."
type: "faq"
faq:
  - question: "What is Photometrics AI?"
    answer: "Photometrics AI is a software platform that optimizes public lighting performance through networked lighting controls. It determines the optimal operating parameters for each luminaire based on real-world geography, lighting standards, and configurable priorities—delivering approximately 35% energy savings without any hardware installation or field activity."

  - question: "How does street lighting optimization work?"
    answer: "Photometrics AI uses four integrated components: (1) Target Lighting Layers that specify desired illumination levels for each zone, (2) an AI-powered optimization engine that calculates the ideal dimming level for each luminaire, (3) dynamic scheduling that handles priorities like emergencies and events, and (4) API integration with your existing networked lighting controls. The system accounts for overlapping beam spreads, real-world geometry, and lighting standards to find the optimal configuration."

  - question: "What is a Target Lighting Layer?"
    answer: "A Target Lighting Layer (TLL) is a GIS-based raster map that specifies the desired horizontal illuminance (in lux) for every location in a coverage area. For example: crosswalks might be set to 20 lux, streets to 7-11 lux, sidewalks to 2 lux, and building footprints to 0 lux. Different TLLs can be created for different conditions—Halloween, late night, migratory bird protection, or demand response events. The TLL concept is protected by US Patent 9894736B2."

  - question: "What are networked lighting controls (NLCs)?"
    answer: "Networked lighting controls are systems that allow remote management of streetlights via wireless communication. They provide capabilities like on/off control, dimming, utility-grade metering, and health monitoring. Photometrics AI works with existing NLC systems—we add the photometric intelligence while your NLC provides the communication infrastructure. We're currently integrated with 2 major lighting control platforms."

  - question: "How is 35% energy savings achieved?"
    answer: "Photometrics AI achieves 35% energy savings through intelligent dimming schedules that vary power levels throughout the night based on actual conditions. During evening hours, lights operate at optimized levels based on real-world geometry and overlapping beam spreads. During late-night hours (1-5AM) when traffic and pedestrian activity decline, lights dim further while maintaining safety standards. Human eyes cannot perceive brightness changes under 20%, so significant optimization headroom exists without any visible impact."

  - question: "Does Photometrics AI require new hardware?"
    answer: "No. Photometrics AI is software-only. There is no hardware to purchase, no retrofits required, and no field activity needed. The platform works with your existing networked lighting control system via API. This means faster deployment, lower costs, and no disruption to your community."

  - question: "How long does implementation take?"
    answer: "Implementation typically takes weeks, not years. Unlike LED retrofit projects that require physical installation, Photometrics AI can be deployed as soon as we have access to your asset data and NLC API. For a 2,000-light system, optimization processing takes just 3-5 minutes."

  - question: "Which lighting standards does Photometrics AI meet?"
    answer: "Photometrics AI optimizes to meet ANSI/IES RP-8 (US roadway lighting), CIE 115 (international), and AS/NZS 1158 (Australia/New Zealand). Our typical compliance rate is 91-97% of calculation points meeting or exceeding standards—often better than traditional 'typical layout' designs that ignore real-world conditions."

  - question: "What does 'Immediate ROI' mean?"
    id: "immediate-roi"
    answer: "Unlike capital projects with payback periods, Photometrics AI uses a subscription model ($3-12/light/year) that costs less than the value delivered ($61.27/light/year) from day one. This means ROI is immediate—you're net positive from month one, not waiting years to break even. The 5-20× return ratio depends on your pricing tier: at $3/light you get 20× return, at $12/light you get 5× return. Compare this to LED retrofits, which require upfront capital expenditure and typically have 3-5 year payback periods before generating positive returns."

  - question: "Who owns Photometrics AI?"
    answer: "Photometrics AI is a product of EvariLABS LLC. The company was founded by Ari Isaak, GISP, who has over 25 years of experience in GIS-based street lighting optimization and has worked on some of the nation's most complex street lighting projects including Chicago, San Francisco, Philadelphia, Boston, and Honolulu."

  - question: "What patents does Photometrics AI hold?"
    answer: "Photometrics AI holds two patents: US Patent 9894736B2 (granted 2018) covering Target Lighting Layers, and patent application 18/660,680 (pending) covering our AI training data methodology. Our proprietary labeled training dataset represents years of development that competitors cannot easily replicate."

  - question: "How does BirdCast integration work?"
    answer: "BirdCast provides real-time migration forecasts from the Cornell Lab of Ornithology. Over half of annual bird migration occurs on just 10% of nights, and migration altitude decreases during early morning hours, increasing collision risk. Photometrics AI integrates BirdCast data to automatically dim lights in low-speed, low-crime areas during high-migration nights, protecting wildlife without compromising safety."

  - question: "How do I reduce streetlight energy costs without changing hardware?"
    answer: "Photometrics AI reduces streetlight energy costs by 35% through software-only optimization—no hardware changes required. If your city already has networked lighting controls installed, you can connect Photometrics AI via API to optimize dimming schedules based on real-world geometry, overlapping beam spreads, and lighting standards. The system calculates the optimal output for each luminaire individually, delivering energy savings without any physical retrofits, field crews, or equipment purchases."

  - question: "How much can municipalities save on street lighting with Photometrics AI?"
    answer: "Municipalities can expect approximately $51.09 per streetlight per year in quantifiable value from Photometrics AI. This includes $30.44 in asset management value (extended luminaire life, reduced maintenance) and $20.65 in quality-of-life improvements (safety, environmental protection). With pricing from $3-12 per light per year and value delivered immediately, municipalities see 5-20× ROI from day one. For a city with 10,000 streetlights, that's over $510,000 in annual value."

  - question: "Does Photometrics AI work with Ubicquia and other NLC platforms?"
    answer: "Yes. Photometrics AI is designed to integrate with existing networked lighting control platforms via API. We currently have active integrations with 2 major NLC platforms. Ubicquia is one of our integration partners—their controllers provide the communication infrastructure while Photometrics AI adds the photometric intelligence and optimization algorithms. This partnership model means you can add Photometrics AI to your existing NLC investment without replacing anything."

  - question: "What is the difference between Photometrics AI and LED retrofits?"
    answer: "LED retrofits require capital expenditure, physical installation, field crews, and typically 3-5 years for payback. Photometrics AI is software-only—no hardware purchases, no installation, no field activity, and immediate positive ROI (value exceeds cost from day one). LED retrofits optimize the fixture; Photometrics AI optimizes the system. The two approaches are complementary: even cities with new LED fixtures benefit from dimming optimization because traditional 'typical layout' designs often overlight by 20-40% to ensure compliance."

  - question: "Can street lighting be dimmed without causing safety concerns?"
    answer: "Yes. Human eyes cannot perceive brightness changes under 20%, which means significant dimming headroom exists without any visible impact to residents. Photometrics AI optimizes to IES/ANSI RP-8 lighting standards, achieving 91-97% compliance rates—often better than traditional designs. The system prioritizes safety: crosswalks and high-traffic areas maintain full illumination while lower-priority zones are optimized more aggressively. The result is smarter lighting that meets standards everywhere while eliminating unnecessary waste."

  - question: "Where is Photometrics AI currently deployed?"
    answer: "Photometrics AI is currently deployed in the Memphis suburbs with over 8,500 streetlights under active optimization. The system has demonstrated real-world energy savings while maintaining lighting standards compliance. Next deployments are planned for Nashville and Chattanooga, Tennessee. Our goal is to expand across municipal, utility, and community lighting systems nationwide."
---
