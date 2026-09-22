# Fresh Water Sentinel

## 1. Track alignment

**Primary track: #6 — Resilience Informatics**  
**Related tracks: #2 — Data-to-Insight and #3 — AI-Supported Assessment**

Fresh Water Sentinel turns multispectral freshwater observations into an interpretable screening workflow for communities and water stewards. It combines water masking, turbidity and chlorophyll-a proxies, NDCI-based algal-bloom screening, uncertainty estimates, activity-specific risk tiers, community context, and plain-language alerts.

The project aligns most directly with **Resilience Informatics** because it is designed to help freshwater communities identify changing environmental conditions early and respond with understandable, actionable information. It also supports **Data-to-Insight** by converting satellite-style reflectance data into water-quality indicators and visual risk signals, and **AI-Supported Assessment** through automated analysis, evidence-oriented explanations, uncertainty reporting, and exploratory linkage with synthetic health data.

Fresh Water Sentinel is intentionally a transparent screening aid rather than a diagnostic, laboratory replacement, regulatory classification, or causal disease-monitoring system.

---

## 2. Project description

### The problem

Freshwater communities often need to make decisions with incomplete, delayed, or difficult-to-interpret information. Changes in water clarity, algae-related signals, and environmental conditions can affect recreation, fishing, pets, and community health. However, laboratory testing and specialist interpretation may not always be immediately available.

The challenge is not only detecting a possible water-quality concern. Information must also be communicated in a way that is understandable, locally relevant, and honest about uncertainty.

### Our solution

**Fresh Water Sentinel** is a FastAPI-based prototype for transparent freshwater screening. It accepts multispectral reflectance scenes, including locally generated synthetic GeoTIFF scenes for offline demonstrations, and applies an interpretable analysis pipeline:

- MNDWI and NDVI-based open-water masking
- Turbidity proxy estimation
- Chlorophyll-a proxy estimation
- NDCI-derived algal-bloom screening
- Heuristic uncertainty estimation
- Activity-specific green/yellow/red risk tiers
- Evidence-oriented explanation payloads
- Community-aware alerts in English and Swahili
- Privacy-preserving community profile seeds
- A clearly labeled synthetic clinic-report overlay for exploratory water–health linkage

The current prototype calculates activity-specific screening risk for **swimming, fishing, and pets**. It does not claim to provide a validated drinking-water safety classification, laboratory-equivalent measurements, confirmed harmful algal-bloom diagnoses, or medical advice.

### How it supports decision-making

The system translates reflectance signals into a structured result that can show:

- What pixels were classified as water
- How much of the scene was usable water
- Which spectral signals contributed to the estimates
- Turbidity and chlorophyll-a proxy values
- NDCI-derived bloom-related signals
- Activity-specific risk scores and rationales
- An uncertainty heuristic
- Limitations such as cloud, atmospheric-correction, shallow-bottom, mixed-pixel, and regional-ecology effects
- A plain-language alert and recommended precaution

### Target users

The prototype is intended for:

- Community water stewards
- Environmental monitoring teams
- Public-health and One Health researchers
- Local organizations working around freshwater access
- Water-point and borehole program teams
- Researchers exploring satellite-supported water assessment
- Technical teams building more locally calibrated monitoring tools

It is not yet a production multi-user monitoring platform or a live alert-delivery service.

### Expected ecosystem-health impact

Fresh Water Sentinel can help users identify areas that may warrant closer inspection, field sampling, or precautionary communication. By combining water masking with turbidity, chlorophyll-a, and NDCI-related signals, it provides a more structured view of freshwater conditions than a single visual observation.

The project supports ecosystem-health awareness by making possible changes in water conditions easier to interpret and compare, while clearly distinguishing screening signals from validated environmental measurements.

### Expected human-health impact

The prototype supports a cautious One Health workflow by connecting environmental screening with community context and synthetic health-linkage records. It can help demonstrate how a water-point reference, a community profile, and a synthetic clinic report might be viewed together for exploratory analysis.

The health overlay is explicitly synthetic and does not establish transmission, causation, or clinical risk. Its purpose is to show how environmental and health information could be organized for further investigation and field validation.

---

## 3. How it works

Fresh Water Sentinel follows a transparent sequence:

### 1. Start with multispectral reflectance

The pipeline accepts a multispectral scene containing bands such as blue, green, red, red-edge, near-infrared, and SWIR data. The repository includes an offline synthetic scene generator so the workflow can be demonstrated without downloading live satellite data.

### 2. Identify likely open water

The system calculates:

- **MNDWI** from green and SWIR reflectance:

  `MNDWI = (B03 - B11) / (B03 + B11)`

- **NDVI** from near-infrared and red reflectance:

  `NDVI = (B08 - B04) / (B08 + B04)`

The default water mask keeps pixels meeting the configured MNDWI and NDVI criteria. This helps exclude land and vegetation before estimating water-quality proxies.

### 3. Estimate water-quality signals

Only pixels retained by the water mask are used for the next stage.

The pipeline estimates:

- A **turbidity proxy**, reported as an NTU-like screening estimate rather than a laboratory measurement
- A **chlorophyll-a proxy**
- Proxy spread and coverage information used in the uncertainty heuristic

These estimates are based on spectral relationships and require local calibration and field or laboratory validation before operational use.

