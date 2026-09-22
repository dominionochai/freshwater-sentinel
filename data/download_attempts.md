# WHO Malawi cholera data download attempts

The requested WHO Malawi cholera data could not be retrieved.

## Attempts

1. Primary endpoint (attempted twice)
   - URL: `https://apps.who.int/gho/athena/api/GHO/CHOLERA.json?filter=COUNTRY:MWI`
   - Each attempt failed: `CRAWL_LIVECRAWL_TIMEOUT`, HTTP 504.

2. Alternative endpoint (attempted once)
   - URL: `https://apps.who.int/gho/athena/data/GHO/CHOLERA_0000000001.json?filter=COUNTRY:MWI`
   - Attempt failed: `CRAWL_LIVECRAWL_TIMEOUT`, HTTP 504.

## Data status

- No WHO fact table/series was retrieved.
- No fallback data was used.
- Forecast/data files were not updated due to the unavailable source.

## Latest mandated-source retrieval outcome

The five mandated URLs were attempted in the required order. None returned usable Malawi annual cholera data.

1. `https://apps.who.int/gho/athena/api/GHO/CHOLERA.json?filter=COUNTRY:MWI`
   - **Status:** Unavailable / Redirected.
   - **Exact outcome reported by retrieval:** The URL redirected to the WHO Global Health Observatory retirement notice (`https://www.who.int/data/gho/info/athena-api-retirement`), indicating this API endpoint is no longer active.

2. `https://apps.who.int/gho/athena/data/GHO/CHOLERA_0000000001.json?filter=COUNTRY:MWI`
   - **Status:** Unavailable / Redirected.
   - **Exact outcome reported by retrieval:** This also redirected to the WHO Global Health Observatory retirement notice (`https://www.who.int/data/gho/info/athena-api-retirement`).

3. `https://raw.githubusercontent.com/owid/etl/master/etl/steps/data/garden/who/2023-06-29/cholera/cholera.csv`
   - **Status:** 404 Not Found.
   - **Exact outcome reported by retrieval:** The GitHub raw file endpoint returned `404: Not Found`.

4. `https://raw.githubusercontent.com/datasets/cholera/master/data/who-cholera.csv`
   - **Status:** 404 Not Found.
   - **Exact outcome reported by retrieval:** The GitHub raw file endpoint also returned `404: Not Found`.

5. `https://data.humdata.org/api/3/action/package_show?id=cholera-in-africa`
   - **Status:** API Error (success: false).
   - **Exact response reported by retrieval:** `{"help":"https://data.humdata.org/api/3/action/help_show?name=package_show","error":{"__type":"Not Found Error","message":"Not found"},"success":false}`

No Malawi annual values, verified source license metadata, CSV, or manifest entry were created. Forecast code and tests were intentionally not changed.