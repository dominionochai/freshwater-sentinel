# Seed data

`malawi_boreholes.csv` is a filtered extract of eight verified rows from the
[`boreholelabdata.csv`](https://raw.githubusercontent.com/openwashdata/boreholelabdata/main/inst/extdata/boreholelabdata.csv)
dataset. It preserves only the waterpoint name, type, coordinates, collection
date, and turbidity columns needed by this vertical slice.

Source: [openwashdata/boreholelabdata](https://github.com/openwashdata/boreholelabdata),
licensed under [CC BY 4.0](https://creativecommons.org/licenses/by/4.0/).

`community_profiles.json` is a separate, privacy-preserving derived seed file.
Its empty children, school, and pets values indicate that those details were
not supplied by the source dataset.