### 4. Calculate the NDCI layer

The system calculates the Normalized Difference Chlorophyll Index:

`NDCI = (B05 - B04) / (B05 + B04)`

It then derives an NDCI-based chlorophyll-a proxy using the implemented quadratic conversion. This provides an additional screening layer for algae-related conditions. It is not presented as confirmation of a harmful algal bloom or a validated concentration measurement.

### 5. Produce activity-specific risk tiers

Turbidity, chlorophyll-related signals, and optional field observations are combined into configurable screening scores for:

- Swimming
- Fishing
- Pets

Each activity receives:

- A score from 0 to 1
- A green, yellow, or red tier
- A rationale explaining the main contributing signals

The thresholds are configurable screening thresholds, not regulatory or public-health limits. A drinking-water risk tier is not claimed as implemented in the current prototype.

### 6. Add uncertainty and explanations

The response includes a bounded heuristic uncertainty value based on factors such as:

- Water-mask coverage
- Estimator spread
- Turbidity and chlorophyll proxy variability

The explanation payload describes the intermediate evidence, including the bands used, the number of analyzed water pixels, the water-mask method, alert date, risk drivers, and known limitations. This is rule-based explainability from pipeline outputs, not trained-model attribution.

### 7. Create community-aware alerts

The alert layer converts the result into plain-language messages in:

- English
- Swahili

Community profile seeds can provide contextual information such as language preference and delivery preference. The repository generates alert content, but it does not currently send live SMS, WhatsApp, or dashboard notifications.

---

## 4. Build and technology stack

Fresh Water Sentinel is implemented as a backend-first Python prototype.

### Core stack

- **Python**
- **FastAPI**
- **Rasterio** for GeoTIFF ingestion
- **NumPy** for array operations and spectral-index calculations
- **Docker** for containerized execution
- **GitHub Actions** for continuous integration
- **Pytest** for unit and API-contract tests
- **Configuration-driven thresholds and weights**

### Main components

- FastAPI endpoints for health, ingestion, analysis, alerts, community profiles, risk results, and health linkage
- Local MNDWI/NDVI water masking
- Turbidity and chlorophyll-a proxy calculations
- NDCI-derived chlorophyll-a screening
- Activity-specific risk scoring
- Explainability payload generation
- English and Swahili alert templates
- Community profile loading and contextualization
- Synthetic clinic-report linkage
- Offline synthetic scene generation

### Offline development and demonstration

The repository includes a deterministic synthetic scene generator that creates a 64×64 GeoTIFF with a synthetic bloom-like feature. This supports local demonstrations and tests without requiring live satellite downloads or external data services.

The synthetic scene is not presented as a real satellite observation.

### Testing and CI

GitHub Actions runs on pushes and pull requests. The workflow installs dependencies, compiles the application code, and runs the test suite.

The current tests cover key pipeline, masking, water-quality, alert, community-data, and API behaviors. The project has not yet undergone field validation, laboratory calibration, clinical validation, large-scale performance testing, or operational satellite benchmarking.

---

## 5. Impact and One Health framing

Fresh Water Sentinel is designed around the idea that freshwater health, ecosystem health, animal exposure, and human health are connected.

### African freshwater communities

The prototype includes community-profile seeds and a filtered Malawi borehole data extract based on the **openwashdata/boreholelabdata** dataset. The retained data is attributed under **CC BY 4.0**:

https://github.com/openwashdata/boreholelabdata

This data is used to demonstrate how water-point and community context can be incorporated into a screening workflow. It is not a live monitoring feed or a complete representation of Malawi’s water infrastructure.

### Children and schools

Community context can include school- and child-related fields when such information is available. The prototype does not infer exposure or health outcomes from these fields. Instead, the structure provides a way for future validated workflows to consider places where children may have increased contact with freshwater, such as schools or community water points.

### Pets and animals

Pets are one of the supported activity-specific risk categories. This reflects the One Health principle that environmental conditions may affect people and animals sharing the same water environment. The pet tier is a screening signal, not veterinary advice or a confirmed toxicity assessment.

### Synthetic health linkage

The repository includes synthetic clinic reports involving diseases such as cholera and typhoid. These records are linked to water-point and community references to demonstrate an exploratory environmental-health data model.

The linkage is explicitly:

- Synthetic
- Privacy-preserving at the prototype level
- Exploratory
- Not evidence of transmission
- Not causal inference
- Not clinical surveillance
- Not a diagnosis or medical recommendation

### Why this matters

For communities with limited access to rapid laboratory testing, an interpretable screening workflow could help organize observations, identify locations for follow-up, and communicate precautionary information more clearly.

The most important impact of the current prototype is not claiming certainty. It is demonstrating a responsible pathway from environmental data to community-oriented insight while showing the assumptions, uncertainty, and validation still required.

Future work would include:

- Local field and laboratory calibration
- Validation against real satellite and water-quality observations
- Improved cloud and atmospheric-quality handling
- Stronger community co-design
- Validation of translations and alert wording
- Secure production data storage
- Carefully governed integration with real health and water-monitoring systems

---

## 6. Tagline

**Fresh Water Sentinel turns multispectral water signals into transparent, community-aware freshwater risk insights.**

**See the signal. Understand the uncertainty. Protect the water-health connection.**
