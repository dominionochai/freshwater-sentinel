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
