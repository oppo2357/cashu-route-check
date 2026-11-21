# Cashu route check

A wallet offers its users a 20-sat Lightning payment. Its staging mint raises the minimum melt amount to 21 sats, while the minting endpoint still accepts 20. This CLI shows which side changed before the wallet ships.

Save the public response from a mint's `GET /v1/info` endpoint. Describe each required route in the format in `routes.json`. Amounts are integers in the named unit. Run with Python 3 and no additional dependencies.

To replay the example without downloading anything, run:

```sh
python routecheck.py routes.json examples/candidate.json --before examples/before.json
```

These two synthetic snapshots differ in one value. Mint stays advertised; melt changes from advertised to blocked because 20 is below 21. The expected exit status is 1. Run `python -m unittest -v` for an automated check, including both inclusive boundaries.

```sh
curl -fsS https://testnut.cashu.space/v1/info > mint-info.json
python routecheck.py routes.json mint-info.json
python routecheck.py routes.json mint-info.json --before examples/before.json
```

The JSON output includes the current verdict, the reason, and the previous verdict when a comparison is requested. Exit 0 means every route is advertised within published limits. Exit 1 means at least one is blocked or unknown. Exit 2 identifies invalid input. Each invocation works offline with saved metadata.

In CI, run the CLI directly as a build step. Redirect stdout to a file to retain the route report while preserving the exit status. Duplicate JSON fields produce exit 2 because different readers can interpret the same snapshot differently.

The checks cover the method, unit, operation-wide disable switch and amount boundaries in [NUT-04](https://github.com/cashubtc/nuts/blob/main/04.md#settings) and [NUT-05](https://github.com/cashubtc/nuts/blob/main/05.md#settings). An advertised route still needs a successful quote and execution. Liquidity, fees, authentication and method-specific options are outside this check.
