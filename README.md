# OV Chipkaart Travel History

Docker image to download travel history of an anonymous OV Chipkaart
using [this website](https://www.ov-chipkaart.nl/customer-service/self-service/travel-history-anonymous-card.htm).

## Rationale
As of now (September 2016), OV Chipkaart doesn't provide open API to download
travel history, including top-up transactions.

This tool is a workaround around the missing API. It uses a headless
Chrome browser and Selenium to scrape travel history from OV Chipkaart website
and store it in a CSV file.

## Usage

```bash
docker run \
  --rm
  --env OVCHIPKAART_CARD_NUMBER="[card_number]" \
  --env OVCHIPKAART_EXPIRATION_DATE="[card_expiration_date]" \
  --volume [download-dir]=/data \
  --privileged \
  mkrcah/ov-chipkaart-tx:latest \
  --month="[month]"
```

where
- `card_number` and `card_expiration_date` are information that can be found on your anonymous OV chipkaart
- `month` is a time period for which travel history will be downloaded, in `YYYY-MM` format. Currently, you can download transactions only half a year back from current date, not earlier.
- `download-dir` a directory where the CSV file with transactions will be saved

There is an optional argument available:
- `--export-filename [filename]` which specified name of the downloaded CSV file.

Card details can be also supplied via a file using the [`--env-file` flag](https://docs.docker.com/engine/reference/commandline/run/#/set-environment-variables-e-env-env-file).

Note: `--privileged` is required in order for Chromium to start.

## Example:

```
$ cat env.list
OVCHIPKAART_CARD_NUMBER=0000-1111-2222-3333
OVCHIPKAART_EXPIRATION_DATE=01-01-2020

$ docker run --env-file=env.list \
   --volume $(pwd)/export-data=/data \
   --privileged mkrcah/ov-chipkaart-tx \
   --month "2016-09"
Starting chrome...
Loading login page
...
Done!

$ ls ./export-data
ovchipkaart-2016-09.csv
```


## Troubleshooting

Try to open [the page](https://www.ov-chipkaart.nl/customer-service/self-service/travel-history-anonymous-card.htm) and fill in provided data manually.
If not, try installing selenium and running the script locally.
If that doesn't help, or you find yourself lost, please open an issue.

## License
[MIT](http://choosealicense.com/licenses/mit/)
